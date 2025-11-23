# 资源感知优化系统

本章节实现了一个基于PocketFlow的资源感知优化系统，能够根据任务复杂性和资源约束动态选择合适的模型和策略，以在成本、性能和质量之间取得平衡。

## 系统组件

### 1. 资源感知优化 (resource_aware_optimization.py)

实现了以下核心组件：

- **TaskClassifierNode**: 任务分类节点，将查询分类为simple、reasoning或internet_search
- **SimpleQueryNode**: 简单查询节点，使用轻量级模型处理简单查询
- **ReasoningQueryNode**: 推理查询节点，使用更强大的模型处理复杂推理任务
- **InternetSearchNode**: 网络搜索节点，模拟搜索相关信息并生成回答
- **ResourceAwareOptimizationFlow**: 资源感知优化流程，根据任务分类动态选择处理策略

### 2. 资源监控 (resource_monitor.py)

实现了以下核心组件：

- **ResourceMonitor**: 资源监控器，记录和跟踪API使用情况
- **ResourceAwareQueryNode**: 带资源监控的查询节点
- **ResourceReportNode**: 资源报告节点，生成资源使用报告
- **ResourceMonitoringFlow**: 资源监控流程，整合资源监控功能

### 3. 集成演示 (beautiful_demo.py)

展示了如何结合资源感知优化系统和资源监控器，实现智能的资源管理和优化，并提供美观的资源使用报告。

## 系统特点

1. **智能分类**: 根据查询内容自动分类为不同复杂度的任务
2. **资源优化**: 根据任务类型选择合适的模型，平衡成本和质量
3. **实时监控**: 记录每次API调用的资源使用情况
4. **详细报告**: 生成包含成本、Token使用、响应时间等详细统计的报告
5. **可视化展示**: 提供美观的资源使用报告界面

## 使用方法

### 基本使用

```python
from resource_aware_optimization import create_resource_aware_flow

# 创建资源感知优化流程
flow = create_resource_aware_flow()

# 处理查询
shared_state = {"query": "法国的首都是哪里？"}
result = await flow.run_async(shared_state)

print(f"分类: {result['classification']}")
print(f"使用模型: {result['model_used']}")
print(f"回答: {result['response']}")
```

### 带监控的使用

```python
from beautiful_demo import IntegratedResourceAwareFlow

# 创建集成流程
flow = IntegratedResourceAwareFlow()
monitor = flow.get_monitor()

# 处理多个查询
queries = ["简单问题", "复杂推理问题", ...]
for query in queries:
    shared_state = {"query": query}
    result = flow.run(shared_state)
    print(f"回答: {result['response']}")

# 生成资源使用报告
report_data = monitor.get_usage_report()
formatted_report = format_report(report_data)
print(formatted_report)
```

## 资源监控指标

系统监控以下资源使用指标：

- **总成本**: API调用的总费用
- **Token使用量**: 输入和输出Token的总数
- **响应时间**: 每次查询的响应时间
- **成功率**: 查询成功的百分比
- **模型使用分布**: 不同模型的使用次数
- **查询类型分布**: 不同类型查询的数量

## 优化建议

系统会根据资源使用情况提供优化建议，例如：

- 平均响应时间较长时，建议优化查询或使用更快的模型
- 某些模型使用频率过高时，建议调整模型选择策略
- 成本过高时，建议使用更经济的模型组合

## 扩展性

系统设计具有良好的扩展性，可以轻松添加：

- 新的任务分类类型
- 新的模型选择策略
- 更复杂的资源优化算法
- 自定义资源监控指标
- 集成外部资源监控服务

## 示例输出

```
--- 测试查询 1: 法国的首都是哪里？ ---
分类: simple
使用模型: gpt-4o-mini
处理时间: 2.34秒
回答: 法国的首都是巴黎...

--- 资源使用报告 ---

╔══════════════════════════════════════════════════════════════╗
║                    资源使用报告                              ║
╚══════════════════════════════════════════════════════════════╝

📊 总体统计:
  • 总成本: $0.016294
  • 总Token数: 7966
  • 平均响应时间: 4.08秒
  • 成功率: 100.00%
  • 查询次数: 94

🤖 按模型统计:
  • gpt-4o: 62次查询
  • gpt-4o-mini: 32次查询

📋 按查询类型统计:
  • simple: 18次查询
  • reasoning: 27次查询
  • classification: 20次查询
  • ...
```

## 总结

资源感知优化系统通过智能任务分类和动态模型选择，实现了在成本、性能和质量之间的平衡。结合实时资源监控和详细报告，用户可以全面了解系统资源使用情况，并根据系统提供的优化建议持续改进性能。