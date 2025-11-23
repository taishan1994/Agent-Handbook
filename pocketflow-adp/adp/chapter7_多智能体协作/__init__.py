"""
Chapter 7: 多智能体协作模式
"""

from .researcher_node import ResearcherNode, WebResearcherNode
from .writer_node import WriterNode, ReviewerNode, FinalizerNode
from .coordinator_node import CoordinatorNode, TaskAssignerNode, ResultIntegratorNode
from .multi_agent_flow import (
    SequentialMultiAgentFlow,
    ParallelMultiAgentFlow,
    HierarchicalMultiAgentFlow,
    CollaborativeDecisionFlow
)

__all__ = [
    # 节点类
    "ResearcherNode",
    "WebResearcherNode",
    "WriterNode",
    "ReviewerNode",
    "FinalizerNode",
    "CoordinatorNode",
    "TaskAssignerNode",
    "ResultIntegratorNode",
    
    # 流程类
    "SequentialMultiAgentFlow",
    "ParallelMultiAgentFlow",
    "HierarchicalMultiAgentFlow",
    "CollaborativeDecisionFlow"
]