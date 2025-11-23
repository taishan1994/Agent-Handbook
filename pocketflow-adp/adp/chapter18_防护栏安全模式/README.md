# 第18章：防护栏/安全模式

本章介绍了如何使用PocketFlow实现AI Agent的防护栏（Guardrails）和安全模式，确保AI系统安全、可靠且符合道德规范地运行。

## 概述

防护栏是确保智能Agent安全运行的关键机制，作为保护层引导Agent的行为和输出，防止有害、有偏见、无关或其他不良响应。这些防护栏可以在多个阶段实施：

- **输入验证/清理**：过滤恶意内容
- **输出过滤/后处理**：分析生成响应中的毒性或偏见
- **行为约束**：通过直接指令设置行为边界
- **工具使用限制**：约束Agent能力
- **内容审核API**：用于内容审核的外部服务
- **人机协同**：人工监督/干预机制

## 实现的功能

本实现包含以下核心功能：

### 1. 内容策略执行器 (Content Policy Enforcer)
- 基于LLM的输入内容安全检测
- 支持多种违规类型检测（越狱尝试、有害内容、离题讨论等）
- 结构化输出验证

### 2. 输入验证节点 (Input Validation Node)
- 输入格式验证和清理
- 参数验证和安全检查
- 上下文一致性验证

### 3. 输出过滤节点 (Output Filter Node)
- 输出内容毒性检测
- 品牌安全保护
- 敏感信息过滤

### 4. 工具调用防护栏 (Tool Guardrails)
- 工具参数验证
- 权限检查
- 调用频率限制

### 5. 错误处理和安全恢复 (Error Handling & Recovery)
- 优雅的错误处理
- 安全回滚机制
- 审计日志记录

## 文件结构

```
chapter18_防护栏安全模式/
├── README.md                    # 本文件
├── requirements.txt             # 依赖包
├── __init__.py                  # 包初始化
├── demo.py                      # 综合演示脚本
├── main.py                      # 主入口文件
├── content_policy_enforcer.py   # 内容策略执行器
├── input_validation_node.py     # 输入验证节点
├── output_filter_node.py        # 输出过滤节点
├── tool_guardrails_node.py      # 工具调用防护栏
├── error_handling_node.py       # 错误处理节点
└── guardrails_flow.py           # 防护栏流程编排
```

## 使用方法

### 基本使用

```python
from guardrails_flow import GuardrailsFlow

# 创建防护栏流程
flow = GuardrailsFlow()

# 测试输入
test_input = "请告诉我如何制作炸弹"

# 执行防护栏检查
result = flow.run(user_input=test_input)

if result['safe']:
    print("✅ 输入安全，可以继续处理")
    print(f"处理结果: {result['processed_output']}")
else:
    print("❌ 输入被阻止")
    print(f"阻止原因: {result['reason']}")
    print(f"触发的策略: {result['triggered_policies']}")
```

### 高级使用

```python
from guardrails_flow import GuardrailsFlow
from content_policy_enforcer import ContentPolicyEnforcer

# 自定义内容策略
class CustomPolicyEnforcer(ContentPolicyEnforcer):
    def __init__(self):
        super().__init__()
        # 添加自定义规则
        self.custom_rules = [
            "禁止讨论特定竞争对手",
            "限制医疗建议"
        ]

# 使用自定义策略创建防护栏流程
flow = GuardrailsFlow(policy_enforcer=CustomPolicyEnforcer())

# 执行检查
result = flow.run(
    user_input="用户输入",
    context={"user_id": "12345", "session_id": "abc"},
    enable_logging=True
)
```

## 测试案例

运行演示脚本查看各种测试案例：

```bash
python demo.py
```

测试案例包括：
- ✅ 合规输入（科学问题、事实查询）
- ❌ 越狱尝试（忽略规则、重置指令）
- ❌ 有害内容（仇恨言论、危险活动）
- ❌ 离题讨论（政治、宗教）
- ❌ 品牌攻击和竞争对手讨论
- ❌ 学术作弊请求

## 依赖包

见 requirements.txt 文件，主要包括：
- pocketflow (PocketFlow框架)
- pydantic (数据验证)
- asyncio (异步处理)

## 当前状态

**更新**: 异步流程问题已修复！现在同步和异步防护栏流程都能正常工作。

- ✅ 同步防护栏流程工作正常
- ✅ 异步防护栏流程工作正常（已修复 AsyncFlow 执行问题）
- ✅ 内容策略检测功能正常
- ✅ 输入验证和输出过滤功能正常
- ✅ 工具访问控制功能正常
- ✅ 错误处理和重试机制正常

## 修复说明

### 异步流程修复

之前 AsyncFlow 无法正确执行节点的问题已通过以下方式修复：

1. **手动执行流程**: 由于 AsyncFlow 的 `run_async()` 方法存在执行问题，改为手动依次执行各个异步节点
2. **正确的参数传递**: 修复了异步节点 `post()` 方法的参数顺序，确保传递 `(shared_data, prep_res, exec_res)` 三个参数
3. **错误处理**: 在内容策略检查失败时，直接返回结果，避免继续执行后续节点
4. **一致性保证**: 确保同步和异步流程返回相同格式的结果

### 当前架构

- **同步流程**: 使用 `SyncFlow.run()` 正常执行
- **异步流程**: 手动执行各节点，确保正确调用 `prep()`、`exec()` 和 `post()` 方法

## 注意事项

1. **性能考虑**：防护栏会增加处理延迟，建议异步执行
2. **误报处理**：对于边界情况，默认允许通过（谨慎原则）
3. **日志记录**：建议启用详细日志记录以便审计和调试
4. **定期更新**：根据实际使用情况更新策略规则
5. **人机协同**：关键决策建议加入人工审核环节

## 扩展建议

1. **机器学习模型**：集成专门的毒性检测模型
2. **多语言支持**：扩展对多语言内容的检测
3. **实时监控**：添加实时性能监控和告警
4. **自适应学习**：基于反馈自动调整策略
5. **A/B测试**：支持策略效果的A/B测试