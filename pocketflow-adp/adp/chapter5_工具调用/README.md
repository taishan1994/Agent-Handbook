# Chapter 5: Tool Use Pattern with PocketFlow

本章展示了如何使用PocketFlow实现工具使用模式。工具使用模式允许Agent调用外部工具来获取信息或执行操作，这是现代AI系统的核心功能之一。

## 实现概述

我们提供了两个基于不同框架示例的实现：

1. **基于LangChain示例的实现** (`flow.py`) - 展示了多工具集成和工具调用解析
2. **基于CrewAI示例的实现** (`crewai_flow.py`) - 展示了财务分析场景中的工具使用

## 核心概念

### 工具抽象

我们创建了一个通用的`Tool`基类，用于定义工具的接口：

```python
class Tool:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    async def execute(self, **kwargs) -> Any:
        """执行工具操作"""
        raise NotImplementedError("子类必须实现execute方法")
```

### 节点设计

工具使用模式包含以下关键节点：

1. **ToolCallParserNode** - 解析用户输入并决定是否需要调用工具
2. **ToolExecutorNode** - 执行工具调用
3. **ResponseGeneratorNode** - 基于工具结果生成最终响应

### 流程控制

使用PocketFlow的条件路由功能，根据工具解析结果决定流程走向：

```python
# 如果需要使用工具，路由到执行器
self.parser.next(self.executor, action="use_tool")
# 如果直接回答，路由到响应生成器
self.parser.next(self.generator, action="direct_answer")
```

## 实现细节

### LangChain示例实现

`flow.py`实现了以下功能：

- **多工具支持**：包含信息搜索和股票价格查询两个工具
- **工具调用解析**：使用LLM解析JSON格式的工具调用
- **错误处理**：处理工具调用失败的情况

主要组件：

- `SearchInformationTool` - 模拟信息搜索工具
- `StockPriceTool` - 模拟股票价格查询工具
- `ToolCallParserNode` - 解析工具调用
- `ToolExecutorNode` - 执行工具调用
- `ResponseGeneratorNode` - 生成响应
- `ToolUseFlow` - 整合所有节点的流程

### CrewAI示例实现

`crewai_flow.py`实现了以下功能：

- **财务分析场景**：专注于股票价格查询和分析
- **角色扮演**：模拟财务分析师角色
- **结构化响应**：提供专业的财务分析结果

主要组件：

- `FinancialTool` - 股票价格查询工具
- `FinancialAnalystNode` - 财务分析师节点
- `ToolExecutorNode` - 工具执行节点
- `ResponseGeneratorNode` - 响应生成节点
- `FinancialAnalysisFlow` - 财务分析流程

## 使用方法

### 运行LangChain示例

```python
import asyncio
from flow import tool_use_flow

async def main():
    # 创建共享状态
    shared_state = {
        "user_input": "帮我查找苹果公司的最新股价",
        "history": []
    }
    
    # 运行流程
    result = await tool_use_flow.run(shared_state)
    
    # 打印结果
    print("最终响应:", result.get("final_response"))

if __name__ == "__main__":
    asyncio.run(main())
```

### 运行CrewAI示例

```python
import asyncio
from crewai_flow import financial_analysis_flow

async def main():
    # 创建共享状态
    shared_state = {
        "task_description": "分析苹果公司(AAPL)的当前股价，并提供投资建议"
    }
    
    # 运行流程
    result = await financial_analysis_flow.run(shared_state)
    
    # 打印结果
    print("最终响应:", result.get("final_response"))

if __name__ == "__main__":
    asyncio.run(main())
```

## 扩展指南

### 添加新工具

1. 创建继承自`Tool`的新工具类：

```python
class WeatherTool(Tool):
    def __init__(self):
        super().__init__(
            name="Weather Lookup Tool",
            description="获取指定城市的天气信息"
        )
    
    async def execute(self, city: str) -> str:
        # 实现天气查询逻辑
        return f"{city}今天晴天，温度25°C"
```

2. 在流程中添加工具：

```python
weather_tool = WeatherTool()
# 将工具添加到工具字典中
tools = {
    "Weather Lookup Tool": weather_tool,
    # 其他工具...
}
```

### 自定义节点

1. 创建继承自`AsyncNode`的新节点类：

```python
class CustomNode(AsyncNode):
    async def prep_async(self, shared_state):
        # 准备输入
        return {"input": shared_state.get("data")}
    
    async def exec_async(self, prep_result):
        # 执行逻辑
        return {"result": "处理后的数据"}
    
    async def post_async(self, shared_state, prep_result, exec_result):
        # 后处理
        shared_state["custom_result"] = exec_result.get("result")
        return shared_state
```

2. 在流程中添加节点：

```python
custom_node = CustomNode()
self.previous_node.next(custom_node)
```

## 最佳实践

1. **工具设计**：保持工具功能单一，参数明确
2. **错误处理**：在工具执行节点中添加适当的错误处理
3. **提示工程**：精心设计LLM提示，确保工具调用格式正确
4. **状态管理**：合理使用共享状态传递信息
5. **模块化**：将不同功能分离到不同节点中

## 与其他框架的对比

| 特性 | PocketFlow | LangChain | CrewAI |
|------|-----------|-----------|--------|
| 工具定义 | 自定义Tool类 | Tool装饰器 | Tool类 |
| 流程控制 | 条件路由 | AgentExecutor | Crew |
| 异步支持 | 原生支持 | 有限 | 有限 |
| 灵活性 | 高 | 中 | 中 |
| 学习曲线 | 中 | 低 | 低 |

## 总结

PocketFlow提供了灵活而强大的工具使用模式实现，通过节点和流程的组合，可以轻松构建复杂的工具调用逻辑。相比其他框架，PocketFlow在异步支持和流程控制方面具有明显优势，特别适合需要高度定制化的应用场景。