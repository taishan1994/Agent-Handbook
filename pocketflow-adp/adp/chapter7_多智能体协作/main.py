"""
Chapter 7: 多智能体协作模式 - 主程序入口
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from multi_agent_flow import (
    SequentialMultiAgentFlow,
    ParallelMultiAgentFlow,
    HierarchicalMultiAgentFlow,
    CollaborativeDecisionFlow
)


def sequential_collaboration_example():
    """顺序协作示例"""
    print("=" * 60)
    print("顺序多智能体协作示例")
    print("=" * 60)
    
    # 创建顺序协作流程
    flow = SequentialMultiAgentFlow()
    
    # 设置研究主题
    research_topic = "2024-2025年人工智能的最新发展趋势"
    
    print(f"研究主题: {research_topic}")
    print("\n正在执行顺序多智能体协作流程...")
    
    # 运行流程
    result = flow.run(
        research_topic=research_topic,
        target_audience="技术爱好者",
        content_type="技术博客",
        word_count="800"
    )
    
    print("\n顺序协作结果:")
    print(result)
    print("\n" + "=" * 60)


async def parallel_collaboration_example():
    """并行协作示例"""
    print("=" * 60)
    print("并行多智能体协作示例")
    print("=" * 60)
    
    # 创建并行协作流程
    flow = ParallelMultiAgentFlow()
    
    # 设置研究主题
    research_topic = "量子计算在网络安全领域的应用前景"
    
    print(f"研究主题: {research_topic}")
    print("\n正在执行并行多智能体协作流程...")
    
    # 运行流程
    result = await flow.run(
        research_topic=research_topic,
        target_audience="技术决策者",
        content_type="研究报告"
    )
    
    print("\n并行协作结果:")
    print(result)
    print("\n" + "=" * 60)


def hierarchical_collaboration_example():
    """层级协作示例"""
    print("=" * 60)
    print("层级多智能体协作示例")
    print("=" * 60)
    
    # 创建层级协作流程
    flow = HierarchicalMultiAgentFlow()
    
    # 设置用户请求
    user_request = "请帮我创建一个关于边缘计算在物联网中应用的全面分析报告，包括技术原理、应用场景、挑战和未来趋势"
    
    print(f"用户请求: {user_request}")
    print("\n正在执行层级多智能体协作流程...")
    
    # 运行流程
    result = flow.run(user_request=user_request)
    
    print("\n层级协作结果:")
    print(result)
    print("\n" + "=" * 60)


def collaborative_decision_example():
    """协作决策示例"""
    print("=" * 60)
    print("协作决策多智能体示例")
    print("=" * 60)
    
    # 创建协作决策流程
    flow = CollaborativeDecisionFlow()
    
    # 设置研究主题
    research_topic = "人工智能伦理问题及其解决方案"
    
    print(f"研究主题: {research_topic}")
    print("\n正在执行协作决策多智能体流程...")
    
    # 运行流程
    result = flow.run(
        research_topic=research_topic,
        target_audience="政策制定者",
        content_type="政策建议报告"
    )
    
    print("\n协作决策结果:")
    print(result)
    print("\n" + "=" * 60)


async def main():
    """主函数"""
    print("Chapter 7: 多智能体协作模式示例")
    print("本示例展示了使用PocketFlow实现的四种多智能体协作模式:")
    print("1. 顺序协作 - 智能体按顺序执行任务")
    print("2. 并行协作 - 多个智能体同时执行任务")
    print("3. 层级协作 - 主智能体协调和管理多个子智能体")
    print("4. 协作决策 - 多个智能体共同参与决策过程")
    print("\n")
    
    # 运行所有示例
    sequential_collaboration_example()
    await parallel_collaboration_example()
    hierarchical_collaboration_example()
    collaborative_decision_example()
    
    print("\n所有多智能体协作模式示例执行完成!")


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())