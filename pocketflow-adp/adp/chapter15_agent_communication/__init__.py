"""
Chapter 15: Agent间通信 (A2A协议) - PocketFlow实现

本模块实现了基于PocketFlow的Agent间通信(A2A)协议，使多个Agent能够相互发现、通信和协作。

主要组件:
1. AgentCard: 描述Agent的能力和通信端点
2. A2A通信节点: 实现发送任务和接收任务的功能
3. Agent注册表: 实现Agent发现机制
4. A2A流程: 封装A2A通信的核心逻辑
5. 示例Agent: 演示A2A协议的使用
"""

from .agent_card import AgentCard, AgentSkill, AgentCapabilities
from .a2a_nodes import SendTaskNode, ReceiveTaskNode, DiscoverAgentsNode
from .a2a_flow import A2AFlow, CollaborationFlow
from .agent_registry import AgentRegistry
from .example_agents import (
    WeatherAgent, 
    NewsAgent, 
    TranslationAgent, 
    CoordinatorAgent,
    demo_a2a_communication
)

__all__ = [
    "AgentCard",
    "AgentSkill",
    "AgentCapabilities",
    "SendTaskNode",
    "ReceiveTaskNode",
    "DiscoverAgentsNode",
    "A2AFlow",
    "CollaborationFlow",
    "AgentRegistry",
    "WeatherAgent",
    "NewsAgent",
    "TranslationAgent",
    "CoordinatorAgent",
    "demo_a2a_communication"
]