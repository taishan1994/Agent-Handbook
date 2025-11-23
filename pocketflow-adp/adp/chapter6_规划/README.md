# 规划模式实现说明

本项目使用 PocketFlow 框架实现了规划模式（Planning Pattern），这是一种将复杂任务分解为多个步骤并按顺序执行的设计模式。

## 文件结构

```
chapter6/
├── planner_node.py              # 规划节点类
├── executor_node.py             # 执行节点类
├── response_generator_node.py   # 响应生成节点类
├── planning_flow.py             # 流程类
├── main.py                      # 主程序文件（依赖外部API）
├── mock_planner_node.py         # 模拟规划节点类（不依赖外部API）
├── mock_executor_node.py        # 模拟执行节点类（不依赖外部API）
├── mock_response_generator_node.py # 模拟响应生成节点类（不依赖外部API）
├── mock_planning_flow.py        # 模拟流程类（不依赖外部API）
├── mock_main.py                 # 模拟主程序文件（不依赖外部API）
└── README.md                    # 说明文档
```

## 实现原理

### 1. 规划节点 (PlannerNode)

规划节点负责接收任务描述，并生成一个详细的执行计划。它使用大语言模型（LLM）来分析任务并创建步骤列表。

### 2. 执行节点 (ExecutorNode)

执行节点负责按照规划节点生成的计划，逐个执行每个步骤。它支持多种工具，如搜索、计算等，并记录每个步骤的执行结果。

### 3. 响应生成节点 (ResponseGeneratorNode)

响应生成节点负责收集所有步骤的执行结果，并生成最终的响应。它使用LLM来整合所有信息，形成连贯的最终回答。

### 4. 流程类 (PlanningFlow)

流程类将上述三个节点连接起来，定义了节点之间的转换规则：
- `start` → `plan` → `execute_plan` → `generate_response` → `end`
- `execute_plan` 可以循环执行，直到所有步骤完成

## 使用方法

### 依赖外部API的版本

```python
from planning_flow import PlanningFlow

async def main():
    planning_flow = PlanningFlow()
    result = await planning_flow.run("分析人工智能在医疗领域的应用")
    print(result)
```

## 运行步骤

1. 确保已安装所有依赖项
2. 运行依赖外部API的版本：
   ```bash
   cd /path/to/pocketflow-adp/adp/chapter6
   python3 main.py
   ```
3. 或运行不依赖外部API的模拟版本：
   ```bash
   cd /path/to/pocketflow-adp/adp/chapter6
   python3 mock_main.py
   ```

## 依赖项

- PocketFlow 框架
- OpenAI API (用于实际版本)
- asyncio (用于异步执行)

## 特点

1. **动态规划**：根据任务描述自动生成执行计划
2. **工具集成**：支持多种工具执行不同类型的步骤
3. **异步执行**：使用异步编程提高执行效率
4. **灵活扩展**：可以轻松添加新的节点类型和工具
5. **模拟版本**：提供不依赖外部API的模拟版本，便于演示和测试

## 应用场景

- 复杂问题分析与解决
- 多步骤任务自动化
- 研究报告生成
- 决策支持系统
- 智能助手功能