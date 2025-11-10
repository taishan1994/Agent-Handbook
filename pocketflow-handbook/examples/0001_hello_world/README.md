# PocketFlow Hello World 课程示例

这是PocketFlow框架的第一个课程示例，旨在帮助您了解PocketFlow的基本概念和使用方法。

## 学习目标

通过本示例，您将学习：
- PocketFlow框架的基本概念：Node（节点）和Flow（流程）
- 如何创建自定义节点类
- 如何构建简单的PocketFlow流程
- 如何在流程中共享数据
- 如何运行PocketFlow应用程序

## 项目结构

```
0001_hello_world/
├── utils/
│   └── call_llm.py   # LLM调用工具函数
├── flow.py           # PocketFlow节点和流程定义
├── main.py           # 主应用入口
├── README.md         # 项目文档（当前文件）
```

## PocketFlow核心概念

### Node（节点）
节点是PocketFlow中执行具体操作的基本单元，每个节点包含三个核心方法：

1. **prep方法**：准备阶段，从共享数据中提取所需的输入
2. **exec方法**：执行阶段，使用输入数据执行核心业务逻辑
3. **post方法**：后续处理阶段，将执行结果存储回共享数据

在本示例中，`AnswerNode`类是一个简单的节点，它从共享数据中获取问题，调用LLM获取回答，然后将回答存储回共享数据。

### Flow（流程）
流程是PocketFlow中组织节点执行的容器。一个流程可以包含多个节点，节点之间通过共享数据进行通信。

在本示例中，`qa_flow`是一个简单的流程，只包含一个`answer_node`节点。

## 代码解析

### utils/call_llm.py
这个文件包含一个调用OpenAI LLM API的工具函数。它创建一个OpenAI客户端，然后调用chat completions API生成响应。

### flow.py
这个文件定义了自定义节点类`AnswerNode`和流程实例`qa_flow`。

### main.py
这个文件是应用程序的入口点。它创建一个共享数据字典，然后运行流程，最后输出结果。

## 运行示例

1. 安装依赖：
```bash
cd pocketflow-handbook/PocketFlow
pip install -e .
```

2. 替换API密钥：
在`utils/call_llm.py`中，将`YOUR_API_KEY_HERE`替换为您的OpenAI API密钥。（这里我使用的是自己部署的模型）

3. 运行示例：
```bash
python main.py
```

## 扩展练习

尝试修改代码，实现以下功能：

1. 更改问题内容
2. 添加多个节点到流程中
3. 实现更复杂的数据处理逻辑

## 下一步学习

完成本示例后，您可以继续学习更高级的PocketFlow功能，如多节点流程、错误处理、异步执行等。