"""
人机协同模式流程实现

本模块定义了人机协同模式的完整流程，整合了所有节点：
1. TaskProcessor - 处理初始任务
2. HumanEscalation - 处理需要人工干预的情况
3. HumanInput - 接收和处理人类输入
4. ResponseGenerator - 生成最终响应

流程支持自动处理和人工干预两种模式，根据任务复杂度自动选择处理方式。
"""

import sys
import os
from typing import Dict, Any, Optional

# 添加PocketFlow路径
pocketflow_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if pocketflow_path not in sys.path:
    sys.path.append(pocketflow_path)

# 添加当前目录路径
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from pocketflow import Flow, Node
except ImportError:
    print("警告: 无法导入PocketFlow，使用模拟Flow类")
    class Node:
        def __init__(self, name: str = ""):
            self.name = name
            self.successors = {}
            self.params = {}
        
        def set_params(self, params):
            self.params = params
        
        def prep(self, shared):
            return None
        
        def exec(self, prep_res):
            return f"{self.name}_action"
        
        def post(self, shared, prep_res, exec_res):
            return exec_res
        
        def next(self, node, action="default"):
            self.successors[action] = node
            return node
        
        def __rshift__(self, other):
            return self.next(other)
    
    class Flow:
        def __init__(self, name: str = ""):
            self.name = name
            self.start_node = None
            self.params = {}
        
        def start(self, node):
            self.start_node = node
            return node
        
        def set_params(self, params):
            self.params = params
        
        def prep(self, shared):
            return None
        
        def post(self, shared, prep_res, exec_res):
            return exec_res
        
        def get_next_node(self, curr, action):
            nxt = curr.successors.get(action or "default")
            return nxt
        
        def _orch(self, shared, params=None):
            curr = self.start_node
            p = params or {**self.params}
            last_action = None
            
            while curr:
                curr.set_params(p)
                last_action = curr._run(shared)
                curr = self.get_next_node(curr, last_action)
            
            return last_action
        
        def _run(self, shared):
            p = self.prep(shared)
            o = self._orch(shared)
            return self.post(shared, p, o)

from nodes import TaskProcessor, HumanEscalation, HumanInput, ResponseGenerator


class HumanInTheLoopFlow:
    """人机协同流程类"""
    
    def __init__(self, complexity_threshold: float = 0.7, simulate_human: bool = True):
        """
        初始化人机协同流程
        
        Args:
            complexity_threshold: 任务复杂度阈值，超过此值需要人工干预
            simulate_human: 是否模拟人类输入（用于测试）
        """
        self.complexity_threshold = complexity_threshold
        self.simulate_human = simulate_human
        self.flow = self._create_flow()
    
    def _create_flow(self) -> Flow:
        """
        创建人机协同流程
        
        Returns:
            Flow: 配置好的流程对象
        """
        # 创建流程
        flow = Flow("HumanInTheLoop")
        
        # 创建节点
        task_processor = TaskProcessor(complexity_threshold=self.complexity_threshold)
        human_escalation = HumanEscalation()
        human_input = HumanInput()
        response_generator = ResponseGenerator()
        
        # 设置节点间的关系
        # 自动处理路径
        task_processor.next(response_generator, "auto_processed")
        
        # 人工干预路径
        task_processor.next(human_escalation, "escalate_to_human")
        human_escalation.next(human_input, "request_human_input")
        human_input.next(response_generator, "process_human_input")
        
        # 设置起始节点
        flow.start(task_processor)
        
        return flow
    
    def process_task(self, task: str, additional_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理任务
        
        Args:
            task: 任务描述
            additional_context: 额外上下文信息
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        # 准备共享数据
        shared_data = {
            "task": task,
            "flow_start_time": os.times()[4],  # 获取当前时间
            "complexity_threshold": self.complexity_threshold,
            "simulate_human": self.simulate_human
        }
        
        # 添加额外上下文
        if additional_context:
            shared_data.update(additional_context)
        
        print(f"🚀 开始人机协同流程处理任务")
        print(f"📋 任务: {task}")
        print(f"⚙️ 复杂度阈值: {self.complexity_threshold}")
        print(f"👥 模拟人类输入: {self.simulate_human}")
        print("-" * 50)
        
        # 执行流程
        flow_result = self.flow._run(shared_data)
        
        # 创建结果字典
        result = {
            "task": task,
            "flow_start_time": shared_data["flow_start_time"],
            "flow_end_time": os.times()[4],
            "flow_duration": os.times()[4] - shared_data["flow_start_time"],
            "final_response": shared_data.get("final_response", "响应生成失败"),
            "requires_human_intervention": shared_data.get("requires_human_intervention", False),
            "task_complexity": shared_data.get("task_complexity", 0),
            "response_type": shared_data.get("response_type", "auto"),
            "escalation_reason": shared_data.get("escalation_reason", "任务复杂度超过阈值"),
            "human_input": shared_data.get("human_input", "无人工输入")
        }
        
        print("-" * 50)
        print(f"✅ 人机协同流程处理完成")
        print(f"⏱️ 处理时间: {result['flow_duration']:.2f}秒")
        print(f"📊 响应类型: {result.get('response_type', 'unknown')}")
        
        return result


def run_human_in_the_loop_example(task: str, complexity_threshold: float = 0.7, simulate_human: bool = True):
    """
    运行人机协同示例
    
    Args:
        task: 任务描述
        complexity_threshold: 复杂度阈值
        simulate_human: 是否模拟人类输入
        
    Returns:
        Dict[str, Any]: 处理结果
    """
    # 创建人机协同流程
    hitl_flow = HumanInTheLoopFlow(
        complexity_threshold=complexity_threshold,
        simulate_human=simulate_human
    )
    
    # 处理任务
    result = hitl_flow.process_task(task)
    
    # 打印结果摘要
    print("\n📋 处理结果摘要:")
    print(f"任务: {result.get('task', 'N/A')}")
    print(f"需要人工干预: {result.get('requires_human_intervention', False)}")
    print(f"任务复杂度: {result.get('task_complexity', 0):.2f}")
    print(f"响应类型: {result.get('response_type', 'unknown')}")
    
    if result.get('requires_human_intervention'):
        # 从shared_data中获取升级原因和人类输入
        escalation_reason = result.get('escalation_reason', '任务复杂度超过阈值')
        human_input = result.get('human_input', '已接收人工输入')
        print(f"升级原因: {escalation_reason}")
        print(f"人类输入: {human_input}")
    
    print(f"\n📝 最终响应:\n{result.get('final_response', 'N/A')}")
    
    return result


if __name__ == "__main__":
    # 示例任务
    simple_task = "查询明天北京的天气"
    complex_task = "制定一个涉及多部门协作的复杂项目计划，需要考虑预算、时间和人力资源限制"
    
    print("=" * 60)
    print("人机协同模式示例 - 简单任务")
    print("=" * 60)
    run_human_in_the_loop_example(simple_task, complexity_threshold=0.7)
    
    print("\n" + "=" * 60)
    print("人机协同模式示例 - 复杂任务")
    print("=" * 60)
    run_human_in_the_loop_example(complex_task, complexity_threshold=0.7)