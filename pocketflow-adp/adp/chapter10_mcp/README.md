# Chapter 10: 模型上下文协议 (MCP) - PocketFlow实现

本项目是基于《Agent设计模式》第10章的MCP示例，使用PocketFlow框架实现的模型上下文协议(MCP)应用。

## 项目概述

模型上下文协议(MCP)是一种标准化的协议，允许AI模型与外部工具和服务进行交互。本项目实现了以下功能：

1. **文件系统交互**：读取、写入和列出文件/目录
2. **Web搜索**：使用Exa API进行网络搜索
3. **文件内容分析**：使用LLM分析文件内容

## 项目结构

```
chapter10_mcp/
├── mcp_server.py    # MCP服务器实现
├── mcp_client.py    # 使用PocketFlow的MCP客户端
├── requirements.txt # 依赖项
└── README.md       # 本文档
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 启动MCP服务器

MCP服务器提供以下工具：

- `read_file`: 读取文件内容
- `write_file`: 写入内容到文件
- `list_directory`: 列出目录内容
- `search_web`: 使用Exa API进行网络搜索
- `analyze_file_content`: 分析文件内容

### 2. 运行MCP客户端

客户端使用PocketFlow框架实现，包含以下节点：

1. **InteractiveNode**: 与用户交互，获取输入
2. **GetToolsNode**: 获取MCP服务器提供的可用工具
3. **DecideToolNode**: 使用LLM决定使用哪个工具
4. **ExecuteToolNode**: 执行选定的工具
5. **ContinueNode**: 询问用户是否继续

运行客户端：

```bash
python mcp_client.py
```

## 示例使用场景

### 读取文件内容

```
用户输入: 读取文件 /path/to/file.txt
```

### Web搜索

```
用户输入: 搜索 "人工智能最新发展"
```

### 文件分析

```
用户输入: 分析文件 /path/to/report.pdf 的内容摘要
```

### 写入文件

```
用户输入: 写入文件 /path/to/output.txt 内容为 "Hello, MCP!"
```

## 技术实现

### PocketFlow工作流

本实现使用PocketFlow框架创建了以下工作流：

```
InteractiveNode -> GetToolsNode -> DecideToolNode -> ExecuteToolNode -> ContinueNode
     ^                                                                              |
     |------------------------------------------------------------------------------|
```

### MCP集成

通过MCP协议，客户端可以：
1. 发现服务器提供的工具
2. 获取工具的参数和描述
3. 调用工具并获取结果

### LLM决策

使用LLM分析用户请求，决定使用哪个工具，并提取必要的参数。

## 注意事项

1. 确保已正确配置LLM API（在utils.py中）
2. 确保已配置Exa API密钥（在exa_search_main.py中）
3. 文件操作需要适当的权限

## 扩展功能

可以通过在mcp_server.py中添加新的工具函数来扩展功能：

```python
@mcp.tool()
def your_tool(param1: str, param2: int) -> str:
    """工具描述"""
    # 实现你的工具逻辑
    return "结果"
```

## 相关资源

- [Agent设计模式 - 第10章](../../agentic-design-patterns/chapters/Chapter%2010_%20Model%20Context%20Protocol%20(MCP).md)
- [PocketFlow框架文档](../../PocketFlow/)
- [MCP协议规范](https://modelcontextprotocol.io/)