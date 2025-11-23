"""
代码评估节点 - 用于评估代码是否满足目标
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node
from utils.utils import call_llm

class CodeEvaluationNode(Node):
    """
    代码评估节点，用于评估代码是否满足目标
    """
    def prep(self, shared):
        """
        准备阶段：从共享状态中获取代码和目标
        """
        code = shared["current_code"]
        goals = shared["goals"]
        current_iteration = shared.get("current_iteration", 1)
        max_iterations = shared.get("max_iterations", 5)
        
        return code, goals, current_iteration, max_iterations
    
    def exec(self, inputs):
        """
        执行阶段：使用LLM评估代码
        """
        code, goals, current_iteration, max_iterations = inputs
        
        # 构建评估提示词
        feedback_prompt = self._build_feedback_prompt(code, goals)
        
        # 调用LLM获取反馈
        feedback = call_llm(feedback_prompt)
        
        # 构建目标检查提示词
        goals_check_prompt = self._build_goals_check_prompt(goals, feedback)
        
        # 调用LLM检查目标是否达成
        goals_check_response = call_llm(goals_check_prompt)
        
        # 解析目标是否达成
        goals_met = self._parse_goals_met(goals_check_response)
        
        return {
            "feedback": feedback,
            "goals_met": goals_met,
            "goals_check_response": goals_check_response
        }
    
    def post(self, shared, prep_res, exec_res):
        """
        后处理阶段：根据评估结果决定下一步
        """
        code, goals, current_iteration, max_iterations = prep_res
        feedback = exec_res["feedback"]
        goals_met = exec_res["goals_met"]
        
        # 存储反馈
        shared["feedback"] = feedback
        
        # 打印反馈
        print(f"\n=== 代码评估反馈 ===")
        print(feedback)
        print("=" * 50)
        
        # 决定下一步动作
        if goals_met:
            print("✅ 目标已达成！")
            return "save_code"
        elif current_iteration >= max_iterations:
            print(f"⚠️ 已达到最大迭代次数 {max_iterations}，停止改进。")
            return "save_code"
        else:
            print(f"🔄 目标未完全达成，准备第 {current_iteration + 1} 次迭代...")
            shared["previous_code"] = code
            return "improve_code"
    
    def _build_feedback_prompt(self, code, goals):
        """
        构建代码反馈提示词
        """
        prompt = f"""
你是一个Python代码审查员。下面显示了一个代码片段。

基于以下目标：
{chr(10).join(f"- {goal}" for goal in goals)}

请对此代码进行批评并确定是否满足目标。提及是否需要改进清晰度、简单性、正确性、边缘情况处理或测试覆盖率。

代码：
{code}
"""
        return prompt
    
    def _build_goals_check_prompt(self, goals, feedback):
        """
        构建目标检查提示词
        """
        prompt = f"""
你是一个AI审查员。这些是目标：
{chr(10).join(f"- {goal}" for goal in goals)}

这是关于代码的反馈：

{feedback}

根据上述反馈，目标是否已达成？仅用一个词回答：True 或 False。
"""
        return prompt
    
    def _parse_goals_met(self, response):
        """
        解析目标是否达成
        """
        response = response.strip().lower()
        return response == "true"