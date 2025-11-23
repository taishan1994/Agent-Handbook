import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.abspath('.'))

from adp.chapter16_资源感知优化.resource_monitor import ResourceMonitor, ResourceMonitoringFlow

def demo_resource_monitor():
    """演示资源监控功能"""
    print("=== 资源感知优化系统演示 ===\n")
    
    # 创建资源监控器
    monitor = ResourceMonitor()
    
    # 创建资源监控流程
    flow = ResourceMonitoringFlow(monitor)
    
    # 测试查询列表
    test_queries = [
        {"query": "法国的首都是哪里？", "type": "simple"},
        {"query": "请解释量子纠缠的基本原理", "type": "reasoning"},
        {"query": "分析人工智能在医疗领域的应用前景，包括技术挑战和伦理考虑", "type": "complex_reasoning"},
        {"query": "编写一个Python函数实现快速排序算法", "type": "code"}
    ]
    
    # 处理每个查询
    for i, test_case in enumerate(test_queries, 1):
        print(f"--- 测试查询 {i}: {test_case['query']} ---")
        
        # 准备共享状态
        shared_state = {
            "query": test_case["query"],
            "query_type": test_case["type"]
        }
        
        # 运行流程
        result = flow.run(shared_state)
        
        # 显示结果
        print(f"模型: {result.get('model_name', 'N/A')}")
        print(f"响应时间: {result.get('response_time', 0):.2f}秒")
        print(f"输入Token: {result.get('input_tokens', 0)}")
        print(f"输出Token: {result.get('output_tokens', 0)}")
        print(f"成功: {result.get('success', False)}")
        print(f"总处理时间: {result.get('total_time', 0):.2f}秒")
        print(f"响应: {result.get('response', 'N/A')[:100]}...")
        print()
    
    # 生成资源使用报告
    print("--- 资源使用报告 ---")
    shared_state = {
        "action": "generate_report",
        "report_days": 7
    }
    
    report_result = flow.run(shared_state)
    report = report_result.get("resource_report", {})
    
    print(f"总成本: ${report.get('total_cost', 0):.6f}")
    print(f"总Token数: {report.get('total_tokens', 0)}")
    print(f"平均响应时间: {report.get('avg_response_time', 0):.2f}秒")
    print(f"成功率: {report.get('success_rate', 0):.2f}%")
    print(f"查询次数: {report.get('query_count', 0)}")
    
    # 按模型统计
    model_stats = report.get('model_stats', {})
    if model_stats:
        print("\n按模型统计:")
        for model, stats in model_stats.items():
            print(f"  {model}: {stats['count']}次查询, "
                  f"平均响应时间 {stats['avg_response_time']:.2f}秒, "
                  f"成功率 {stats['success_rate']:.2f}%")
    
    # 按查询类型统计
    type_stats = report.get('type_stats', {})
    if type_stats:
        print("\n按查询类型统计:")
        for qtype, stats in type_stats.items():
            print(f"  {qtype}: {stats['count']}次查询, "
                  f"平均响应时间 {stats['avg_response_time']:.2f}秒, "
                  f"成功率 {stats['success_rate']:.2f}%")
    
    print("\n=== 所有演示完成！ ===")

if __name__ == "__main__":
    demo_resource_monitor()