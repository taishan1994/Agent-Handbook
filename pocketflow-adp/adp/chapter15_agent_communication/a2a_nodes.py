"""
A2A通信节点实现

本文件包含A2A通信协议的核心节点，用于发送任务、接收任务和发现Agent。
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, Optional, List, Callable
import sys
import os

# 添加父目录到系统路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from pocketflow import Node
except ImportError:
    # 如果无法导入，创建一个简单的替代实现
    class Node:
        """简单的Node替代实现"""
        def __init__(self, name: str):
            self.name = name
        
        async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
            """执行节点"""
            return {"status": "completed", "result": f"Node {self.name} executed"}

from adp.chapter15_agent_communication.agent_card import AgentCard
from adp.chapter15_agent_communication.agent_registry import AgentRegistry


class SendTaskNode(Node):
    """
    发送任务节点
    
    用于向其他Agent发送任务请求。
    """
    
    def __init__(self, name: str = "send_task", description: str = "", agent_registry: Optional[AgentRegistry] = None):
        super().__init__(name)
        self.description = description
        self.agent_registry = agent_registry or AgentRegistry()
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行发送任务
        
        Args:
            inputs: 输入数据，包含:
                   - sender_id: 发送者ID
                   - receiver_id: 接收者ID
                   - task_data: 任务数据
                   - task_handler: 任务处理函数
        
        Returns:
            执行结果，包含任务响应
        """
        sender_id = inputs.get("sender_id")
        receiver_id = inputs.get("receiver_id")
        task_data = inputs.get("task_data", {})
        task_handler = inputs.get("task_handler")
        
        if not sender_id or not receiver_id:
            return {
                "success": False,
                "error": "缺少发送者ID或接收者ID"
            }
        
        # 获取目标Agent
        target_agent = self.agent_registry.get_agent(receiver_id)
        if not target_agent:
            return {
                "success": False,
                "error": f"未找到ID为{receiver_id}的Agent"
            }
        
        # 构造A2A任务请求
        a2a_request = {
            "jsonrpc": "2.0",
            "id": f"task_{sender_id}_{receiver_id}_{id(self)}",
            "method": "tasks/send",
            "params": {
                "task": task_data,
                "context": {
                    "sender_id": sender_id,
                    "receiver_id": receiver_id
                }
            }
        }
        
        # 发送请求
        response = await self._send_request(target_agent, a2a_request)
        
        return {
            "success": True,
            "response": response
        }
    
    async def _send_request(self, target_agent: AgentCard, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            target_agent: 目标Agent
            request: 请求内容
        
        Returns:
            响应内容
        """
        try:
            # 获取目标Agent的通信端点
            if not target_agent.communication.endpoints:
                return {
                    "error": "目标Agent没有配置通信端点"
                }
            
            endpoint = target_agent.communication.endpoints[0]
            url = f"{endpoint.protocol}://{endpoint.host}:{endpoint.port}{endpoint.path}"
            
            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        return {
                            "error": f"请求失败，状态码: {response.status}"
                        }
        except Exception as e:
            return {
                "error": f"请求异常: {str(e)}"
            }


class ReceiveTaskNode(Node):
    """
    接收任务节点
    
    用于接收和处理来自其他Agent的任务请求。
    """
    
    def __init__(self, name: str = "receive_task", description: str = "", agent_registry: Optional[AgentRegistry] = None):
        super().__init__(name)
        self.description = description
        self.agent_registry = agent_registry or AgentRegistry()
        self.task_handler = None
    
    def set_task_handler(self, handler: Callable):
        """
        设置任务处理函数
        
        Args:
            handler: 任务处理函数，接收任务和上下文，返回处理结果
        """
        self.task_handler = handler
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行接收任务
        
        Args:
            inputs: 输入数据，包含:
                   - receiver_id: 接收者ID
                   - request: 任务请求
                   - task_handler: 任务处理函数
        
        Returns:
            执行结果，包含任务响应
        """
        receiver_id = inputs.get("receiver_id")
        request = inputs.get("request")
        task_handler = inputs.get("task_handler") or self.task_handler
        
        if not receiver_id:
            return {
                "success": False,
                "error": "缺少接收者ID"
            }
        
        # 获取当前Agent
        # 首先尝试通过ID查找，如果失败则尝试通过名称查找
        current_agent = self.agent_registry.get_agent(receiver_id)
        if not current_agent:
            # 尝试通过名称查找
            for agent in self.agent_registry.list_agents():
                if agent.id == receiver_id:
                    current_agent = agent
                    break
        
        if not current_agent:
            return {
                "success": False,
                "error": f"未找到ID为{receiver_id}的Agent"
            }
        
        # 从请求中获取任务或创建模拟任务
        if request and "params" in request:
            task = {
                "id": request["params"].get("id", f"task_{receiver_id}_{id(self)}"),
                "sessionId": request["params"].get("sessionId", ""),
                "message": request["params"].get("message", {}),
                "acceptedOutputModes": request["params"].get("acceptedOutputModes", []),
                "historyLength": request["params"].get("historyLength", 5)
            }
        else:
            # 模拟任务
            task = {
                "id": f"task_{receiver_id}_{id(self)}",
                "type": "test_task",
                "data": "测试任务数据"
            }
        
        context = {
            "receiver_id": receiver_id
        }
        
        # 处理任务
        if task_handler:
            # 检查任务处理函数的签名
            import inspect
            sig = inspect.signature(task_handler)
            params = list(sig.parameters.keys())
            
            if len(params) >= 5:
                # 旧式签名: (task_id, session_id, message, agent_card, context)
                result = await task_handler(
                    task.get("id"),
                    task.get("sessionId"),
                    task.get("message"),
                    current_agent,
                    context
                )
            else:
                # 新式签名: (task, context)
                result = await task_handler(task, context)
        else:
            result = {
                "status": {
                    "state": "completed",
                    "message": "任务已接收，但未设置处理函数"
                }
            }
        
        # 构造响应
        response = {
            "jsonrpc": "2.0",
            "id": request.get("id", task.get("id")),
            "result": result
        }
        
        return {
            "success": True,
            "response": response
        }


class DiscoverAgentsNode(Node):
    """
    发现Agent节点
    
    用于发现具有特定技能的Agent。
    """
    
    def __init__(self, name: str = "discover_agents", description: str = "", agent_registry: Optional[AgentRegistry] = None):
        super().__init__(name)
        self.description = description
        self.agent_registry = agent_registry or AgentRegistry()
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行发现Agent
        
        Args:
            inputs: 输入数据，包含:
                   - query: 查询条件
        
        Returns:
            执行结果，包含符合条件的Agent列表
        """
        query = inputs.get("query", "")
        
        # 发现Agent
        if query:
            agents = self.agent_registry.search_agents(query)
        else:
            agents = self.agent_registry.list_agents()
        
        return {
            "success": True,
            "agents": agents
        }


class TaskResultNode(Node):
    """
    任务结果节点
    
    用于处理任务结果。
    """
    
    def __init__(self, name: str = "task_result", description: str = ""):
        super().__init__(name)
        self.description = description
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务结果处理
        
        Args:
            inputs: 输入数据，包含:
                   - task_id: 任务ID
                   - result: 任务结果
        
        Returns:
            执行结果
        """
        task_id = inputs.get("task_id")
        result = inputs.get("result")
        
        if not task_id:
            return {
                "success": False,
                "error": "缺少任务ID"
            }
        
        # 处理任务结果
        # 在实际实现中，这里可以将结果保存到数据库或发送给其他Agent
        
        return {
            "success": True,
            "task_id": task_id,
            "result": result
        }


class TaskRequestNode(Node):
    """
    任务请求节点
    
    用于向多个Agent发送任务请求。
    """
    
    def __init__(self, name: str = "task_request", description: str = "", agent_registry: Optional[AgentRegistry] = None):
        super().__init__(name)
        self.description = description
        self.agent_registry = agent_registry or AgentRegistry()
    
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务请求
        
        Args:
            inputs: 输入数据，包含:
                   - coordinator_id: 协调者ID
                   - task_data: 任务数据
                   - target_agents: 目标Agent ID列表
                   - task_handler: 任务处理函数
        
        Returns:
            执行结果，包含任务请求结果
        """
        coordinator_id = inputs.get("coordinator_id")
        task_data = inputs.get("task_data", {})
        target_agents = inputs.get("target_agents", [])
        task_handler = inputs.get("task_handler")
        
        if not coordinator_id:
            return {
                "success": False,
                "error": "缺少协调者ID"
            }
        
        # 如果没有指定目标Agent，则获取所有Agent
        if not target_agents:
            agents = self.agent_registry.list_agents()
            target_agents = [agent.id for agent in agents if agent.id != coordinator_id]
        
        # 向每个目标Agent发送任务
        results = []
        for agent_id in target_agents:
            send_node = SendTaskNode(
                f"send_task_{agent_id}",
                agent_registry=self.agent_registry
            )
            
            result = await send_node.execute({
                "sender_id": coordinator_id,
                "receiver_id": agent_id,
                "task_data": task_data,
                "task_handler": task_handler
            })
            
            results.append({
                "agent_id": agent_id,
                "result": result
            })
        
        return {
            "success": True,
            "results": results
        }