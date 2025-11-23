"""
Chapter 17: 推理技术实现

本章实现了多种高级推理技术，基于PocketFlow框架构建，并集成了utils中的LLM调用和搜索功能。

实现的推理技术包括：
1. 思维链(Chain of Thought, CoT) - 引导模型逐步思考问题
2. 思维树(Tree of Thoughts, ToT) - 探索多个推理路径并评估最佳路径
3. 自我纠正(Self-Correction) - 检测并修正推理过程中的错误
4. ReAct(Reasoning and Acting) - 结合推理和行动的循环过程
5. 辩论链(Chain of Debate, CoD) - 通过多轮辩论提高推理质量
6. Deep Research - 结合多种推理技术的深度研究系统

所有实现都基于PocketFlow框架，并使用utils中的call_llm和search_web_exa函数。
"""

__version__ = "1.0.0"

# 导入所有推理技术模块
from .chain_of_thought import (
    ChainOfThoughtNode,
    FewShotCoTNode,
    create_cot_workflow,
    demo_chain_of_thought
)

# 注意：思维树(ToT)推理技术已从演示中移除

from .self_correction import (
    SelfCorrectionNode,
    ReflexionNode,
    create_self_correction_workflow,
    demo_self_correction
)

from .react import (
    ReActNode,
    ReActWithToolsNode,
    create_react_workflow,
    demo_react
)

from .chain_of_debate import (
    DebateAgent,
    ChainOfDebateNode,
    GraphOfDebateNode,
    create_cod_workflow,
    demo_cod
)

from .deep_research import (
    ResearchPlannerNode,
    ResearchExecutorNode,
    ResearchSynthesizerNode,
    create_deep_research_workflow,
    demo_deep_research
)

# 导入综合演示
from .demo import (
    compare_reasoning_techniques,
    demonstrate_technique_specialties,
    interactive_demo,
    main
)

# 导出所有类和函数
__all__ = [
    # 思维链
    "ChainOfThoughtNode",
    "FewShotCoTNode",
    "create_cot_workflow",
    "demo_chain_of_thought",
    
    # 注意：思维树(ToT)推理技术已从演示中移除
    
    # 自我纠正
    "SelfCorrectionNode",
    "ReflexionNode",
    "create_self_correction_workflow",
    "demo_self_correction",
    
    # ReAct
    "ReActNode",
    "ReActWithToolsNode",
    "create_react_workflow",
    "demo_react",
    
    # 辩论链
    "DebateAgent",
    "ChainOfDebateNode",
    "GraphOfDebateNode",
    "create_cod_workflow",
    "demo_cod",
    
    # Deep Research
    "ResearchPlannerNode",
    "ResearchExecutorNode",
    "ResearchSynthesizerNode",
    "create_deep_research_workflow",
    "demo_deep_research",
    
    # 综合演示
    "compare_reasoning_techniques",
    "demonstrate_technique_specialties",
    "interactive_demo",
    "main"
]