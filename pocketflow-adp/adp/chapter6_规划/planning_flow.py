"""
规划模式流程类 - 连接各个节点并定义转换规则
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from pocketflow import AsyncFlow
from planner_node import PlannerNode
from executor_node import ExecutorNode
from response_generator_node import ResponseGeneratorNode


class PlanningFlow(AsyncFlow):
    """规划模式流程，实现任务的自动规划和执行"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化节点
        self.planner = PlannerNode()
        self.executor = ExecutorNode()
        self.response_generator = ResponseGeneratorNode()
        
        # 定义流程转换规则
        # 使用 next 方法连接节点
        self.planner.next(self.executor, action="execute_plan")
        self.executor.next(self.executor, action="execute_plan")  # 循环执行步骤
        self.executor.next(self.response_generator, action="generate_response")
        
        # 设置起始节点
        self.start(self.planner)
        
    async def run(self, task, context=""):
        """运行规划流程"""
        # 初始化共享状态
        shared_state = {
            "task": task,
            "context": context,
            "plan": {},
            "step_results": [],
            "current_step": 0,
            "total_steps": 0,
            "final_response": ""
        }
        
        # 执行流程
        result = await self.run_async(shared_state)
        return result.get("final_response", "未能生成响应")
    
    def get_plan(self, shared_state):
        """获取当前计划"""
        return shared_state.get("plan", {})
    
    def get_step_results(self, shared_state):
        """获取步骤执行结果"""
        return shared_state.get("step_results", [])
    
    def get_progress(self, shared_state):
        """获取当前执行进度"""
        current_step = shared_state.get("current_step", 0)
        total_steps = shared_state.get("total_steps", 0)
        return {
            "current_step": current_step,
            "total_steps": total_steps,
            "progress_percent": (current_step / total_steps * 100) if total_steps > 0 else 0
        }