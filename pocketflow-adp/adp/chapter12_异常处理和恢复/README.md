# Chapter 12: 异常处理和恢复模式 - PocketFlow实现

本目录包含了使用PocketFlow框架实现的异常处理和恢复模式，基于《Agent Design Patterns》第12章的内容。

## 概述

异常处理和恢复模式是一种设计模式，用于构建能够优雅处理错误并从失败中恢复的智能系统。该模式包含三个主要组件：

1. **PrimaryHandler（主要处理器）**：执行核心任务，可能失败
2. **FallbackHandler（回退处理器）**：处理异常并尝试恢复
3. **ResponseAgent（响应代理）**：生成最终响应

## 文件结构

```
chapter12_异常处理和恢复/
├── nodes.py          # 节点实现
├── flow.py           # 流程定义
├── main.py           # 示例和测试代码
└── README.md         # 本文件
```

## 实现说明

### 节点实现

#### PrimaryHandler

主要处理节点，负责执行核心任务。为了演示异常处理，该节点会以一定概率（默认30%）模拟不同类型的错误：

- 网络超时 (network_timeout)
- API错误 (api_error)
- 数据损坏 (data_corruption)
- 资源耗尽 (resource_exhausted)

当处理成功时，它会使用搜索功能和LLM生成回答。

#### FallbackHandler

回退处理节点，负责处理异常并尝试恢复。它根据不同的错误类型采用不同的恢复策略：

- 网络超时：增加超时时间
- API错误：使用备用API
- 数据损坏：清理损坏数据
- 资源耗尽：释放资源
- 处理异常：使用简化处理流程

该节点有最大重试次数限制（默认3次），超过限制后将放弃恢复。

#### ResponseAgent

响应代理节点，负责生成最终响应。它会根据处理结果生成成功或错误响应，并包含处理历史信息（如重试次数和使用的恢复策略）。

### 流程定义

流程定义在`flow.py`中，使用PocketFlow的Flow类连接各个节点：

```
PrimaryHandler --[失败]--> FallbackHandler --[恢复成功]--> PrimaryHandler
                 |                                  |
                 |                                  |
                 +------[成功]----------------------> ResponseAgent
                                                    |
                                                    +----[结束]----> End
```

## 使用方法

### 基本使用

```python
from flow import run_exception_handling_example

# 运行示例
result = run_exception_handling_example("刘翔获得了多少次世界冠军？")
```

### 自定义使用

```python
from flow import create_exception_handling_flow
from nodes import PrimaryHandler, FallbackHandler

# 创建自定义节点
primary = PrimaryHandler(failure_rate=0.2)  # 设置20%失败率
fallback = FallbackHandler(max_retries=5)    # 设置最大重试5次

# 创建流程
flow = create_exception_handling_flow()

# 准备数据
shared_data = {
    "question": "你的问题",
    "context": "上下文信息",
    "retry_count": 0
}

# 执行流程
result = flow.run(shared_data)
```

## 运行测试

运行所有测试：

```bash
python main.py
```

这将运行以下测试：

1. 基本问题处理
2. 复杂问题处理
3. 带上下文的问题处理
4. 多次运行测试（观察异常处理和恢复情况）

测试完成后，可以选择进行交互式测试，输入自己的问题。

## 依赖项

本实现依赖于以下组件：

1. PocketFlow框架 - 用于流程编排
2. utils.call_llm - LLM调用功能
3. exa_search_main - 网络搜索功能

## 特点

1. **模块化设计**：每个组件都有明确的职责，易于理解和修改
2. **灵活的错误处理**：支持多种错误类型和恢复策略
3. **可配置参数**：可以调整失败率和最大重试次数
4. **详细的日志**：提供详细的处理过程日志，便于调试
5. **完整的测试**：包含多种测试场景，验证实现的正确性

## 扩展

可以通过以下方式扩展此实现：

1. 添加更多错误类型和恢复策略
2. 实现更智能的恢复策略选择
3. 添加处理时间限制
4. 实现错误统计和学习功能
5. 添加更复杂的上下文管理

## 示例输出

```
🚀 开始执行异常处理和恢复流程
问题: 刘翔获得了多少次世界冠军？
==================================================
🔧 PrimaryHandler: 开始处理问题 (重试次数: 0)
问题: 刘翔获得了多少次世界冠军？
❌ PrimaryHandler: 处理失败 - 模拟错误: network_timeout
⚠️ PrimaryHandler: 处理失败，转到回退处理器 (错误类型: network_timeout)
🛠️ FallbackHandler: 开始处理错误 (重试次数: 1/3)
错误类型: network_timeout
错误信息: 模拟错误: network_timeout
🔧 FallbackHandler: 尝试恢复策略 - 增加超时时间
✅ FallbackHandler: 恢复成功
🔄 FallbackHandler: 恢复成功，重新尝试主要处理
🔧 PrimaryHandler: 开始处理问题 (重试次数: 1)
问题: 刘翔获得了多少次世界冠军？
🔍 PrimaryHandler: 开始搜索相关信息...
✅ PrimaryHandler: 处理成功
✅ PrimaryHandler: 流程完成，转到响应代理
📝 ResponseAgent: 生成最终响应
✅ ResponseAgent: 成功生成最终响应
==================================================
🏁 流程执行完成
处理成功: 是
重试次数: 1

📋 最终响应:
[LLM生成的回答...]

处理信息: 此回答经过了 1 次重试，最后使用了 '增加超时时间' 恢复策略
```