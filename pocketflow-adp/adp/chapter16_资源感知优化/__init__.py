"""
资源感知优化 - 基于PocketFlow的实现

该包实现了一个资源感知优化系统，能够根据任务复杂性和资源约束
动态选择合适的模型和策略，以在成本、性能和质量之间取得平衡。
"""

from .resource_aware_optimization import (
    TaskClassifierNode,
    SimpleQueryNode,
    ReasoningQueryNode,
    InternetSearchNode,
    ResourceAwareOptimizationFlow,
    create_resource_aware_flow
)

from .dynamic_model_selector import (
    ModelTier,
    ModelConfig,
    ModelSelector,
    TaskComplexityClassifier,
    ModelSelectionNode,
    QueryProcessingNode,
    DynamicModelSelectionFlow,
    create_dynamic_model_selection_flow
)

from .resource_monitor import (
    ResourceUsage,
    ResourceMetrics,
    ResourceMonitor,
    ResourceAwareQueryNode,
    ResourceReportNode,
    ResourceMonitoringFlow,
    create_resource_monitoring_flow
)

__all__ = [
    # 资源感知优化
    "TaskClassifierNode",
    "SimpleQueryNode",
    "ReasoningQueryNode",
    "InternetSearchNode",
    "ResourceAwareOptimizationFlow",
    "create_resource_aware_flow",
    
    # 动态模型选择
    "ModelTier",
    "ModelConfig",
    "ModelSelector",
    "TaskComplexityClassifier",
    "ModelSelectionNode",
    "QueryProcessingNode",
    "DynamicModelSelectionFlow",
    "create_dynamic_model_selection_flow",
    
    # 资源监控
    "ResourceUsage",
    "ResourceMetrics",
    "ResourceMonitor",
    "ResourceAwareQueryNode",
    "ResourceReportNode",
    "ResourceMonitoringFlow",
    "create_resource_monitoring_flow"
]

__version__ = "1.0.0"