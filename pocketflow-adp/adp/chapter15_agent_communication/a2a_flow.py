"""
A2A流程定义

本文件包含A2AFlow和CollaborationFlow类，用于定义Agent间的通信和协作流程。
"""

import sys
import os
from typing import Dict, Any, Optional, List, Callable

# 添加父目录到系统路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pocketflow import Flow, ExecutionResult
except ImportError:
    # 如果无法导入，创建一个简单的替代实现
    class Flow:
        """简单的Flow替代实现"""
        def __init__(self, name: str, description: str = ""):
            self.name = name
            self.description = description
        
        def execute(self, context: Dict[str, Any] = None) -> Any:
            """执行流程"""
            return {"status": "completed", "result": f"Flow {self.name} executed"}
    
    class ExecutionResult:
        """简单的ExecutionResult替代实现"""
        def __init__(self, status: str, result: Any = None, error: Optional[str] = None):
            self.status = status
            self.result = result
            self.error = error

from adp.chapter15_agent_communication.agent_card import AgentCard
from adp.chapter15_agent_communication.a2a_nodes import (
    SendTaskNode, ReceiveTaskNode, DiscoverAgentsNode, 
    TaskResultNode, TaskRequestNode
)
from adp.chapter15_agent_communication.agent_registry import AgentRegistry


class A2AFlow(Flow):
    """
    A2A流程类
    
    定义Agent间的通信流程，包括任务发送、接收和结果处理。
    """
    
    def __init__(
        self, 
        name: str = "A2A Communication",
        description: str = "Agent-to-Agent communication flow",
        agent_registry: Optional[AgentRegistry] = None
    ):
        """
        初始化A2A流程
        
        Args:
            name: 流程名称
            description: 流程描述
            agent_registry: Agent注册表
        """
        super().__init__(name, description)
        self.agent_registry = agent_registry or AgentRegistry()
        
        # 创建流程节点
        self.send_task_node = SendTaskNode(
            "send_task", 
            "Send task to another agent",
            agent_registry=self.agent_registry
        )
        
        self.receive_task_node = ReceiveTaskNode(
            "receive_task", 
            "Receive task from another agent",
            agent_registry=self.agent_registry
        )
        
        self.task_result_node = TaskResultNode(
            "task_result", 
            "Process task result"
        )
        
        self.discover_agents_node = DiscoverAgentsNode(
            "discover_agents", 
            "Discover available agents",
            agent_registry=self.agent_registry
        )
    
    def send_task(
        self, 
        sender_id: str, 
        receiver_id: str, 
        task_data: Dict[str, Any],
        task_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        发送任务到另一个Agent
        
        Args:
            sender_id: 发送者ID
            receiver_id: 接收者ID
            task_data: 任务数据
            task_handler: 任务处理函数
            
        Returns:
            任务执行结果
        """
        # 准备上下文
        context = {
            "sender_id": sender_id,
            "receiver_id": receiver_id,
            "task_data": task_data,
            "task_handler": task_handler
        }
        
        # 执行发送任务节点
        result = self.send_task_node.execute(context)
        
        return result
    
    def receive_task(
        self, 
        receiver_id: Optional[str] = None,
        request: Optional[Dict[str, Any]] = None,
        task_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        接收来自另一个Agent的任务
        
        Args:
            receiver_id: 接收者ID
            request: 任务请求
            task_handler: 任务处理函数
            
        Returns:
            任务执行结果
        """
        # 准备上下文
        context = {
            "receiver_id": receiver_id,
            "request": request,
            "task_handler": task_handler
        }
        
        # 执行接收任务节点
        result = self.receive_task_node.execute(context)
        
        return result
    
    def discover_agents(self, query: str = "") -> List[AgentCard]:
        """
        发现可用的Agent
        
        Args:
            query: 查询条件
            
        Returns:
            匹配的Agent列表
        """
        # 准备上下文
        context = {"query": query}
        
        # 执行发现Agent节点
        result = self.discover_agents_node.execute(context)
        
        return result.get("agents", [])
    
    def create_collaboration_flow(self, agents: List[str] = None, initial_message: Dict[str, Any] = None, max_iterations: int = 3) -> 'CollaborationFlow':
        """
        创建协作流程
        
        Args:
            agents: 要协作的Agent名称列表
            initial_message: 初始消息
            max_iterations: 最大迭代次数
            
        Returns:
            协作流程实例
        """
        collaboration_flow = CollaborationFlow(agent_registry=self.agent_registry)
        
        # 设置协作参数
        if agents:
            collaboration_flow.agents = agents
        if initial_message:
            collaboration_flow.initial_message = initial_message
        if max_iterations:
            collaboration_flow.max_iterations = max_iterations
            
        return collaboration_flow
    
    def execute(self, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        执行A2A流程
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = {}
        
        # 根据上下文确定执行的操作
        operation = context.get("operation", "send_task")
        
        if operation == "send_task":
            result = self.send_task(
                context.get("sender_id", ""),
                context.get("receiver_id", ""),
                context.get("task_data", {}),
                context.get("task_handler")
            )
        elif operation == "receive_task":
            result = self.receive_task(
                context.get("receiver_id", ""),
                context.get("task_handler")
            )
        elif operation == "discover_agents":
            agents = self.discover_agents(context.get("query", ""))
            result = {"agents": agents}
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        # 返回执行结果
        if "error" in result:
            return ExecutionResult("failed", error=result["error"])
        else:
            return ExecutionResult("completed", result)


class CollaborationFlow(Flow):
    """
    协作流程类
    
    定义多个Agent之间的协作流程，包括任务分发、结果收集和协调。
    """
    
    def __init__(
        self, 
        name: str = "Agent Collaboration",
        description: str = "Multi-agent collaboration flow",
        agent_registry: Optional[AgentRegistry] = None
    ):
        """
        初始化协作流程
        
        Args:
            name: 流程名称
            description: 流程描述
            agent_registry: Agent注册表
        """
        super().__init__(name, description)
        self.agent_registry = agent_registry or AgentRegistry()
        
        # 创建任务请求节点
        self.task_request_node = TaskRequestNode(
            "task_request", 
            "Request task from multiple agents",
            agent_registry=self.agent_registry
        )
        
        # 创建任务结果节点
        self.task_result_node = TaskResultNode(
            "task_result", 
            "Collect and process task results"
        )
    
    def distribute_task(
        self, 
        coordinator_id: str, 
        task_data: Dict[str, Any],
        target_agents: Optional[List[str]] = None,
        task_handler: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        分发任务到多个Agent
        
        Args:
            coordinator_id: 协调者ID
            task_data: 任务数据
            target_agents: 目标Agent ID列表
            task_handler: 任务处理函数
            
        Returns:
            任务分发结果
        """
        # 准备上下文
        context = {
            "coordinator_id": coordinator_id,
            "task_data": task_data,
            "target_agents": target_agents,
            "task_handler": task_handler
        }
        
        # 执行任务请求节点
        result = self.task_request_node.execute(context)
        
        return result
    
    def collect_results(
        self, 
        coordinator_id: str, 
        task_id: str
    ) -> Dict[str, Any]:
        """
        收集任务结果
        
        Args:
            coordinator_id: 协调者ID
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        # 准备上下文
        context = {
            "coordinator_id": coordinator_id,
            "task_id": task_id
        }
        
        # 执行任务结果节点
        result = self.task_result_node.execute(context)
        
        return result
    
    def execute(self, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        执行协作流程
        
        Args:
            context: 执行上下文
            
        Returns:
            执行结果
        """
        if context is None:
            context = {}
        
        # 根据上下文确定执行的操作
        operation = context.get("operation", "distribute_task")
        
        if operation == "distribute_task":
            result = self.distribute_task(
                context.get("coordinator_id", ""),
                context.get("task_data", {}),
                context.get("target_agents"),
                context.get("task_handler")
            )
        elif operation == "collect_results":
            result = self.collect_results(
                context.get("coordinator_id", ""),
                context.get("task_id", "")
            )
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        # 返回执行结果
        if "error" in result:
            return ExecutionResult("failed", error=result["error"])
        else:
            return ExecutionResult("completed", result)
    
    async def run(self) -> Dict[str, Any]:
        """
        运行协作流程
        
        Returns:
            协作结果
        """
        # 获取协作参数
        agents = getattr(self, 'agents', [])
        initial_message = getattr(self, 'initial_message', {})
        max_iterations = getattr(self, 'max_iterations', 3)
        
        # 如果没有指定Agent，返回错误
        if not agents:
            return {
                "status": "error",
                "error": "未指定要协作的Agent"
            }
        
        # 模拟协作过程
        conversation_history = []
        
        # 为每个Agent生成响应
        for agent_name in agents:
            # 在实际实现中，这里应该调用相应Agent的处理函数
            # 为了演示，我们生成一个简单的响应
            if agent_name == "WeatherBot":
                response = "天气查询结果：北京今天天气晴朗，温度25°C，微风，适合外出。"
            elif agent_name == "NewsBot":
                response = "新闻查询结果：最新科技新闻：人工智能技术在医疗领域取得重大突破。"
            elif agent_name == "TranslationBot":
                response = "翻译结果：Hello的中文翻译是：你好。"
            else:
                response = f"{agent_name}：已处理请求。"
            
            # 添加到对话历史
            conversation_history.append({
                "agent": agent_name,
                "response": response
            })
        
        # 返回协作结果
        return {
            "status": "completed",
            "conversation_history": conversation_history
        }


def create_a2a_flow(agent_registry: Optional[AgentRegistry] = None) -> A2AFlow:
    """
    创建A2A流程
    
    Args:
        agent_registry: Agent注册表
        
    Returns:
        A2A流程实例
    """
    return A2AFlow(agent_registry=agent_registry)


def create_collaboration_flow(agent_registry: Optional[AgentRegistry] = None) -> CollaborationFlow:
    """
    创建协作流程
    
    Args:
        agent_registry: Agent注册表
        
    Returns:
        协作流程实例
    """
    return CollaborationFlow(agent_registry=agent_registry)