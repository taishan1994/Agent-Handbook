"""
代码改进节点 - 用于根据评估反馈改进代码
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm

class CodeImprovementNode(Node):
    """
    代码改进节点，用于根据评估反馈改进代码
    """
    def prep(self, shared):
        """
        准备阶段：从共享状态中获取代码、目标和反馈
        """
        previous_code = shared["previous_code"]
        goals = shared["goals"]
        feedback = shared["feedback"]
        current_iteration = shared.get("current_iteration", 1)
        
        return previous_code, goals, feedback, current_iteration
    
    def exec(self, inputs):
        """
        执行阶段：使用LLM改进代码
        """
        previous_code, goals, feedback, current_iteration = inputs
        
        # 构建改进提示词
        prompt = self._build_improvement_prompt(previous_code, goals, feedback, current_iteration)
        
        # 调用LLM改进代码
        response = call_llm(prompt)
        
        # 清理代码块
        improved_code = self._clean_code_block(response)
        
        return improved_code
    
    def post(self, shared, prep_res, exec_res):
        """
        后处理阶段：将改进后的代码存储到共享状态中
        """
        previous_code, goals, feedback, current_iteration = prep_res
        improved_code = exec_res
        
        # 存储改进后的代码
        shared["current_code"] = improved_code
        shared["previous_code"] = previous_code
        shared["current_iteration"] = current_iteration + 1
        
        # 打印改进后的代码
        print(f"\n=== 迭代 {current_iteration + 1} 改进后的代码 ===")
        print(improved_code)
        print("=" * 50)
        
        # 返回下一个动作
        return "evaluate_code"
    
    def _build_improvement_prompt(self, previous_code, goals, feedback, iteration):
        """
        构建代码改进的提示词
        """
        prompt = f"""
你是一个AI编程助手。你的任务是改进以下Python代码以更好地满足目标：

目标：
{chr(10).join(f"- {goal}" for goal in goals)}

之前版本的代码：
{previous_code}

对之前版本的反馈：
{feedback}

请根据反馈改进代码，确保它更好地满足目标。请仅返回改进后的Python代码，不要包含额外的解释或注释。

这是第 {iteration + 1} 次改进。
"""
        return prompt
    
    def _clean_code_block(self, code):
        """
        清理代码块，移除markdown标记
        """
        lines = code.strip().splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()