"""
目标设定和监控模式主流程
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import Flow
from goal_setting_node import GoalSettingNode
from code_generation_node import CodeGenerationNode
from code_evaluation_node import CodeEvaluationNode
from code_improvement_node import CodeImprovementNode

class SaveCodeNode:
    """
    保存代码节点
    """
    def __init__(self):
        self.params = {}
        self.successors = {}
    
    def set_params(self, params):
        self.params = params
    
    def next(self, node, action="default"):
        if action in self.successors:
            import warnings
            warnings.warn(f"Overwriting successor for action '{action}'")
        self.successors[action] = node
        return node
    
    def prep(self, shared):
        """
        准备阶段：获取最终代码
        """
        final_code = shared["current_code"]
        use_case = shared["use_case"]
        goals = shared["goals"]
        current_iteration = shared.get("current_iteration", 1)
        
        return final_code, use_case, goals, current_iteration
    
    def exec(self, inputs):
        """
        执行阶段：保存代码到文件
        """
        final_code, use_case, goals, current_iteration = inputs
        
        # 创建输出目录
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        file_name = f"generated_code_{current_iteration}.py"
        file_path = os.path.join(output_dir, file_name)
        
        # 写入文件
        with open(file_path, "w") as f:
            f.write(final_code)
        
        # 创建说明文件
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write(f"# 生成的代码\n\n")
            f.write(f"## 用例\n{use_case}\n\n")
            f.write(f"## 目标\n{chr(10).join(f'- {goal}' for goal in goals)}\n\n")
            f.write(f"## 迭代次数\n{current_iteration}\n\n")
            f.write(f"## 代码文件\n{file_name}\n")
        
        return file_path
    
    def post(self, shared, prep_res, exec_res):
        """
        后处理阶段：打印保存结果
        """
        final_code, use_case, goals, current_iteration = prep_res
        file_path = exec_res
        
        print(f"\n🎉 代码已保存到: {file_path}")
        print(f"📊 总共迭代了 {current_iteration} 次")
        print(f"📝 说明文件已保存到: {os.path.join(os.path.dirname(file_path), 'README.md')}")
        
        # 结束流程
        return "end"
    
    def _run(self, shared):
        p = self.prep(shared)
        e = self.exec(p)
        return self.post(shared, p, e)
    
    def __rshift__(self, other):
        return self.next(other)

def create_goal_monitoring_flow():
    """
    创建目标设定和监控流程
    """
    # 创建节点
    goal_setting = GoalSettingNode()
    code_generation = CodeGenerationNode()
    code_evaluation = CodeEvaluationNode()
    code_improvement = CodeImprovementNode()
    save_code = SaveCodeNode()
    
    # 创建流程
    flow = Flow()
    
    # 设置流程连接
    flow.start(goal_setting)
    
    # 目标设定后生成代码
    goal_setting.next(code_generation, "generate_code")
    
    # 代码生成后评估
    code_generation.next(code_evaluation, "evaluate_code")
    
    # 代码评估后根据结果决定下一步
    code_evaluation.next(code_improvement, "improve_code")
    code_evaluation.next(save_code, "save_code")
    
    # 代码改进后重新评估
    code_improvement.next(code_evaluation, "evaluate_code")
    
    return flow

def run_goal_monitoring_flow(use_case, goals, max_iterations=5):
    """
    运行目标设定和监控流程
    """
    # 创建流程
    flow = create_goal_monitoring_flow()
    
    # 初始化共享状态
    shared = {
        "use_case": use_case,
        "goals": goals,
        "max_iterations": max_iterations,
        "current_iteration": 0
    }
    
    # 运行流程
    result = flow.run(shared)
    
    return result