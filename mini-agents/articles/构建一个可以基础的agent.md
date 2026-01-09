# 说明

这里我们基于之前的使用的工具，构建一个基础的agent。

# 属性说明
一个基础的agent类包含以下属性：
```python
class Agent:
    """Single agent with basic tools and MCP support."""

    def __init__(
        self,
        llm_client: LLMClient,
        system_prompt: str,
        tools: list[Tool],
        max_steps: int = 50,
        workspace_dir: str = "./workspace",
        token_limit: int = 80000,  # Summary triggered when tokens exceed this value
    ):
        self.llm = llm_client
        self.tools = {tool.name: tool for tool in tools}
        self.max_steps = max_steps
        self.token_limit = token_limit
        self.workspace_dir = Path(workspace_dir)

        # Ensure workspace exists
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Inject workspace information into system prompt if not already present
        if "Current Workspace" not in system_prompt:
            workspace_info = f"\n\n## Current Workspace\nYou are currently working in: `{self.workspace_dir.absolute()}`\nAll relative paths will be resolved relative to this directory."
            system_prompt = system_prompt + workspace_info

        self.system_prompt = system_prompt

        # Initialize message history
        self.messages: list[Message] = [Message(role="system", content=system_prompt)]

        # Initialize logger
        self.logger = AgentLogger()

        # Token usage from last API response (updated after each LLM call)
        self.api_total_tokens: int = 0
        # Flag to skip token check right after summary (avoid consecutive triggers)
        self._skip_next_token_check: bool = False
```
- `self.llm = llm_client` - 大模型客户端，用于与 LLM 交互（如 OpenAI、Claude 等）
- `self.tools = {tool.name: tool for tool in tools}` - 工具字典：将工具列表转为 {name: Tool} 映射，方便运行时按名调用
- `self.max_steps = max_steps` - 单轮任务最大执行步数，防止无限循环
- `self.token_limit = token_limit` - Token 阈值：当累计 token 超过此值时触发摘要，避免上下文溢出
- `self.workspace_dir = Path(workspace_dir)` - 工作区目录，所有文件读写均基于此路径
- `self.workspace_dir.mkdir(parents=True, exist_ok=True)` - 确保工作区目录存在（若不存在则递归创建）
- `if "Current Workspace" not in system_prompt:` - 若系统提示词中未包含工作区信息，则追加当前绝对路径，方便 LLM 理解上下文
- `self.system_prompt = system_prompt` - 最终系统提示词，已包含工作区信息
- `self.messages: list[Message] = [Message(role="system", content=system_prompt)]` - 消息历史，初始仅含系统提示，后续每步对话均追加至此列表
- `self.logger = AgentLogger()` - 日志记录器，用于输出调试、运行信息
- `self.api_total_tokens: int = 0` - 上一次 LLM 调用返回的累计 token 数，用于触发摘要逻辑
- `self._skip_next_token_check: bool = False` - 摘要后跳过下一次 token 检查的标记，防止连续触发摘要

# 方法说明与使用样例

## 1. `add_user_message(content: str)`

**作用**：向消息历史中添加用户消息。

**使用样例**：
```python
agent.add_user_message("请帮我分析这个数据文件")
```

---

## 2. `_estimate_tokens() -> int`

**作用**：使用tiktoken准确计算消息历史的token数量。使用cl100k_base编码器（GPT-4/Claude/M2兼容）。

**使用样例**：
```python
token_count = agent._estimate_tokens()
print(f"当前消息历史的token数量: {token_count}")
```

---

## 3. `_estimate_tokens_fallback() -> int`

**作用**：当tiktoken不可用时的备用token估算方法。使用简单的字符数除以2.5来估算token数。

**使用样例**：
```python
# 当tiktoken初始化失败时自动调用
token_estimate = agent._estimate_tokens_fallback()
```

---

## 4. `async _summarize_messages()`

**作用**：消息历史摘要功能。当token超过限制时，在用户消息之间总结对话内容。策略是保留所有用户消息，并总结每个用户消息之间的执行过程。

**使用样例**：
```python
# 在run()方法中自动调用，无需手动调用
# 当token数量超过token_limit时触发
await agent._summarize_messages()
```

---

## 5. `async _create_summary(messages: list[Message], round_num: int) -> str`

**作用**：为单轮执行创建摘要。接收消息列表和轮次号，返回该轮执行的摘要文本。

**使用样例**：
```python
messages = [
    Message(role="assistant", content="正在执行任务..."),
    Message(role="tool", content="工具执行结果...")
]
summary = await agent._create_summary(messages, round_num=1)
print(f"第1轮的摘要: {summary}")
```

---

## 6. `async run() -> str`

**作用**：执行agent主循环，直到任务完成或达到最大步数。这是Agent的核心方法，负责：
- 检查并总结消息历史
- 调用LLM获取响应
- 执行工具调用
- 记录日志
- 返回最终结果

**使用样例**：
```python
# 基本使用
result = await agent.run()
print(f"任务完成，结果: {result}")

# 完整示例
from Mini_Agents.llm import LLMClient
from Mini_Agents.tools import Tool

# 创建LLM客户端
llm_client = LLMClient(
    api_key="your-api-key",
    model="gpt-4"
)

# 创建工具
tools = [Tool(...)]

# 创建Agent
agent = Agent(
    llm_client=llm_client,
    system_prompt="你是一个有帮助的助手",
    tools=tools,
    max_steps=50,
    workspace_dir="./workspace"
)

# 添加用户消息
agent.add_user_message("请帮我创建一个Python文件")

# 运行agent
result = await agent.run()
```

---

## 7. `get_history() -> list[Message]`

**作用**：获取消息历史的副本。返回当前所有消息的列表，包括系统提示、用户消息、助手消息和工具消息。

**使用样例**：
```python
# 获取完整对话历史
history = agent.get_history()

# 遍历历史消息
for msg in history:
    print(f"{msg.role}: {msg.content}")

# 保存对话历史到文件
import json
with open("conversation_history.json", "w") as f:
    json.dump([msg.dict() for msg in history], f, indent=2)
```

---

# 完整使用示例

```python
import asyncio
from Mini_Agents.base_agent import Agent
from Mini_Agents.llm import LLMClient
from Mini_Agents.tools import ReadTool, WriteTool

async def main():
    # 1. 创建LLM客户端
    llm_client = LLMClient(
        api_key="your-api-key",
        model="gpt-4",
        base_url="https://api.openai.com/v1"
    )
    
    # 2. 准备工具
    workspace_dir = "./my_workspace"
    tools = [
        ReadTool(workspace_dir=workspace_dir),
        WriteTool(workspace_dir=workspace_dir)
    ]
    
    # 3. 创建Agent实例
    agent = Agent(
        llm_client=llm_client,
        system_prompt="你是一个文件操作助手，可以帮助用户读取和写入文件。",
        tools=tools,
        max_steps=50,
        workspace_dir=workspace_dir,
        token_limit=80000
    )
    
    # 4. 添加用户任务
    agent.add_user_message("请创建一个名为hello.txt的文件，内容是'Hello, World!'")
    
    # 5. 运行Agent
    result = await agent.run()
    print(f"\n最终结果: {result}")
    
    # 6. 查看对话历史
    history = agent.get_history()
    print(f"\n对话共进行了 {len(history)} 轮")

# 运行主程序
asyncio.run(main())
```
