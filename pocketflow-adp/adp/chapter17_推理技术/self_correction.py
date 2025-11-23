"""
自我纠正(Self-Correction)推理技术实现

自我纠正是一种通过迭代改进来提高答案质量的推理技术。
它首先生成一个初步答案，然后评估该答案的质量，识别潜在问题，
最后基于评估结果对答案进行修正，重复这个过程直到达到满意的答案。
"""

import sys
import os
import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple

# 添加本地PocketFlow路径到sys.path的开头
current_dir = os.path.dirname(os.path.abspath(__file__))
pocketflow_path = os.path.abspath(os.path.join(current_dir, "../../PocketFlow"))

# 将本地PocketFlow路径插入到sys.path的开头
if pocketflow_path not in sys.path:
    sys.path.insert(0, pocketflow_path)
    print(f"[DEBUG] 已将本地PocketFlow路径添加到sys.path开头: {pocketflow_path}")

# 添加utils路径
utils_path = os.path.abspath(os.path.join(current_dir, "../../utils"))
if utils_path not in sys.path:
    sys.path.append(utils_path)
    print(f"[DEBUG] 已将utils路径添加到sys.path: {utils_path}")

from pocketflow import AsyncNode, AsyncFlow
from utils import call_llm, call_llm_async


class SelfCorrectionNode(AsyncNode):
    """
    自我纠正节点
    
    该节点通过迭代改进来提高答案质量。
    它会生成一个初步答案，评估其质量，识别问题，然后进行修正。
    """
    
    def __init__(self, 
                 name: str = "SelfCorrectionNode",
                 max_iterations: int = 3,
                 quality_threshold: float = 80.0,
                 initial_prompt: Optional[str] = None,
                 evaluation_prompt: Optional[str] = None,
                 correction_prompt: Optional[str] = None,
                 max_retries: int = 1):
        """
        初始化自我纠正节点
        
        Args:
            name: 节点名称
            max_iterations: 最大迭代次数
            quality_threshold: 质量阈值，达到此阈值则停止迭代
            initial_prompt: 初始答案生成提示模板
            evaluation_prompt: 答案评估提示模板
            correction_prompt: 答案修正提示模板
            max_retries: 最大重试次数
        """
        super().__init__(max_retries=max_retries)
        self.name = name
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        
        # 默认初始答案生成提示模板
        self.initial_prompt = initial_prompt or """
请针对以下问题提供一个详细的答案：

问题：{question}

请提供一个全面、准确、有条理的答案。
"""
        
        # 默认答案评估提示模板
        self.evaluation_prompt = evaluation_prompt or """
请评估以下答案的质量：

问题：{question}

答案：{answer}

请从以下维度评估答案质量（0-100分）：
1. 准确性：答案是否准确，是否有事实错误
2. 完整性：答案是否完整，是否涵盖了问题的所有方面
3. 清晰性：答案是否清晰易懂，结构是否合理
4. 相关性：答案是否与问题高度相关，是否切中要点

请给出总分（0-100分），并指出答案中存在的问题和改进建议。

评估结果格式：
总分：[分数]
问题：[答案中存在的问题]
改进建议：[具体的改进建议]
"""
        
        # 默认答案修正提示模板
        self.correction_prompt = correction_prompt or """
基于以下评估结果，请改进答案：

问题：{question}

当前答案：{current_answer}

评估结果：
总分：{score}
问题：{issues}
改进建议：{suggestions}

请根据评估结果，改进当前答案，解决存在的问题，并采纳改进建议。
请提供一个改进后的答案。
"""
    
    async def generate_initial_answer(self, question: str) -> str:
        """
        生成初始答案
        
        Args:
            question: 问题
            
        Returns:
            初始答案
        """
        prompt = self.initial_prompt.format(question=question)
        return await call_llm_async(prompt)
    
    async def evaluate_answer(self, question: str, answer: str) -> Tuple[float, str, str]:
        """
        评估答案质量
        
        Args:
            question: 问题
            answer: 答案
            
        Returns:
            (分数, 问题列表, 改进建议)
        """
        prompt = self.evaluation_prompt.format(
            question=question,
            answer=answer
        )
        
        try:
            response = await call_llm_async(prompt)
            print(f"[DEBUG] SelfCorrectionNode.evaluate_answer: LLM response=\n{response}\n")
            
            # 尝试从响应中提取评估结果
            score = 50.0  # 默认分数
            issues = ""
            suggestions = ""
            
            # 首先尝试按标准格式解析
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith('总分：'):
                    try:
                        score = float(line.split('：')[1].strip())
                        score = min(100.0, max(0.0, score))  # 确保分数在0-100范围内
                    except:
                        continue
                elif line.startswith('问题：'):
                    issues = line.split('：', 1)[1].strip()
                elif line.startswith('改进建议：'):
                    suggestions = line.split('：', 1)[1].strip()
            
            # 如果标准格式解析失败，尝试从文本中提取信息
            if not issues and not suggestions:
                # 尝试从整个响应中提取问题和建议
                sections = response.split('\n\n')
                for section in sections:
                    section_lower = section.lower()
                    # 查找可能的问题部分
                    if any(keyword in section_lower for keyword in ['问题', '不足', '缺点', '缺陷', '弱点']):
                        if not issues:
                            issues = section.strip()
                    # 查找可能的建议部分
                    elif any(keyword in section_lower for keyword in ['建议', '改进', '提升', '优化']):
                        if not suggestions:
                            suggestions = section.strip()
                
                # 如果仍然没有找到明确的建议部分，尝试从整个响应中提取
                if not suggestions:
                    # 查找包含"建议"、"改进"等关键词的行
                    for line in lines:
                        if any(keyword in line for keyword in ['建议', '改进', '提升', '优化']):
                            if not suggestions:
                                suggestions = line.strip()
                            else:
                                suggestions += " " + line.strip()
            
            # 尝试从响应中提取分数（如果没有按标准格式）
            if score == 50.0:  # 如果还是默认值，说明没有提取到分数
                import re
                # 查找可能的分数模式
                score_patterns = [
                    r'(\d+)\s*分',
                    r'分数[：:]\s*(\d+)',
                    r'评分[：:]\s*(\d+)',
                    r'总分[：:]\s*(\d+)',
                    r'(\d+)/100',
                    r'(\d+)\s*\/\s*100'
                ]
                
                for pattern in score_patterns:
                    match = re.search(pattern, response)
                    if match:
                        try:
                            extracted_score = float(match.group(1))
                            score = min(100.0, max(0.0, extracted_score))
                            break
                        except:
                            continue
            
            print(f"[DEBUG] SelfCorrectionNode.evaluate_answer: extracted score={score}, issues={issues}, suggestions={suggestions}")
            return score, issues, suggestions
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            import traceback
            traceback.print_exc()
            return 50.0, "评估过程中出现错误", "请检查答案的准确性和完整性"
    
    async def correct_answer(self, question: str, current_answer: str, 
                           score: float, issues: str, suggestions: str) -> str:
        """
        修正答案
        
        Args:
            question: 问题
            current_answer: 当前答案
            score: 当前分数
            issues: 存在的问题
            suggestions: 改进建议
            
        Returns:
            修正后的答案
        """
        prompt = self.correction_prompt.format(
            question=question,
            current_answer=current_answer,
            score=score,
            issues=issues,
            suggestions=suggestions
        )
        
        return await call_llm_async(prompt)
    
    async def prep_async(self, shared):
        """
        预处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            
        Returns:
            共享状态数据
        """
        return shared
        
    async def exec_async(self, prep_res):
        """
        处理输入并生成自我纠正后的答案
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            包含纠正结果的字典
        """
        print(f"[DEBUG] SelfCorrectionNode.exec_async: prep_res={prep_res}")
        question = prep_res.get('question', '')
        if not question:
            print(f"[DEBUG] SelfCorrectionNode.exec_async: No question provided")
            return {
                'error': 'No question provided',
                'answer': '',
                'iterations': [],
                'final_score': 0.0
            }
        
        try:
            print(f"[DEBUG] SelfCorrectionNode.exec_async: Processing question: {question}")
            # 生成初始答案
            print("生成初始答案...")
            current_answer = await self.generate_initial_answer(question)
            
            # 记录迭代历史
            iterations = []
            
            # 迭代评估和修正答案
            for i in range(self.max_iterations):
                print(f"评估和修正答案 - 迭代 {i+1}/{self.max_iterations}")
                
                # 评估当前答案
                score, issues, suggestions = await self.evaluate_answer(question, current_answer)
                
                # 记录当前迭代
                iterations.append({
                    'iteration': i+1,
                    'answer': current_answer,
                    'score': score,
                    'issues': issues,
                    'suggestions': suggestions
                })
                
                # 如果分数达到阈值，停止迭代
                if score >= self.quality_threshold:
                    print(f"答案质量达到阈值 ({self.quality_threshold})，停止迭代")
                    break
                
                # 如果是最后一次迭代，不再修正
                if i == self.max_iterations - 1:
                    print("达到最大迭代次数，停止迭代")
                    break
                
                # 修正答案
                current_answer = await self.correct_answer(
                    question, current_answer, score, issues, suggestions
                )
            
            # 获取最终分数
            final_score = iterations[-1]['score'] if iterations else 0.0
            
            result = {
                'question': question,
                'answer': current_answer,
                'iterations': iterations,
                'final_score': final_score,
                'error': None
            }
            
            print(f"[DEBUG] SelfCorrectionNode.exec_async: Returning result={result}")
            return result
            
        except Exception as e:
            print(f"[DEBUG] SelfCorrectionNode.exec_async: Exception occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            result = {
                'question': question,
                'answer': '',
                'iterations': [],
                'final_score': 0.0,
                'error': str(e)
            }
            print(f"[DEBUG] SelfCorrectionNode.exec_async: Returning error result={result}")
            return result
    
    async def post_async(self, shared, prep_res, exec_res):
        """
        后处理方法，返回exec_async的结果
        
        Args:
            shared: 共享状态数据
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            执行结果
        """
        print(f"[DEBUG] SelfCorrectionNode.post_async: 开始执行")
        print(f"[DEBUG] SelfCorrectionNode.post_async: exec_res type={type(exec_res)}")
        print(f"[DEBUG] SelfCorrectionNode.post_async: exec_res value={exec_res}")
        print(f"[DEBUG] SelfCorrectionNode.post_async: 准备返回exec_res")
        
        # 将结果存储在shared中，以便后续访问
        if 'self_correction_results' not in shared:
            shared['self_correction_results'] = []
        shared['self_correction_results'].append(exec_res)
        
        # 返回一个简单的字符串作为action，而不是整个字典
        # 这样可以避免在get_next_node中出现"unhashable type: 'dict'"错误
        result = "completed"
        print(f"[DEBUG] SelfCorrectionNode.post_async: 返回结果 type={type(result)}, value={result}")
        return result


class ReflexionNode(AsyncNode):
    """
    反思节点
    
    反思是一种特殊的自我纠正技术，它通过反思自己的推理过程来改进答案。
    它不仅评估答案本身，还反思生成答案的推理过程，从而找到更深层次的问题。
    """
    
    def __init__(self, 
                 name: str = "ReflexionNode",
                 max_reflections: int = 3,
                 quality_threshold: float = 80.0,
                 initial_prompt: Optional[str] = None,
                 reflection_prompt: Optional[str] = None,
                 refinement_prompt: Optional[str] = None,
                 max_retries: int = 1):
        """
        初始化反思节点
        
        Args:
            name: 节点名称
            max_reflections: 最大反思次数
            quality_threshold: 质量阈值，达到此阈值则停止反思
            initial_prompt: 初始答案生成提示模板
            reflection_prompt: 反思提示模板
            refinement_prompt: 答案精炼提示模板
            max_retries: 最大重试次数
        """
        super().__init__(max_retries=max_retries)
        self.name = name
        self.max_reflections = max_reflections
        self.quality_threshold = quality_threshold
        
        # 默认初始答案生成提示模板
        self.initial_prompt = initial_prompt or """
请针对以下问题提供一个详细的答案，并展示你的推理过程：

问题：{question}

请提供一个全面、准确、有条理的答案，并详细展示你的推理过程。
"""
        
        # 默认反思提示模板
        self.reflection_prompt = reflection_prompt or """
请反思以下答案及其推理过程：

问题：{question}

答案：{answer}

请从以下角度反思：
1. 推理过程是否合理？是否有逻辑漏洞？
2. 答案是否准确？是否有事实错误？
3. 答案是否完整？是否遗漏了重要信息？
4. 答案是否清晰？是否需要更好的组织？

请给出总分（0-100分），并指出推理过程中存在的问题和改进建议。

反思结果格式：
总分：[分数]
反思：[对推理过程的反思]
改进建议：[具体的改进建议]
"""
        
        # 默认答案精炼提示模板
        self.refinement_prompt = refinement_prompt or """
基于以下反思结果，请精炼答案和推理过程：

问题：{question}

当前答案：{current_answer}

反思结果：
总分：{score}
反思：{reflection}
改进建议：{suggestions}

请根据反思结果，精炼你的答案和推理过程，解决存在的问题，并采纳改进建议。
请提供一个精炼后的答案，并展示改进后的推理过程。
"""
    
    async def generate_initial_answer(self, question: str) -> str:
        """
        生成初始答案
        
        Args:
            question: 问题
            
        Returns:
            初始答案
        """
        prompt = self.initial_prompt.format(question=question)
        return await call_llm_async(prompt)
    
    async def reflect_on_answer(self, question: str, answer: str) -> Tuple[float, str, str]:
        """
        反思答案及其推理过程
        
        Args:
            question: 问题
            answer: 答案
            
        Returns:
            (分数, 反思内容, 改进建议)
        """
        prompt = self.reflection_prompt.format(
            question=question,
            answer=answer
        )
        
        try:
            response = await call_llm_async(prompt)
            
            # 尝试从响应中提取反思结果
            score = 50.0
            reflection = ""
            suggestions = ""
            
            lines = response.strip().split('\n')
            for line in lines:
                if line.startswith('总分：'):
                    try:
                        score = float(line.split('：')[1].strip())
                        score = min(100.0, max(0.0, score))  # 确保分数在0-100范围内
                    except:
                        continue
                elif line.startswith('反思：'):
                    reflection = line.split('：', 1)[1].strip()
                elif line.startswith('改进建议：'):
                    suggestions = line.split('：', 1)[1].strip()
            
            return score, reflection, suggestions
            
        except Exception as e:
            print(f"Error reflecting on answer: {e}")
            return 50.0, "反思过程中出现错误", "请检查答案的准确性和推理过程的合理性"
    
    async def refine_answer(self, question: str, current_answer: str, 
                          score: float, reflection: str, suggestions: str) -> str:
        """
        精炼答案
        
        Args:
            question: 问题
            current_answer: 当前答案
            score: 当前分数
            reflection: 反思内容
            suggestions: 改进建议
            
        Returns:
            精炼后的答案
        """
        prompt = self.refinement_prompt.format(
            question=question,
            current_answer=current_answer,
            score=score,
            reflection=reflection,
            suggestions=suggestions
        )
        
        return await call_llm_async(prompt)
    
    async def prep_async(self, shared):
        """
        预处理方法，符合AsyncNode接口要求
        
        Args:
            shared: 共享状态数据
            
        Returns:
            共享状态数据
        """
        return shared
        
    async def exec_async(self, prep_res):
        """
        处理输入并生成反思后的答案
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            包含反思结果的字典
        """
        question = prep_res.get('question', '')
        if not question:
            return {
                'error': 'No question provided',
                'answer': '',
                'reflections': [],
                'final_score': 0.0
            }
        
        try:
            # 生成初始答案
            print("生成初始答案...")
            current_answer = await self.generate_initial_answer(question)
            
            # 记录反思历史
            reflections = []
            
            # 迭代反思和精炼答案
            for i in range(self.max_reflections):
                print(f"反思和精炼答案 - 迭代 {i+1}/{self.max_reflections}")
                
                # 反思当前答案
                score, reflection, suggestions = await self.reflect_on_answer(question, current_answer)
                
                # 记录当前反思
                reflections.append({
                    'iteration': i+1,
                    'answer': current_answer,
                    'score': score,
                    'reflection': reflection,
                    'suggestions': suggestions
                })
                
                # 如果分数达到阈值，停止反思
                if score >= self.quality_threshold:
                    print(f"答案质量达到阈值 ({self.quality_threshold})，停止反思")
                    break
                
                # 如果是最后一次反思，不再精炼
                if i == self.max_reflections - 1:
                    print("达到最大反思次数，停止反思")
                    break
                
                # 精炼答案
                current_answer = await self.refine_answer(
                    question, current_answer, score, reflection, suggestions
                )
            
            # 获取最终分数
            final_score = reflections[-1]['score'] if reflections else 0.0
            
            return {
                'question': question,
                'answer': current_answer,
                'reflections': reflections,
                'final_score': final_score,
                'error': None
            }
            
        except Exception as e:
            return {
                'question': question,
                'answer': '',
                'reflections': [],
                'final_score': 0.0,
                'error': str(e)
            }
            
    async def post_async(self, shared, prep_res, exec_res):
        """
        后处理方法，返回exec_async的结果
        
        Args:
            shared: 共享状态数据
            prep_res: 预处理结果
            exec_res: 执行结果
            
        Returns:
            执行结果
        """
        print(f"[DEBUG] SelfCorrectionNode.post_async: 开始执行")
        print(f"[DEBUG] SelfCorrectionNode.post_async: exec_res type={type(exec_res)}")
        print(f"[DEBUG] SelfCorrectionNode.post_async: exec_res value={exec_res}")
        print(f"[DEBUG] SelfCorrectionNode.post_async: 准备返回exec_res")
        result = exec_res
        print(f"[DEBUG] SelfCorrectionNode.post_async: 返回结果 type={type(result)}, value={result}")
        return result


def create_self_correction_workflow(correction_type: str = "standard") -> AsyncFlow:
    """
    创建自我纠正工作流
    
    Args:
        correction_type: 自我纠正类型，"standard"或"reflexion"
        
    Returns:
        配置好的自我纠正工作流
    """
    if correction_type == "standard":
        correction_node = SelfCorrectionNode()
    elif correction_type == "reflexion":
        correction_node = ReflexionNode()
    else:
        raise ValueError(f"Unknown correction type: {correction_type}")
    
    # 创建工作流，以correction_node为起始节点
    workflow = AsyncFlow(correction_node)
    workflow.name = f"SelfCorrectionWorkflow_{correction_type}"
    
    return workflow


# 示例使用
async def demo_self_correction():
    """
    自我纠正推理演示
    """
    # 创建标准自我纠正工作流
    self_correction_workflow = create_self_correction_workflow("standard")
    
    # 测试问题
    questions = [
        "解释为什么地球是圆的而不是平的，并提供至少三个科学证据。",
        "描述光合作用的过程，并解释它对地球生态系统的重要性。",
        "什么是量子计算？它与经典计算有什么区别？"
    ]
    
    print("=== 标准自我纠正推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await self_correction_workflow._run_async({'question': question})
        
        print(f"最终答案: {result['answer']}\n")
        print(f"最终分数: {result['final_score']}\n")
        
        # 打印迭代历史
        print("迭代历史:")
        for iteration in result['iterations']:
            print(f"  迭代{iteration['iteration']}: 分数={iteration['score']}")
            print(f"    问题: {iteration['issues']}")
            print(f"    建议: {iteration['suggestions']}\n")
        
        print("-" * 50 + "\n")
    
    # 创建反思工作流
    reflexion_workflow = create_self_correction_workflow("reflexion")
    
    print("=== 反思推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await reflexion_workflow._run_async({'question': question})
        
        print(f"最终答案: {result['answer']}\n")
        print(f"最终分数: {result['final_score']}\n")
        
        # 打印反思历史
        print("反思历史:")
        for reflection in result['reflections']:
            print(f"  反思{reflection['iteration']}: 分数={reflection['score']}")
            print(f"    反思: {reflection['reflection']}")
            print(f"    建议: {reflection['suggestions']}\n")
        
        print("-" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_self_correction())