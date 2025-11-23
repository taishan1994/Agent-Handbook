"""
思维链(Chain of Thought, CoT)推理技术实现

思维链是一种通过引导模型逐步思考问题来解决复杂任务的技术。
它要求模型在给出最终答案之前，先展示其推理过程，从而提高解决复杂问题的准确性。
"""

import sys
import os
import asyncio
from typing import Dict, List, Any, Optional

# 添加utils路径以便导入
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from utils import call_llm, call_llm_async

from pocketflow import AsyncNode, AsyncFlow


class ChainOfThoughtNode(AsyncNode):
    """
    思维链节点
    
    该节点通过引导模型逐步思考问题来解决复杂任务。
    它会生成一个思维链提示，引导模型逐步推理，并最终得出答案。
    """
    
    def __init__(self, name: str = "ChainOfThoughtNode", 
                 cot_template: Optional[str] = None,
                 max_thinking_steps: int = 5,
                 max_retries: int = 1):
        """
        初始化思维链节点
        
        Args:
            name: 节点名称
            cot_template: 自定义思维链提示模板
            max_thinking_steps: 最大思考步骤数
            max_retries: 最大重试次数
        """
        self.name = name
        super().__init__(max_retries=max_retries)
        self.max_thinking_steps = max_thinking_steps
        
        # 默认思维链提示模板
        self.cot_template = cot_template or """
请按照以下步骤逐步思考并回答问题：

问题：{question}

步骤1：理解问题
首先，仔细阅读并理解问题的核心要求和限制条件。

步骤2：分析关键信息
识别问题中的关键信息和已知条件。

步骤3：制定解决方案
基于问题要求和已知条件，设计一个分步解决方案。

步骤4：执行解决方案
按照设计的步骤逐步解决问题，展示每一步的计算和推理过程。

步骤5：验证答案
检查你的解决方案是否合理，并验证最终答案的正确性。

请按照上述步骤详细思考，并给出最终答案。
"""
    
    async def prep_async(self, shared):
        """预处理输入数据"""
        return shared
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理方法，返回执行结果"""
        # 获取结果字典
        result = getattr(self, 'last_result', {
            'question': prep_res.get('question', ''),
            'answer': '',
            'reasoning': '',
            'error': 'No result available'
        })
        
        # 将结果存储在shared中，以便外部访问
        if 'cot_results' not in shared:
            shared['cot_results'] = []
        shared['cot_results'].append(result)
        
        # 返回一个简单的字符串作为action
        return "completed"
    
    async def exec_async(self, prep_res):
        """
        处理输入并生成思维链推理结果
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            思维链推理结果字符串
        """
        question = prep_res.get('question', '')
        if not question:
            return "错误：未提供问题"
        
        # 生成思维链提示
        cot_prompt = self.cot_template.format(question=question)
        
        try:
            # 调用LLM生成思维链推理
            reasoning = await call_llm_async(cot_prompt)
            
            # 提取答案（假设答案在推理过程的最后）
            # 这里可以进一步优化，使用更精确的提取方法
            lines = reasoning.strip().split('\n')
            answer = ""
            
            # 尝试从最后几行中提取答案
            for line in reversed(lines[-5:]):
                if line.strip() and not line.startswith(('步骤', 'Step', '分析', '执行', '验证')):
                    answer = line.strip()
                    break
            
            # 如果没有找到明确的答案，使用整个推理结果作为答案
            if not answer:
                answer = reasoning
            
            # 将结果存储在实例变量中，以便在post_async中访问
            self.last_result = {
                'question': question,
                'answer': answer,
                'reasoning': reasoning,
                'error': None
            }
            
            # 返回一个简单的字符串作为action
            return "completed"
            
        except Exception as e:
            # 将错误结果存储在实例变量中
            self.last_result = {
                'question': question,
                'answer': '',
                'reasoning': '',
                'error': str(e)
            }
            
            # 返回一个简单的字符串作为action
            return "error"


class FewShotCoTNode(AsyncNode):
    """
    少样本思维链节点
    
    该节点使用少样本示例来引导模型进行思维链推理。
    通过提供示例，模型可以更好地理解如何进行逐步推理。
    """
    
    def __init__(self, name: str = "FewShotCoTNode", 
                 examples: Optional[List[Dict[str, str]]] = None,
                 max_retries: int = 1):
        """
        初始化少样本思维链节点
        
        Args:
            name: 节点名称
            examples: 少样本示例列表，每个示例包含'question'和'reasoning'字段
            max_retries: 最大重试次数
        """
        self.name = name
        super().__init__(max_retries=max_retries)
        
        # 默认示例
        self.examples = examples or [
            {
                'question': '一个农场有鸡和兔子共35个头，94只脚。问鸡和兔子各有多少只？',
                'reasoning': '''
步骤1：理解问题
我们需要找出农场中鸡和兔子的数量。已知总共有35个头和94只脚。

步骤2：分析关键信息
- 鸡有1个头，2只脚
- 兔子有1个头，4只脚
- 总头数：35
- 总脚数：94

步骤3：制定解决方案
设鸡的数量为x，兔子的数量为y。
根据题意，我们可以列出方程组：
x + y = 35  (头的总数)
2x + 4y = 94  (脚的总数)

步骤4：执行解决方案
从第一个方程得到：x = 35 - y
将x代入第二个方程：
2(35 - y) + 4y = 94
70 - 2y + 4y = 94
2y = 24
y = 12

因此，x = 35 - 12 = 23

步骤5：验证答案
鸡：23只，脚数：23 × 2 = 46
兔子：12只，脚数：12 × 4 = 48
总脚数：46 + 48 = 94 ✓

答案：农场有23只鸡和12只兔子。
'''
            },
            {
                'question': '小明去商店买文具，买了3支笔和2个本子，共花了27元。如果1支笔比1个本子贵3元，求笔和本子的价格各是多少？',
                'reasoning': '''
步骤1：理解问题
我们需要找出笔和本子的价格。已知3支笔和2个本子共27元，且1支笔比1个本子贵3元。

步骤2：分析关键信息
- 设本子的价格为x元
- 笔的价格为x + 3元
- 3支笔和2个本子共27元

步骤3：制定解决方案
根据题意，我们可以列出方程：
3(x + 3) + 2x = 27

步骤4：执行解决方案
3x + 9 + 2x = 27
5x = 18
x = 3.6

因此，本子的价格为3.6元，笔的价格为3.6 + 3 = 6.6元。

步骤5：验证答案
3支笔：3 × 6.6 = 19.8元
2个本子：2 × 3.6 = 7.2元
总花费：19.8 + 7.2 = 27元 ✓

答案：笔的价格是6.6元，本子的价格是3.6元。
'''
            }
        ]
    
    async def prep_async(self, shared):
        """预处理输入数据"""
        return shared
    
    async def post_async(self, shared, prep_res, exec_res):
        """后处理方法，返回执行结果"""
        # 获取结果字典
        result = getattr(self, 'last_result', {
            'question': prep_res.get('question', ''),
            'answer': '',
            'reasoning': '',
            'error': 'No result available'
        })
        
        # 将结果存储在shared中，以便外部访问
        if 'cot_results' not in shared:
            shared['cot_results'] = []
        shared['cot_results'].append(result)
        
        # 返回一个简单的字符串作为action
        return "completed"
    
    async def exec_async(self, prep_res):
        """
        处理输入并生成少样本思维链推理结果
        
        Args:
            prep_res: 预处理结果，应包含'question'字段
            
        Returns:
            少样本思维链推理结果字符串
        """
        question = prep_res.get('question', '')
        if not question:
            self.last_result = {
                'error': 'No question provided',
                'answer': '',
                'reasoning': ''
            }
            return "error"
        
        # 构建少样本提示
        examples_text = ""
        for i, example in enumerate(self.examples, 1):
            examples_text += f"""
示例{i}：
问题：{example['question']}
推理过程：{example['reasoning']}
"""
        
        few_shot_prompt = f"""
以下是一些思维链推理的示例：

{examples_text}

现在，请按照上述示例的格式，逐步思考并回答以下问题：

问题：{question}

请按照示例的格式，详细展示你的推理过程，并给出最终答案。
"""
        
        try:
            # 调用LLM生成思维链推理
            reasoning = await call_llm_async(few_shot_prompt)
            
            # 提取答案（假设答案在推理过程的最后）
            lines = reasoning.strip().split('\n')
            answer = ""
            
            # 尝试从最后几行中提取答案
            for line in reversed(lines[-5:]):
                if line.strip() and not line.startswith(('示例', '问题', '推理', '步骤', 'Step', '分析', '执行', '验证')):
                    answer = line.strip()
                    break
            
            # 如果没有找到明确的答案，使用整个推理结果作为答案
            if not answer:
                answer = reasoning
            
            # 将结果存储在实例变量中，以便在post_async中访问
            self.last_result = {
                'question': question,
                'answer': answer,
                'reasoning': reasoning,
                'error': None
            }
            
            # 返回一个简单的字符串作为action
            return "completed"
            
        except Exception as e:
            # 将错误结果存储在实例变量中
            self.last_result = {
                'question': question,
                'answer': '',
                'reasoning': '',
                'error': str(e)
            }
            
            # 返回一个简单的字符串作为action
            return "error"


def create_cot_workflow(cot_type: str = "standard") -> AsyncFlow:
    """
    创建思维链工作流
    
    Args:
        cot_type: 思维链类型，"standard"或"few_shot"
        
    Returns:
        配置好的思维链工作流
    """
    if cot_type == "standard":
        cot_node = ChainOfThoughtNode()
    elif cot_type == "few_shot":
        cot_node = FewShotCoTNode()
    else:
        raise ValueError(f"Unknown CoT type: {cot_type}")
    
    # 创建工作流，以cot_node为起始节点
    workflow = AsyncFlow(cot_node)
    workflow.name = f"ChainOfThoughtWorkflow_{cot_type}"
    
    return workflow


# 示例使用
async def demo_chain_of_thought():
    """
    思维链推理演示
    """
    # 创建标准思维链工作流
    cot_workflow = create_cot_workflow("standard")
    
    # 测试问题
    questions = [
        "一个班级有40名学生，其中男生比女生多6人。问男生和女生各有多少人？",
        "小明有50元钱，买了3本书，每本书的价格不同，最贵的书比最便宜的书贵10元，中间价格的书比最便宜的书贵5元。问三本书的价格各是多少？",
        "一个长方形的周长是24厘米，长是宽的2倍。求这个长方形的面积。"
    ]
    
    print("=== 标准思维链推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await cot_workflow._run_async({'question': question})
        
        print(f"答案: {result['answer']}\n")
        print(f"推理过程:\n{result['reasoning']}\n")
        print("-" * 50 + "\n")
    
    # 创建少样本思维链工作流
    few_shot_cot_workflow = create_cot_workflow("few_shot")
    
    print("=== 少样本思维链推理演示 ===\n")
    
    for i, question in enumerate(questions, 1):
        print(f"问题{i}: {question}")
        
        # 执行工作流
        result = await few_shot_cot_workflow._run_async({'question': question})
        
        print(f"答案: {result['answer']}\n")
        print(f"推理过程:\n{result['reasoning']}\n")
        print("-" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(demo_chain_of_thought())