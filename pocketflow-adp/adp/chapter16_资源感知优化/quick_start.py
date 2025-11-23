#!/usr/bin/env python3
"""
资源感知优化系统 - 快速开始示例

这个示例展示了如何使用资源感知优化系统来处理不同类型的查询，
并根据查询复杂度自动选择合适的模型和处理策略。
"""

import asyncio
from resource_aware_optimization import create_resource_aware_flow
from beautiful_demo import IntegratedResourceAwareFlow, format_report


async def basic_usage_example():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 创建资源感知优化流程
    flow = create_resource_aware_flow()
    
    # 处理不同类型的查询
    queries = [
        "法国的首都是哪里？",
        "请解释量子计算的基本原理",
        "分析人工智能在医疗领域的应用前景"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- 查询 {i}: {query} ---")
        shared_state = {"query": query}
        result = await flow.run_async(shared_state)
        
        print(f"分类: {result['classification']}")
        print(f"使用模型: {result['model_used']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['response'][:100]}...")


async def monitored_usage_example():
    """带监控的使用示例"""
    print("\n\n=== 带监控的使用示例 ===")
    
    # 创建集成流程
    flow = IntegratedResourceAwareFlow()
    monitor = flow.get_monitor()
    
    # 处理多个查询
    queries = [
        "2+2等于多少？",
        "请解释机器学习中的过拟合问题",
        "编写一个Python函数实现二分查找",
        "分析全球气候变化对农业的影响"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- 测试查询 {i}: {query} ---")
        shared_state = {"query": query}
        result = flow.run(shared_state)
        
        print(f"分类: {result['classification']}")
        print(f"使用模型: {result['model_used']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['response'][:100]}...")
    
    # 生成资源使用报告
    print("\n--- 资源使用报告 ---")
    report_data = monitor.get_usage_report()
    formatted_report = format_report(report_data)
    print(formatted_report)


async def main():
    """主函数"""
    print("资源感知优化系统 - 快速开始示例\n")
    
    # 基本使用示例
    await basic_usage_example()
    
    # 带监控的使用示例
    await monitored_usage_example()
    
    print("\n示例运行完成！")
    print("\n要了解更多信息，请参考 README.md 文档。")


if __name__ == "__main__":
    asyncio.run(main())