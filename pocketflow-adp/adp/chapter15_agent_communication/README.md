# Chapter 15: Agent间通信 (A2A协议) - PocketFlow实现

## 概述

本模块实现了基于PocketFlow的Agent间通信(A2A)协议，使多个Agent能够相互发现、通信和协作。A2A协议是一种轻量级的Agent间通信协议，支持任务发送、接收和协作。

## 主要组件

### 1. AgentCard
- **文件**: `agent_card.py`
- **功能**: 描述Agent的能力和通信端点
- **主要类**:
  - `AgentCard`: 包含Agent的基本信息、技能和能力
  - `AgentSkill`: 描述Agent的特定技能
  - `AgentCapabilities`: 描述Agent的能力，如是否支持流式响应

### 2. A2A通信节点
- **文件**: `a2a_nodes.py`
- **功能**: 实现A2A通信协议的核心节点
- **主要类**:
  - `SendTaskNode`: 发送任务到其他Agent
  - `ReceiveTaskNode`: 接收来自其他Agent的任务
  - `DiscoverAgentsNode`: 发现其他Agent

### 3. Agent注册表
- **文件**: `agent_registry.py`
- **功能**: 实现Agent发现机制
- **主要类**:
  - `AgentRegistry`: 管理Agent的注册和发现

### 4. A2A流程
- **文件**: `a2a_flow.py`
- **功能**: 封装A2A通信的核心逻辑
- **主要类**:
  - `A2AFlow`: 提供发送任务、接收任务和发现Agent的功能
  - `CollaborationFlow`: 实现多Agent协作逻辑

### 5. 示例Agent
- **文件**: `example_agents.py`
- **功能**: 演示A2A协议的使用
- **主要类**:
  - `WeatherAgent`: 天气查询Agent
  - `NewsAgent`: 新闻查询Agent
  - `TranslationAgent`: 文本翻译Agent
  - `CoordinatorAgent`: 协调其他Agent的Agent

## 使用示例

### 创建并注册Agent

```python
from pocketflow_adp.adp.chapter15_agent_communication import (
    AgentRegistry, 
    WeatherAgent, 
    NewsAgent, 
    CoordinatorAgent
)

# 创建Agent注册表
registry = AgentRegistry()

# 创建Agent
weather_agent = WeatherAgent()
news_agent = NewsAgent()
coordinator_agent = CoordinatorAgent()

# 注册Agent
registry.register_agent(weather_agent.agent_card)
registry.register_agent(news_agent.agent_card)
registry.register_agent(coordinator_agent.agent_card)
```

### 发送任务到其他Agent

```python
# 发送天气查询任务
response = await coordinator_agent.a2a_flow.send_task(
    agent_card=weather_agent.agent_card,
    task_id="weather-001",
    session_id="session-001",
    message={
        "role": "user",
        "parts": [
            {
                "type": "text",
                "text": "北京今天天气怎么样？"
            }
        ]
    },
    accepted_output_modes=["text/plain"],
    history_length=5
)

# 获取结果
weather_info = response["task"]["artifacts"][0]["data"]
```

### 接收并处理任务

```python
# 定义任务处理函数
async def handle_weather_query(task_id, session_id, message, agent_card, context):
    # 处理天气查询逻辑
    # ...
    return {
        "task": {
            "id": task_id,
            "status": {
                "state": "completed",
                "timestamp": "2025-06-20T10:00:00Z"
            },
            "artifacts": [
                {
                    "name": "weather_info",
                    "type": "text/plain",
                    "data": "北京今天天气晴朗，温度25°C，微风，适合外出。"
                }
            ]
        }
    }

# 接收任务
response = await weather_agent.a2a_flow.receive_task(
    request=request,
    task_handler=handle_weather_query
)
```

### 多Agent协作

```python
# 创建协作流程
collaboration_flow = coordinator_agent.a2a_flow.create_collaboration_flow(
    agents=["WeatherBot", "NewsBot"],
    initial_message={
        "role": "user",
        "parts": [
            {
                "type": "text",
                "text": "帮我查询北京天气和最新新闻"
            }
        ]
    },
    max_iterations=2
)

# 运行协作流程
result = await collaboration_flow.run()
```

## 运行测试

```bash
# 运行单元测试
python -m unittest adp/chapter15_agent_communication/test_a2a.py

# 运行示例
python -m adp.chapter15_agent_communication.example_agents
```

## 与MCP协议的区别

A2A协议与MCP(Model Context Protocol)相比有以下特点：

1. **轻量级**: A2A协议更简单，专注于Agent间通信
2. **灵活性**: 支持多种交互模式和发现机制
3. **安全性**: 内置双向TLS和审计日志等安全特性
4. **协作性**: 专门设计用于多Agent协作场景

## 实际应用场景

1. **多Agent协作系统**: 多个专门Agent协同完成复杂任务
2. **分布式AI服务**: 将不同AI能力封装为独立Agent
3. **微服务架构**: 在微服务间实现智能通信
4. **边缘计算**: 在边缘设备间实现Agent通信

## 扩展性

A2A协议设计为可扩展的，支持：

1. **自定义技能**: Agent可以定义自己的技能和能力
2. **多种通信模式**: 支持同步、异步和流式通信
3. **插件架构**: 可以轻松添加新的通信协议
4. **多框架支持**: 可以与不同AI框架集成