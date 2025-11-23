"""
ReAct (Reasoning and Acting) 推理技术实现

ReAct是一种结合推理和行动的框架，它通过交替进行推理和行动来解决问题。
在ReAct框架中，模型首先思考(Thought)如何解决问题，然后执行行动(Action)获取信息，
接着观察(Observation)行动的结果，最后基于观察结果进行新的思考，循环这个过程直到得出最终答案。
"""

import sys
import os
import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Tuple, Callable

# 添加utils路径以便导入
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from utils import call_llm, call_llm_async
from exa_search_main import search_web_exa

from pocketflow import AsyncNode, AsyncFlow


class ReActNode(AsyncNode):
    """
    ReAct节点
    
    实现推理-行动-观察循环，通过交替进行推理和行动来解决问题。
    """
    
    def __init__(self, 
                 max_iterations: int = 5,
                 thought_prompt: Optional[str] = None,
                 action_prompt: Optional[str] = None,
                 final_answer_prompt: Optional[str] = None,
                 tools: Optional[Dict[str, Callable]] = None,
                 max_retries: int = 1):
        """
        初始化ReAct节点
        
        Args:
            max_iterations: 最大迭代次数
            thought_prompt: 思考提示模板
            action_prompt: 行动提示模板
            final_answer_prompt: 最终答案提示模板
            tools: 可用工具字典，键为工具名，值为工具函数
            max_retries: 最大重试次数
        """
        self.name = "ReActNode"
        self.max_iterations = max_iterations
        super().__init__(max_retries=max_retries)
        
        # 默认思考提示模板
        self.thought_prompt = thought_prompt or """
问题：{question}

{history}

现在请思考下一步应该做什么。你的思考应该简短而明确。

思考：
"""
        
        # 默认行动提示模板
        self.action_prompt = action_prompt or """
问题：{question}

{history}

基于你的思考，请选择一个行动。可用的行动包括：
1. search[查询内容] - 使用搜索引擎查询信息
2. finish[答案] - 提供最终答案

请选择一个行动并执行：

行动：
"""
        
        # 默认最终答案提示模板
        self.final_answer_prompt = final_answer_prompt or """
问题：{question}

{history}

基于以上所有信息，请提供一个全面、准确的答案。

答案：
"""
        
        # 默认工具
        self.tools = tools or {
            "search": self._search_tool,
        }
    
    async def _search_tool(self, query: str) -> str:
        """
        搜索工具
        
        Args:
            query: 搜索查询
            
        Returns:
            搜索结果
        """
        try:
            # 导入异步版本的search_web_exa函数
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
            from utils import search_web_exa
            
            # 使用异步版本的search_web_exa函数
            search_results = await search_web_exa(query, 3)
            
            if not search_results:
                return "搜索未找到相关结果。"
            
            # 将搜索结果格式化为字符串
            formatted_results = []
            for i, result in enumerate(search_results, 1):
                title = result.get("title", "")
                url = result.get("url", "")
                snippet = result.get("snippet", "")
                formatted_results.append(f"搜索结果 {i}:\n标题: {title}\nURL: {url}\n摘要: {snippet}")
            
            return "\n\n".join(formatted_results)
            
        except Exception as e:
            return f"搜索过程中出现错误: {str(e)}"
    
    async def think(self, question: str, history: str) -> str:
        """
        思考下一步行动
        
        Args:
            question: 问题
            history: 历史记录
            
        Returns:
            思考内容
        """
        prompt = self.thought_prompt.format(
            question=question,
            history=history
        )
        
        return await call_llm_async(prompt)
    
    async def act(self, question: str, history: str) -> Tuple[str, str]:
        """
        执行行动
        
        Args:
            question: 问题
            history: 历史记录
            
        Returns:
            (行动类型, 行动内容)
        """
        prompt = self.action_prompt.format(
            question=question,
            history=history
        )
        
        response = await call_llm_async(prompt)
        
        # 解析行动
        action = response.strip()
        
        # 尝试匹配行动模式
        search_match = re.search(r'search\[(.*?)\]', action)
        finish_match = re.search(r'finish\[(.*?)\]', action)
        
        if finish_match:
            return "finish", finish_match.group(1).strip()
        elif search_match:
            return "search", search_match.group(1).strip()
        else:
            # 如果没有匹配到标准格式，尝试从文本中推断
            if "搜索" in action or "search" in action.lower():
                # 尝试提取搜索查询
                query = re.sub(r'(搜索|search)', '', action).strip('：: \n')
                return "search", query
            elif "答案" in action or "answer" in action.lower() or "完成" in action:
                # 尝试提取答案
                answer = re.sub(r'(答案|answer|完成|finish)', '', action).strip('：: \n')
                return "finish", answer
            else:
                # 默认为搜索
                return "search", action
    
    async def observe(self, action_type: str, action_content: str) -> str:
        """
        观察行动结果
        
        Args:
            action_type: 行动类型
            action_content: 行动内容
            
        Returns:
            观察结果
        """
        if action_type == "search":
            return await self._search_tool(action_content)
        elif action_type == "finish":
            return "准备提供最终答案。"
        else:
            return f"未知行动类型: {action_type}"
    
    def format_history(self, steps: List[Dict[str, str]]) -> str:
        """
        格式化历史记录
        
        Args:
            steps: 步骤列表
            
        Returns:
            格式化的历史记录
        """
        if not steps:
            return "这是第一步。"
        
        formatted_steps = []
        for i, step in enumerate(steps, 1):
            formatted_steps.append(
                f"步骤 {i}:\n"
                f"思考: {step.get('thought', '')}\n"
                f"行动: {step.get('action', '')}\n"
                f"观察: {step.get('observation', '')}\n"
            )
        
        return "\n".join(formatted_steps)
    
    async def prep_async(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备阶段，验证输入并提取问题
        
        Args:
            inputs: 输入数据，应包含'question'字段
            
        Returns:
            验证后的输入数据
        """
        question = inputs.get('question', '')
        if not question:
            return {
                'error': 'No question provided',
                'question': '',
                'steps': []
            }
        
        return {
            'question': question,
            'steps': []
        }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段，进行ReAct推理循环
        
        Args:
            prep_res: 准备阶段的输出，包含问题字段
            
        Returns:
            包含ReAct推理结果的字典
        """
        question = prep_res.get('question', '')
        steps = prep_res.get('steps', [])
        
        try:
            # ReAct循环
            action_type = ""
            action_content = ""
            
            for i in range(self.max_iterations):
                print(f"ReAct循环 - 步骤 {i+1}/{self.max_iterations}")
                
                # 格式化历史记录
                history = self.format_history(steps)
                
                # 思考
                thought = await self.think(question, history)
                print(f"思考: {thought}")
                
                # 行动
                action_type, action_content = await self.act(question, history)
                action = f"{action_type}[{action_content}]"
                print(f"行动: {action}")
                
                # 如果是完成行动，直接提供答案
                if action_type == "finish":
                    print(f"DEBUG: 检测到finish操作，action_content长度={len(action_content)}")
                    steps.append({
                        'thought': thought,
                        'action': action,
                        'observation': "准备提供最终答案。"
                    })
                    print(f"DEBUG: 已添加步骤并准备break")
                    break
                
                # 观察
                observation = await self.observe(action_type, action_content)
                print(f"观察: {observation[:100]}...")
                
                # 记录步骤
                steps.append({
                    'thought': thought,
                    'action': action,
                    'observation': observation
                })
            
            # 如果没有完成行动，生成最终答案
            final_answer = ""
            print(f"DEBUG: action_type={action_type}, action_content长度={len(action_content)}")
            print(f"DEBUG: action_content前50字符: {action_content[:50]}")
            
            if action_type != "finish" or not action_content:
                # 使用所有信息生成最终答案
                history = self.format_history(steps)
                final_prompt = self.final_answer_prompt.format(
                    question=question,
                    history=history
                )
                final_answer = await call_llm_async(final_prompt)
                print("DEBUG: 使用final_answer_prompt生成答案")
            else:
                # 如果是完成行动，但思考阶段和行动阶段答案不一致，
                # 则使用思考阶段的答案作为参考，重新生成最终答案
                thought_answer = None  # 初始化thought_answer变量
                
                if steps and 'thought' in steps[-1]:
                    thought = steps[-1]['thought']
                    # 检查思考阶段是否包含数字答案
                    import re
                    
                    # 尝试从思考阶段中提取最终答案
                    # 查找"答案："、"结果："等关键词后的数字
                    answer_patterns = [
                        r'答案[：:]\s*(\d+)',
                        r'结果[：:]\s*(\d+)',
                        r'总共[是]?(\d+)',
                        r'总计[是]?(\d+)',
                        r'一共[是]?(\d+)',
                        r'所以.*?(\d+)',
                        r'还剩.*?(\d+)',
                        r'剩下.*?(\d+)'
                    ]
                    
                    # 首先检查行动阶段是否是finish操作且包含完整答案
                    is_finish_with_content = action_type == "finish" and len(action_content.strip()) > 10
                    print(f"DEBUG: is_finish_with_content={is_finish_with_content}")
                    
                    # 只有在行动阶段不是finish操作或内容太短时，才尝试从思考阶段提取答案
                    if not is_finish_with_content:
                        for pattern in answer_patterns:
                            match = re.search(pattern, thought)
                            if match:
                                thought_answer = match.group(1)
                                break
                        
                        # 如果没有找到特定模式，尝试提取最后一个数字
                        if not thought_answer:
                            all_numbers = re.findall(r'\d+', thought)
                            if all_numbers:
                                # 通常在数学问题中，最后计算的数字是答案
                                thought_answer = all_numbers[-1]
                        
                        action_numbers = re.findall(r'\d+', action_content)
                        action_answer = action_numbers[0] if action_numbers else None
                        
                        # 如果思考阶段有数字答案，但行动阶段没有数字或行动阶段答案是"答案"等非数字内容
                        if thought_answer and (not action_answer or action_content in ["答案", "answer", "结果", "result"]):
                            print(f"检测到思考阶段有数字答案({thought_answer})但行动阶段无有效数字，使用思考阶段答案")
                            final_answer = thought_answer
                        # 如果思考阶段和行动阶段都有数字答案，且不相同
                        elif thought_answer and action_answer and thought_answer != action_answer:
                            print(f"检测到思考阶段答案({thought_answer})与行动阶段答案({action_answer})不一致，使用思考阶段答案")
                            final_answer = thought_answer
                        # 如果行动阶段答案是占位符，尝试从思考阶段提取非数字答案
                        elif action_content in ["答案", "answer", "结果", "result"]:
                            # 当行动阶段是占位符时，使用所有信息生成最终答案
                            print("检测到行动阶段是占位符，使用所有信息生成最终答案")
                            history = self.format_history(steps)
                            final_prompt = self.final_answer_prompt.format(
                                question=question,
                                history=history
                            )
                            final_answer = await call_llm_async(final_prompt)
                        else:
                            final_answer = action_content
                    else:
                        # 行动阶段是finish操作且包含完整答案，直接使用
                        final_answer = action_content
                        print("DEBUG: 直接使用action_content作为final_answer")
                    
                    # 只有在明确是数学问题且行动阶段没有提供有效答案时，才强制使用数字答案
                    if thought_answer and not is_finish_with_content and not re.match(r'^\d+$', final_answer) and any(keyword in question.lower() for keyword in ['计算', '等于', '加', '减', '乘', '除', '1+1', '2+2', '3+3']):
                        print(f"检测到数学问题但最终答案({final_answer})不是纯数字，使用思考阶段数字答案({thought_answer})")
                        final_answer = thought_answer
                else:
                    final_answer = action_content
                    print("DEBUG: 没有steps或thought，直接使用action_content")
            
            print(f"DEBUG: 最终final_answer长度={len(final_answer)}, 内容前50字符: {final_answer[:50]}")
            
            result = {
                'question': question,
                'answer': final_answer,
                'steps': steps,
                'error': None
            }
            print(f"DEBUG: 返回结果中的answer长度={len(result['answer'])}, 内容前50字符: {result['answer'][:50]}")
            
            return result
            
        except Exception as e:
            return {
                'question': question,
                'answer': '',
                'steps': steps,
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
            状态转换条件
        """
        print(f"DEBUG: ReActNode.post_async被调用")
        print(f"DEBUG: exec_res类型: {type(exec_res)}")
        print(f"DEBUG: exec_res键: {exec_res.keys() if isinstance(exec_res, dict) else '非字典'}")
        print(f"DEBUG: exec_res.get('answer')长度: {len(exec_res.get('answer', ''))}")
        print(f"DEBUG: exec_res.get('answer')前50字符: {exec_res.get('answer', '')[:50]}")
        
        # 将结果存储在shared中，以便后续访问
        if 'react_results' not in shared:
            shared['react_results'] = []
        shared['react_results'].append(exec_res)
        
        # 将最终答案也存储在shared中，方便直接访问
        answer = exec_res.get('answer', '')
        shared['react_answer'] = answer
        print(f"DEBUG: shared['react_answer']长度: {len(shared['react_answer'])}")
        print(f"DEBUG: shared['react_answer']前50字符: {shared['react_answer'][:50]}")
        
        # 返回状态转换条件
        return "default"


class ReActWithToolsNode(ReActNode):
    """
    带自定义工具的ReAct节点
    
    扩展ReAct节点以支持更多自定义工具。
    """
    
    def __init__(self, 
                 name: str = "ReActWithToolsNode",
                 max_iterations: int = 5,
                 thought_prompt: Optional[str] = None,
                 action_prompt: Optional[str] = None,
                 final_answer_prompt: Optional[str] = None,
                 tools: Optional[Dict[str, Callable]] = None,
                 max_retries: int = 1):
        """
        初始化带自定义工具的ReAct节点
        
        Args:
            name: 节点名称
            max_iterations: 最大迭代次数
            thought_prompt: 思考提示模板
            action_prompt: 行动提示模板
            final_answer_prompt: 最终答案提示模板
            tools: 可用工具字典，键为工具名，值为工具函数
        """
        # 默认工具
        default_tools = {
            "search": self._search_tool,
            "calculate": self._calculate_tool,
        }
        
        # 合并自定义工具
        if tools:
            default_tools.update(tools)
        
        # 更新行动提示模板以包含更多工具
        updated_action_prompt = action_prompt or """
问题：{question}

{history}

基于你的思考，请选择一个行动。可用的行动包括：
1. search[查询内容] - 使用搜索引擎查询信息
2. calculate[表达式] - 计算数学表达式
3. finish[答案] - 提供最终答案

请选择一个行动并执行：

行动：
"""
        
        super().__init__(
            max_iterations=max_iterations,
            thought_prompt=thought_prompt,
            action_prompt=updated_action_prompt,
            final_answer_prompt=final_answer_prompt,
            tools=default_tools,
            max_retries=max_retries
        )
        self.name = name
    
    async def _calculate_tool(self, expression: str) -> str:
        """
        计算工具
        
        Args:
            expression: 数学表达式
            
        Returns:
            计算结果
        """
        try:
            # 使用eval计算表达式，但限制可用的函数和操作符
            allowed_names = {
                "__builtins__": {},
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
            }
            
            result = eval(expression, allowed_names, {})
            return f"计算结果: {result}"
            
        except Exception as e:
            return f"计算过程中出现错误: {str(e)}"
    
    async def act(self, question: str, history: str) -> Tuple[str, str]:
        """
        执行行动（扩展版本）
        
        Args:
            question: 问题
            history: 历史记录
            
        Returns:
            (行动类型, 行动内容)
        """
        prompt = self.action_prompt.format(
            question=question,
            history=history
        )
        
        response = await call_llm_async(prompt)
        
        # 解析行动
        action = response.strip()
        
        # 尝试匹配行动模式
        search_match = re.search(r'search\[(.*?)\]', action)
        calculate_match = re.search(r'calculate\[(.*?)\]', action)
        finish_match = re.search(r'finish\[(.*?)\]', action)
        
        if finish_match:
            return "finish", finish_match.group(1).strip()
        elif search_match:
            return "search", search_match.group(1).strip()
        elif calculate_match:
            return "calculate", calculate_match.group(1).strip()
        else:
            # 如果没有匹配到标准格式，尝试从文本中推断
            if "搜索" in action or "search" in action.lower():
                # 尝试提取搜索查询
                query = re.sub(r'(搜索|search)', '', action).strip('：: \n')
                return "search", query
            elif "计算" in action or "calculate" in action.lower():
                # 尝试提取计算表达式
                expression = re.sub(r'(计算|calculate)', '', action).strip('：: \n')
                return "calculate", expression
            elif "答案" in action or "answer" in action.lower() or "完成" in action:
                # 尝试提取答案
                answer = re.sub(r'(答案|answer|完成|finish)', '', action).strip('：: \n')
                return "finish", answer
            else:
                # 默认为搜索
                return "search", action
    
    async def observe(self, action_type: str, action_content: str) -> str:
        """
        观察行动结果（扩展版本）
        
        Args:
            action_type: 行动类型
            action_content: 行动内容
            
        Returns:
            观察结果
        """
        if action_type == "search":
            # 使用与ReActNode相同的搜索工具实现
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(None, search_web_exa, action_content, 3)
            
            if not search_results:
                return "搜索未找到相关结果。"
            
            # search_web_exa返回的是字符串，不是字典列表
            # 直接返回搜索结果字符串
            return search_results
        elif action_type == "calculate":
            return await self._calculate_tool(action_content)
        elif action_type == "finish":
            return "准备提供最终答案。"
        else:
            return f"未知行动类型: {action_type}"


def create_react_workflow(with_tools: bool = False) -> AsyncFlow:
    """
    创建ReAct工作流
    
    Args:
        with_tools: 是否使用带工具的ReAct节点
        
    Returns:
        配置好的ReAct工作流
    """
    if with_tools:
        react_node = ReActWithToolsNode()
    else:
        react_node = ReActNode()
    
    # 创建工作流，以react_node为起始节点
    workflow = AsyncFlow(react_node)
    workflow.name = "ReActWorkflow"
    
    return workflow


# 示例使用
async def demo_react():
    """
    ReAct推理演示
    """
    # 创建标准ReAct工作流
    react_workflow = create_react_workflow(with_tools=False)
    
    # 测试问题
    questions = [
        "2023年诺贝尔物理学奖获得者是谁？他们的贡献是什么？",
        "计算圆的面积，如果半径为5厘米。",
        "什么是量子纠缠？它有什么应用？"
    ]
    
    print("=== ReAct推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await react_workflow._run_async({'question': question})
        
        print(f"最终答案: {result['answer']}\n")
        
        # 打印推理步骤
        print("推理步骤:")
        for j, step in enumerate(result['steps'], 1):
            print(f"  步骤{j}:")
            print(f"    思考: {step['thought']}")
            print(f"    行动: {step['action']}")
            print(f"    观察: {step['observation'][:100]}...\n")
        
        print("-" * 50 + "\n")
    
    # 创建带工具的ReAct工作流
    react_with_tools_workflow = create_react_workflow(with_tools=True)
    
    print("=== 带工具的ReAct推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await react_with_tools_workflow._run_async({'question': question})
        
        print(f"最终答案: {result['answer']}\n")
        
        # 打印推理步骤
        print("推理步骤:")
        for j, step in enumerate(result['steps'], 1):
            print(f"  步骤{j}:")
            print(f"    思考: {step['thought']}")
            print(f"    行动: {step['action']}")
            print(f"    观察: {step['observation'][:100]}...\n")
        
        print("-" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_react())