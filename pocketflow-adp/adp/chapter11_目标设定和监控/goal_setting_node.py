"""
目标设定节点 - 用于接收和解析用户的目标
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Node

class GoalSettingNode(Node):
    """
    目标设定节点，用于接收和解析用户的目标
    """
    def prep(self, shared):
        """
        准备阶段：从共享状态中获取用户输入的目标
        """
        # 如果共享状态中没有目标，则提示用户输入
        if "use_case" not in shared:
            print("请输入您的用例（代码需求）：")
            use_case = input("> ")
            shared["use_case"] = use_case
        
        if "goals" not in shared:
            print("请输入您的目标（用逗号分隔）：")
            goals = input("> ")
            shared["goals"] = [goal.strip() for goal in goals.split(",")]
        
        return shared["use_case"], shared["goals"]
    
    def exec(self, inputs):
        """
        执行阶段：处理和验证目标
        """
        use_case, goals = inputs
        
        # 验证目标是否为空
        if not use_case.strip():
            raise ValueError("用例不能为空")
        
        if not goals or not any(goal.strip() for goal in goals):
            raise ValueError("至少需要提供一个目标")
        
        # 清理目标列表
        cleaned_goals = [goal.strip() for goal in goals if goal.strip()]
        
        return {
            "use_case": use_case.strip(),
            "goals": cleaned_goals,
            "max_iterations": 5  # 默认最大迭代次数
        }
    
    def post(self, shared, prep_res, exec_res):
        """
        后处理阶段：将处理后的目标存储到共享状态中
        """
        # 存储处理后的目标
        shared["use_case"] = exec_res["use_case"]
        shared["goals"] = exec_res["goals"]
        shared["max_iterations"] = exec_res["max_iterations"]
        shared["current_iteration"] = 0
        shared["previous_code"] = ""
        shared["feedback"] = ""
        
        # 打印目标信息
        print(f"\n目标设定完成！")
        print(f"用例: {shared['use_case']}")
        print("目标:")
        for i, goal in enumerate(shared["goals"], 1):
            print(f"  {i}. {goal}")
        print(f"最大迭代次数: {shared['max_iterations']}")
        
        # 返回下一个动作
        return "generate_code"