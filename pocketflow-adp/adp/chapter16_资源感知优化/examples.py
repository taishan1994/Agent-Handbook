"""
资源感知优化示例 - 综合演示

该文件演示了如何结合使用资源感知优化系统的各个组件，
包括任务分类、动态模型选择和资源监控。
"""

import sys
import os
import asyncio
import time

# 添加utils目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from utils import call_llm, search_web_exa
from .resource_aware_optimization import create_resource_aware_flow
from .dynamic_model_selector import create_dynamic_model_selection_flow, ModelTier
from .resource_monitor import create_resource_monitoring_flow


async def demo_resource_aware_optimization():
    """演示资源感知优化流程"""
    print("=" * 60)
    print("资源感知优化流程演示")
    print("=" * 60)
    
    # 创建流程
    flow = create_resource_aware_flow()
    
    # 测试查询
    test_queries = [
        "法国的首都是哪里？",  # simple
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？",  # reasoning
        "2024年诺贝尔物理学奖获得者是谁？"  # internet_search
    ]
    
    # 处理每个查询
    for query in test_queries:
        print(f"\n处理查询: {query}")
        print("-" * 50)
        
        # 运行流程
        shared_state = {"query": query}
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"分类: {result['classification']}")
        print(f"使用模型: {result['model_used']}")
        print(f"处理时间: {result['processing_time']:.2f}秒")
        print(f"回答: {result['response'][:200]}...")
    
    print("\n资源感知优化流程演示完成\n")


async def demo_dynamic_model_selection():
    """演示动态模型选择流程"""
    print("=" * 60)
    print("动态模型选择流程演示")
    print("=" * 60)
    
    # 创建流程
    flow = create_dynamic_model_selection_flow()
    
    # 测试查询
    test_queries = [
        "法国的首都是哪里？",  # simple
        "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？",  # reasoning
        "请分析一下人工智能在医疗领域的应用前景和挑战",  # analysis
        "请写一个Python函数，实现快速排序算法",  # code
    ]
    
    # 处理每个查询
    for query in test_queries:
        print(f"\n处理查询: {query}")
        print("-" * 50)
        
        # 运行流程
        shared_state = {"query": query}
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"复杂度: {result['complexity']}")
        print(f"选择模型: {result['model_name']}")
        print(f"模型层级: {result['model_config'].get('tier', '')}")
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"估算成本: ${result['estimated_cost']:.6f}")
        print(f"回答: {result['response'][:200]}...")
    
    print("\n动态模型选择流程演示完成\n")


async def demo_resource_monitoring():
    """演示资源监控流程"""
    print("=" * 60)
    print("资源监控流程演示")
    print("=" * 60)
    
    # 创建流程和监控器
    flow, monitor = create_resource_monitoring_flow()
    
    # 测试查询
    test_queries = [
        {"query": "法国的首都是哪里？", "query_type": "simple"},
        {"query": "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？", "query_type": "reasoning"},
        {"query": "请分析一下人工智能在医疗领域的应用前景和挑战", "query_type": "analysis"},
        {"query": "请写一个Python函数，实现快速排序算法", "query_type": "code"}
    ]
    
    # 处理每个查询
    for query_data in test_queries:
        print(f"\n处理查询: {query_data['query']}")
        print("-" * 50)
        
        # 运行流程
        shared_state = query_data
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"使用模型: {result['model_name']}")
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"输入/输出Token: {result['input_tokens']}/{result['output_tokens']}")
        print(f"成功: {result['success']}")
        print(f"回答: {result['response'][:100]}...")
    
    # 生成资源使用报告
    print("\n" + "=" * 50)
    print("资源使用报告")
    print("=" * 50)
    
    shared_state = {"action": "generate_report", "report_days": 7}
    report_result = await flow.run_async(shared_state)
    
    report = report_result["resource_report"]
    metrics = report.get("metrics", {})
    
    # 调试信息
    print(f"报告内容: {report}")
    
    # 检查metrics是否为空
    if not metrics:
        print("警告: 无法获取资源使用指标，可能是没有查询记录或报告生成失败")
        return
    
    print(f"查询总数: {metrics['query_count']}")
    print(f"总成本: ${metrics['total_cost']:.4f}")
    print(f"总Token数: {metrics['total_tokens']}")
    print(f"平均响应时间: {metrics['avg_response_time']:.2f}秒")
    print(f"成功率: {metrics['success_rate']:.2%}")
    print(f"模型使用分布: {metrics['model_usage']}")
    print(f"查询类型分布: {metrics['query_type_distribution']}")
    
    print("\n优化建议:")
    for i, suggestion in enumerate(report["optimization_suggestions"], 1):
        print(f"{i}. {suggestion}")
    
    print("\n资源监控流程演示完成\n")


async def demo_cost_optimization():
    """演示成本优化场景"""
    print("=" * 60)
    print("成本优化场景演示")
    print("=" * 60)
    
    # 创建流程
    flow = create_dynamic_model_selection_flow()
    
    # 测试查询
    test_queries = [
        {"query": "法国的首都是哪里？", "cost_constraint": 0.001},  # 限制成本
        {"query": "如果一个房间里有3只猫，每只猫抓了2只老鼠，那么总共有多少只老鼠被抓？", "cost_constraint": 0.005},
        {"query": "请分析一下人工智能在医疗领域的应用前景和挑战", "tier_constraint": ModelTier.STANDARD.value},  # 限制层级
        {"query": "请写一个Python函数，实现快速排序算法", "tier_constraint": ModelTier.BASIC.value}  # 限制为基础模型
    ]
    
    # 处理每个查询
    for query_data in test_queries:
        query = query_data["query"]
        constraints = {k: v for k, v in query_data.items() if k != "query"}
        
        print(f"\n处理查询: {query}")
        print(f"约束条件: {constraints}")
        print("-" * 50)
        
        # 运行流程
        shared_state = query_data
        result = await flow.run_async(shared_state)
        
        # 显示结果
        print(f"复杂度: {result['complexity']}")
        print(f"选择模型: {result['model_name']}")
        print(f"模型层级: {result['model_config'].get('tier', '')}")
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"估算成本: ${result['estimated_cost']:.6f}")
        print(f"回答: {result['response'][:200]}...")
    
    print("\n成本优化场景演示完成\n")


async def demo_performance_comparison():
    """演示不同模型的性能比较"""
    print("=" * 60)
    print("模型性能比较演示")
    print("=" * 60)
    
    # 创建不同模型的监控流程
    models_to_test = ["gpt-4o-mini", "gpt-4o"]
    
    # 测试查询
    test_query = "请解释什么是机器学习，并提供一个简单的例子"
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n测试模型: {model_name}")
        print("-" * 50)
        
        # 创建流程
        flow, _ = create_resource_monitoring_flow(model_name)
        
        # 运行流程
        shared_state = {"query": test_query, "query_type": "reasoning"}
        result = await flow.run_async(shared_state)
        
        # 存储结果
        results[model_name] = result
        
        # 显示结果
        print(f"响应时间: {result['response_time']:.2f}秒")
        print(f"输入/输出Token: {result['input_tokens']}/{result['output_tokens']}")
        print(f"成功: {result['success']}")
        print(f"回答: {result['response'][:300]}...")
    
    # 比较结果
    print("\n" + "=" * 50)
    print("模型比较结果")
    print("=" * 50)
    
    for model_name, result in results.items():
        print(f"\n{model_name}:")
        print(f"  响应时间: {result['response_time']:.2f}秒")
        print(f"  输入/输出Token: {result['input_tokens']}/{result['output_tokens']}")
        print(f"  成功: {result['success']}")
        
        # 估算成本
        if model_name == "gpt-4o-mini":
            cost_per_1k = 0.00015
        elif model_name == "gpt-4o":
            cost_per_1k = 0.0025
        else:
            cost_per_1k = 0.0025
            
        total_tokens = result['input_tokens'] + result['output_tokens']
        estimated_cost = (total_tokens / 1000) * cost_per_1k
        print(f"  估算成本: ${estimated_cost:.6f}")
    
    print("\n模型性能比较演示完成\n")


async def main():
    """主函数：运行所有演示"""
    print("开始资源感知优化系统演示")
    print("=" * 60)
    
    # 运行各个演示
    await demo_resource_aware_optimization()
    await demo_dynamic_model_selection()
    await demo_resource_monitoring()
    await demo_cost_optimization()
    await demo_performance_comparison()
    
    print("所有演示完成！")


if __name__ == "__main__":
    asyncio.run(main())