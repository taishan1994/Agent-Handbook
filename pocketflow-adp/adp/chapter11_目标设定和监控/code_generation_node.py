"""
代码生成节点 - 用于根据目标生成初始代码
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm

class CodeGenerationNode(Node):
    """
    代码生成节点，用于根据目标生成初始代码
    """
    def prep(self, shared):
        """
        准备阶段：从共享状态中获取目标和之前的代码
        """
        use_case = shared["use_case"]
        goals = shared["goals"]
        previous_code = shared.get("previous_code", "")
        feedback = shared.get("feedback", "")
        current_iteration = shared.get("current_iteration", 0)
        
        return use_case, goals, previous_code, feedback, current_iteration
    
    def exec(self, inputs):
        """
        执行阶段：使用LLM生成代码
        """
        use_case, goals, previous_code, feedback, current_iteration = inputs
        
        # 构建提示词
        prompt = self._build_prompt(use_case, goals, previous_code, feedback, current_iteration)
        
        # 调用LLM生成代码
        response = call_llm(prompt)
        
        # 清理代码块
        code = self._clean_code_block(response)
        
        return code
    
    def post(self, shared, prep_res, exec_res):
        """
        后处理阶段：将生成的代码存储到共享状态中
        """
        use_case, goals, previous_code, feedback, current_iteration = prep_res
        generated_code = exec_res
        
        # 存储生成的代码
        shared["current_code"] = generated_code
        shared["current_iteration"] = current_iteration + 1
        
        # 打印生成的代码
        print(f"\n=== 迭代 {current_iteration + 1} 生成的代码 ===")
        print(generated_code)
        print("=" * 50)
        
        # 返回下一个动作
        return "evaluate_code"
    
    def _build_prompt(self, use_case, goals, previous_code="", feedback="", iteration=0):
        """
        构建代码生成的提示词
        """
        base_prompt = f"""
你是一个AI编程助手。你的任务是根据以下用例编写Python代码：

用例：{use_case}

你的目标是：
{chr(10).join(f"- {goal}" for goal in goals)}
"""
        
        # 如果不是第一次迭代，添加之前的代码和反馈
        if iteration > 0 and previous_code:
            base_prompt += f"\n之前生成的代码：\n{previous_code}"
        
        if feedback:
            base_prompt += f"\n对之前版本的反馈：\n{feedback}\n"
        
        base_prompt += "\n请仅返回Python代码，不要包含额外的解释或注释。"
        
        return base_prompt
    
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