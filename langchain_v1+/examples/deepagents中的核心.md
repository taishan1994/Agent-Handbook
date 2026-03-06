## 核心组件

### 1. `get_default_model()` - 获取默认模型

```python
def get_default_model() -> ChatAnthropic:
    """Get the default model for deep agents.

    Returns:
        `ChatAnthropic` instance configured with Claude Sonnet 4.5.
    """
    return ChatAnthropic(
        model_name="claude-sonnet-4-5-20250929",
        max_tokens=20000,
    )
```

**功能**：返回配置了Claude Sonnet 4.5的默认聊天模型实例。

**特点**：
- 默认使用Claude Sonnet 4.5
- 最大token数设置为20000
- 可以被自定义模型覆盖

---

### 2. `create_deep_agent()` - 创建深度Agent（核心函数）

这是deepagents的核心函数，用于创建功能完整的智能agent。

#### 函数签名

```python
def create_deep_agent(
    model: str | BaseChatModel | None = None,
    tools: Sequence[BaseTool | Callable | dict[str, Any]] | None = None,
    *,
    system_prompt: str | SystemMessage | None = None,
    middleware: Sequence[AgentMiddleware] = (),
    subagents: list[SubAgent | CompiledSubAgent] | None = None,
    skills: list[str] | None = None,
    memory: list[str] | None = None,
    response_format: ResponseFormat | None = None,
    context_schema: type[Any] | None = None,
    checkpointer: Checkpointer | None = None,
    store: BaseStore | None = None,
    backend: BackendProtocol | BackendFactory | None = None,
    interrupt_on: dict[str, bool | InterruptOnConfig] | None = None,
    debug: bool = False,
    name: str | None = None,
    cache: BaseCache | None = None,
) -> CompiledStateGraph
```

#### 参数详解

| 参数 | 类型 | 说明 |
|------|------|------|
| `model` | `str \| BaseChatModel \| None` | 使用的模型，默认为Claude Sonnet 4.5 |
| `tools` | `Sequence[BaseTool \| Callable \| dict] \| None` | agent可访问的工具列表 |
| `system_prompt` | `str \| SystemMessage \| None` | 自定义系统指令 |
| `middleware` | `Sequence[AgentMiddleware]` | 额外的中间件 |
| `subagents` | `list[SubAgent \| CompiledSubAgent]` | 子agent列表 |
| `skills` | `list[str]` | 技能源路径列表 |
| `memory` | `list[str]` | 记忆文件路径列表（AGENTS.md） |
| `response_format` | `ResponseFormat` | 结构化输出格式 |
| `context_schema` | `type[Any]` | agent的上下文模式 |
| `checkpointer` | `Checkpointer` | 状态持久化检查点 |
| `store` | `BaseStore` | 持久化存储 |
| `backend` | `BackendProtocol \| BackendFactory` | 文件存储和执行的backend |
| `interrupt_on` | `dict[str, bool \| InterruptOnConfig]` | 工具调用中断配置 |
| `debug` | `bool` | 是否启用调试模式 |
| `name` | `str` | agent名称 |
| `cache` | `BaseCache` | agent使用的缓存 |

---

## 默认工具

deepagents默认提供以下工具：

### 1. `write_todos` - 待办事项管理
- 管理agent的任务列表
- 支持添加、完成、删除任务

### 2. 文件操作工具
- `ls` - 列出目录文件
- `read_file` - 读取文件内容
- `write_file` - 创建新文件
- `edit_file` - 编辑文件
- `glob` - 查找匹配模式的文件
- `grep` - 搜索文件中的文本

### 3. `execute` - 执行shell命令
- ⚠️ 仅在backend实现`SandboxBackendProtocol`时可用
- 非沙箱backend会返回错误消息

### 4. `task` - 调用子agent
- 启动临时子agent处理特定任务
- 支持并行执行多个子agent

---

## Middleware栈（中间件栈）

### 主Agent的Middleware栈

```python
deepagent_middleware: list[AgentMiddleware] = [
    TodoListMiddleware(),              # 1. 待办事项管理
    MemoryMiddleware(...),            # 2. 记忆加载（如果提供）
    SkillsMiddleware(...),            # 3. 技能加载（如果提供）
    FilesystemMiddleware(...),        # 4. 文件系统工具
    SubAgentMiddleware(...),          # 5. 子agent支持
    SummarizationMiddleware(...),     # 6. 对话摘要
    AnthropicPromptCachingMiddleware(), # 7. 提示缓存
    PatchToolCallsMiddleware(),       # 8. 工具调用修复
    HumanInTheLoopMiddleware(...),    # 9. 人工干预（如果提供）
]
```

### 子Agent的Middleware栈

```python
subagent_middleware: list[AgentMiddleware] = [
    TodoListMiddleware(),              # 1. 待办事项管理
    SkillsMiddleware(...),            # 2. 技能加载（如果提供）
    FilesystemMiddleware(...),        # 3. 文件系统工具
    SummarizationMiddleware(...),     # 4. 对话摘要
    AnthropicPromptCachingMiddleware(), # 5. 提示缓存
    PatchToolCallsMiddleware(),       # 6. 工具调用修复
]
```

**注意**：子agent不包含MemoryMiddleware和SubAgentMiddleware，以避免递归。

---

## 智能摘要策略

根据模型的`max_input_tokens`自动调整摘要策略：

```python
if model.profile is not None and "max_input_tokens" in model.profile:
    # 大上下文模型（如Claude 200K）
    trigger = ("fraction", 0.85)  # 85%上下文窗口时触发
    keep = ("fraction", 0.10)     # 保留10%上下文
    truncate_args_settings = {
        "trigger": ("fraction", 0.85),
        "keep": ("fraction", 0.10),
    }
else:
    # 小上下文模型
    trigger = ("tokens", 170000)  # 170K tokens时触发
    keep = ("messages", 6)        # 保留6条消息
    truncate_args_settings = {
        "trigger": ("messages", 20),
        "keep": ("messages", 20),
    }
```

---

## 使用示例

### 示例1：最简单的deepagent

```python
from deepagents import create_deep_agent

# 使用默认配置
agent = create_deep_agent()

# 调用agent
result = agent.invoke({"messages": [("user", "帮我写一个Python脚本")]})
```

### 示例2：自定义模型

```python
from deepagents import create_deep_agent

# 使用OpenAI GPT-4
agent = create_deep_agent(
    model="openai:gpt-4",
)

# 或者使用模型实例
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(model_name="claude-opus-4-20250514")
agent = create_deep_agent(model=model)
```

### 示例3：添加自定义工具

```python
from deepagents import create_deep_agent
from langchain.tools import tool

@tool
def calculate(expression: str) -> str:
    """计算数学表达式"""
    try:
        result = eval(expression)
        return f"结果: {result}"
    except Exception as e:
        return f"错误: {e}"

agent = create_deep_agent(
    tools=[calculate],
)

result = agent.invoke({"messages": [("user", "计算 2+2*3")]})
```

### 示例4：添加记忆

```python
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

# 创建AGENTS.md文件
agent = create_deep_agent(
    memory=["/memory/AGENTS.md"],
    backend=FilesystemBackend(root_dir="/project"),
)
```

### 示例5：添加技能

```python
from deepagents import create_deep_agent
from deepagents.backends.state import StateBackend

agent = create_deep_agent(
    skills=["/skills/base/", "/skills/user/"],
    backend=lambda rt: StateBackend(rt),
)
```

### 示例6：添加子agent

```python
from deepagents import create_deep_agent

research_agent = {
    "name": "research-analyst",
    "description": "进行复杂主题的深入研究",
    "prompt": "你是一个研究分析师。使用搜索工具收集信息，然后提供综合报告。",
    "tools": [search_tool],
}

code_reviewer = {
    "name": "code-reviewer",
    "description": "审查代码并提供改进建议",
    "prompt": "审查代码的质量、安全性和最佳实践。",
}

agent = create_deep_agent(
    subagents=[research_agent, code_reviewer],
)
```

### 示例7：人工干预

```python
from deepagents import create_deep_agent

# 在编辑文件前暂停
agent = create_deep_agent(
    interrupt_on={
        "edit_file": True,  # 每次编辑前暂停
        "execute": {"confirm": "dangerous"},  # 危险命令需要确认
    },
)
```

### 示例8：持久化状态

```python
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()

agent = create_deep_agent(
    checkpointer=checkpointer,
)

# 使用thread_id保持会话状态
config = {"configurable": {"thread_id": "session-123"}}
result = agent.invoke({"messages": [("user", "你好")]}, config=config)
```

### 示例9：使用StoreBackend持久化

```python
from deepagents import create_deep_agent
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: StoreBackend(rt),
)
```

### 示例10：自定义系统提示

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    system_prompt="你是一个专业的Python开发者，专注于编写高质量的代码。",
)
```

### 示例11：完整配置

```python
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.postgres import PostgresStore

# 完整配置示例
checkpointer = SqliteSaver.from_conn_string(":memory:")
store = PostgresStore(conn_string="postgresql://...")

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[custom_tool],
    system_prompt="你是一个专业的AI助手。",
    middleware=[custom_middleware],
    subagents=[research_agent, code_reviewer],
    skills=["/skills/base/", "/skills/user/"],
    memory=["/memory/AGENTS.md"],
    checkpointer=checkpointer,
    store=store,
    backend=FilesystemBackend(root_dir="/workspace", virtual_mode=True),
    interrupt_on={"edit_file": True},
    debug=True,
    name="my-agent",
)
```

---

## 子Agent配置

### SubAgent字典格式

```python
subagent: SubAgent = {
    "name": "research-analyst",           # 必需：子agent名称
    "description": "进行复杂主题的深入研究",  # 必需：描述（用于主agent决策）
    "prompt": "你是一个研究分析师...",      # 必需：系统提示
    "tools": [search_tool],               # 可选：工具列表
    "model": "gpt-4",                     # 可选：模型（字符串或实例）
    "middleware": [custom_middleware],    # 可选：中间件列表
}
```

### CompiledSubAgent格式

```python
from deepagents import create_deep_agent

# 创建一个子agent
subagent = create_deep_agent(
    model="gpt-4",
    tools=[search_tool],
    system_prompt="你是一个研究分析师。",
)

# 在主agent中使用
main_agent = create_deep_agent(
    subagents=[subagent],
)
```

---

## Backend配置

### StateBackend（默认）

```python
from deepagents import create_deep_agent
from deepagents.backends.state import StateBackend

agent = create_deep_agent(
    backend=lambda rt: StateBackend(rt),
)
```

### FilesystemBackend

```python
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

agent = create_deep_agent(
    backend=FilesystemBackend(
        root_dir="/workspace",
        virtual_mode=True,  # 启用虚拟模式，限制路径访问
    ),
)
```

### StoreBackend

```python
from deepagents import create_deep_agent
from deepagents.backends.store import StoreBackend
from langgraph.store.memory import InMemoryStore

store = InMemoryStore()

agent = create_deep_agent(
    store=store,
    backend=lambda rt: StoreBackend(rt),
)
```

### SandboxBackend

```python
from deepagents import create_deep_agent
from deepagents.backends.sandbox import DockerSandbox

agent = create_deep_agent(
    backend=DockerSandbox(),
)
```

### CompositeBackend

```python
from deepagents import create_deep_agent
from deepagents.backends.composite import CompositeBackend
from deepagents.backends.state import StateBackend
from deepagents.backends.store import StoreBackend

agent = create_deep_agent(
    backend=CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(rt),
            "/persistent/": StoreBackend(rt),
        }
    ),
)
```

---

## 系统提示组合

`create_deep_agent()`会自动将自定义系统提示与基础提示组合：

```python
BASE_AGENT_PROMPT = "In order to complete the objective that the user asks of you, you have access to a number of standard tools."
```

### 组合规则

1. **无自定义提示**：使用`BASE_AGENT_PROMPT`
2. **字符串提示**：简单拼接
   ```python
   final_system_prompt = system_prompt + "\n\n" + BASE_AGENT_PROMPT
   ```
3. **SystemMessage提示**：追加到content_blocks
   ```python
   new_content = [
       *system_prompt.content_blocks,
       {"type": "text", "text": f"\n\n{BASE_AGENT_PROMPT}"},
   ]
   final_system_prompt = SystemMessage(content=new_content)
   ```

---

## 重要特性

### 1. 递归限制
```python
.with_config({"recursion_limit": 1000})
```
设置递归限制为1000，防止无限循环。

### 2. 智能摘要
根据模型上下文大小自动调整摘要策略，优化token使用。

### 3. 工具参数截断
自动截断旧消息中的大工具参数，减少摘要时的token消耗。

### 4. 提示缓存
使用`AnthropicPromptCachingMiddleware`缓存提示，提高性能。

### 5. 工具调用修复
使用`PatchToolCallsMiddleware`修复悬空的工具调用。

---

## 最佳实践

1. **模型选择**：根据任务复杂度选择合适的模型
2. **Backend选择**：根据持久性需求选择backend
3. **Middleware顺序**：使用默认middleware栈，必要时添加自定义middleware
4. **子agent设计**：保持子agent专注，避免功能重叠
5. **技能组织**：按层级组织技能（base → user → project）
6. **人工干预**：对危险操作启用人工干预
7. **状态持久化**：使用checkpointer保持会话状态
8. **调试模式**：开发时启用debug模式

---

## 总结

`graph.py`中的`create_deep_agent()`函数是deepagents的核心，它：

1. ✅ 提供开箱即用的完整agent功能
2. ✅ 支持丰富的自定义选项
3. ✅ 自动配置合理的middleware栈
4. ✅ 智能处理摘要和token优化
5. ✅ 支持子agent、技能、记忆等高级功能
6. ✅ 灵活的backend和存储选项
7. ✅ 完善的状态持久化和人工干预机制

通过这个函数，您可以快速构建功能强大的AI agent，满足各种复杂的应用场景。