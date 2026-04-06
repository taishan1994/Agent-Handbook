# OpenHarness 架构深度解析：从 Harness Engineer 视角看 Agent 运行时系统

## 引言

在 Harness Engineering 的概念框架下，一个成熟的 Agent 系统需要具备六大核心能力：**执行循环与编排、状态与记忆管理、工具与权限管控、安全护栏与校验、环境隔离与沙箱、反馈与自愈**。OpenHarness 作为开源社区中首个完整实现这些能力的 Python 项目，为我们提供了一个绝佳的学习样本。

本文将从 Harness Engineer 的专业视角，深入拆解 OpenHarness 的架构设计，分析其如何将抽象的 Harness 理念转化为可落地的工程实践。

## 一、整体架构概览

OpenHarness 采用分层模块化架构，核心代码位于 `src/openharness/` 目录下：

```
openharness/
├── engine/          # 执行引擎 - Agent Loop 的核心实现
├── tools/           # 工具系统 - 43+ 可扩展工具
├── permissions/     # 权限管控 - 多级安全策略
├── hooks/           # 生命周期钩子 - 事件驱动扩展
├── sandbox/         # 沙箱隔离 - 安全执行环境
├── coordinator/     # 多Agent协调 - 分布式任务编排
├── skills/          # 技能系统 - 知识注入机制
├── mcp/             # MCP协议 - 工具生态集成
├── tasks/           # 任务管理 - 后台任务生命周期
├── config/          # 配置系统 - 多层配置合并
└── prompts/         # 上下文管理 - 系统提示词组装
```

这种架构设计完美契合了 Harness Engineering 的「分层闭环架构」理念，每个模块职责清晰、边界明确。

## 二、核心模块深度解析

### 2.1 执行引擎：Agent Loop 的心脏

执行引擎是整个 Harness 系统的核心调度中枢。OpenHarness 的 `QueryEngine` 实现了一个经典的 **Plan-Act-Observe-Reflect** 闭环：

```python
class QueryEngine:
    """Owns conversation history and the tool-aware model loop."""

    def __init__(
        self,
        *,
        api_client: SupportsStreamingMessages,
        tool_registry: ToolRegistry,
        permission_checker: PermissionChecker,
        cwd: str | Path,
        model: str,
        system_prompt: str,
        max_tokens: int = 4096,
        max_turns: int | None = 8,
        permission_prompt: PermissionPrompt | None = None,
        ask_user_prompt: AskUserPrompt | None = None,
        hook_executor: HookExecutor | None = None,
        tool_metadata: dict[str, object] | None = None,
    ) -> None:
        ...
```

**设计亮点**：

1. **依赖注入模式**：所有核心组件（API客户端、工具注册表、权限检查器、钩子执行器）通过构造函数注入，实现松耦合。

2. **会话状态管理**：`_messages` 列表维护完整的对话历史，支持断点续跑和会话恢复。

3. **成本追踪**：内置 `CostTracker` 实时监控 Token 消耗，这是生产级 Harness 的必备能力。

4. **最大轮次限制**：`max_turns` 参数防止 Agent 陷入无限循环，体现了「确定性优先」的设计原则。

执行流程的核心逻辑：

```python
async def submit_message(self, prompt: str) -> AsyncIterator[StreamEvent]:
    """Append a user message and execute the query loop."""
    self._messages.append(ConversationMessage.from_user_text(prompt))
    context = QueryContext(
        api_client=self._api_client,
        tool_registry=self._tool_registry,
        permission_checker=self._permission_checker,
        ...
    )
    async for event, usage in run_query(context, self._messages):
        if usage is not None:
            self._cost_tracker.add(usage)
        yield event
```

### 2.2 工具系统：标准化能力封装

OpenHarness 定义了一套优雅的工具抽象体系：

```python
class BaseTool(ABC):
    """Base class for all OpenHarness tools."""

    name: str
    description: str
    input_model: type[BaseModel]

    @abstractmethod
    async def execute(self, arguments: BaseModel, context: ToolExecutionContext) -> ToolResult:
        """Execute the tool."""

    def is_read_only(self, arguments: BaseModel) -> bool:
        """Return whether the invocation is read-only."""
        return False

    def to_api_schema(self) -> dict[str, Any]:
        """Return the tool schema expected by the Anthropic Messages API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_model.model_json_schema(),
        }
```

**设计亮点**：

1. **Pydantic 强类型**：所有工具输入使用 Pydantic 模型定义，自动获得参数校验、类型转换和 JSON Schema 生成能力。

2. **读写分离标识**：`is_read_only()` 方法支持权限系统的精细化控制——只读工具默认放行，写操作需要确认。

3. **自描述能力**：`to_api_schema()` 方法让 LLM 自动理解工具用法，无需额外文档。

以 Bash 工具为例：

```python
class BashToolInput(BaseModel):
    command: str = Field(description="Shell command to execute")
    cwd: str | None = Field(default=None, description="Working directory override")
    timeout_seconds: int = Field(default=120, ge=1, le=600)

class BashTool(BaseTool):
    name = "bash"
    description = "Run a shell command in the local repository."
    input_model = BashToolInput

    async def execute(self, arguments: BashToolInput, context: ToolExecutionContext) -> ToolResult:
        cwd = Path(arguments.cwd).expanduser() if arguments.cwd else context.cwd
        process = await create_shell_subprocess(
            arguments.command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        ...
```

### 2.3 权限管控：多级安全策略

权限系统是 Harness 区别于普通 Agent 框架的核心特征。OpenHarness 实现了三级权限模式：

```python
class PermissionMode(str, Enum):
    DEFAULT = "default"    # 写操作需确认
    FULL_AUTO = "auto"     # 全自动执行
    PLAN = "plan"          # 只读模式，禁止所有写操作
```

权限检查器的核心逻辑：

```python
class PermissionChecker:
    def evaluate(
        self,
        tool_name: str,
        *,
        is_read_only: bool,
        file_path: str | None = None,
        command: str | None = None,
    ) -> PermissionDecision:
        # 1. 显式拒绝列表
        if tool_name in self._settings.denied_tools:
            return PermissionDecision(allowed=False, reason=f"{tool_name} is explicitly denied")

        # 2. 显式允许列表
        if tool_name in self._settings.allowed_tools:
            return PermissionDecision(allowed=True, reason=f"{tool_name} is explicitly allowed")

        # 3. 路径级别规则
        if file_path and self._path_rules:
            for rule in self._path_rules:
                if fnmatch.fnmatch(file_path, rule.pattern):
                    if not rule.allow:
                        return PermissionDecision(allowed=False, ...)

        # 4. 命令拒绝模式
        if command:
            for pattern in self._settings.denied_commands:
                if fnmatch.fnmatch(command, pattern):
                    return PermissionDecision(allowed=False, ...)

        # 5. 全自动模式
        if self._settings.mode == PermissionMode.FULL_AUTO:
            return PermissionDecision(allowed=True, reason="Auto mode allows all tools")

        # 6. 只读工具默认放行
        if is_read_only:
            return PermissionDecision(allowed=True, reason="read-only tools are allowed")

        # 7. Plan 模式阻止写操作
        if self._settings.mode == PermissionMode.PLAN:
            return PermissionDecision(allowed=False, reason="Plan mode blocks mutating tools")

        # 8. 默认模式需要确认
        return PermissionDecision(allowed=False, requires_confirmation=True, ...)
```

**设计亮点**：

1. **多层级校验**：工具级别 → 路径级别 → 命令级别，层层递进。

2. **Glob 模式匹配**：路径规则支持通配符，如 `/etc/*` 禁止访问系统目录。

3. **决策透明化**：每个决策都附带 `reason`，便于审计和调试。

### 2.4 钩子系统：生命周期事件驱动

钩子系统是 Harness 实现可扩展性的关键机制。OpenHarness 支持四种钩子类型：

```python
# 命令钩子：执行外部脚本
class CommandHookDefinition(HookDefinition):
    type: Literal["command"] = "command"
    command: str
    timeout_seconds: int = 30
    block_on_failure: bool = False

# HTTP 钩子：调用远程服务
class HttpHookDefinition(HookDefinition):
    type: Literal["http"] = "http"
    url: str
    headers: dict[str, str] = {}
    timeout_seconds: int = 30

# Prompt 钩子：使用 LLM 验证
class PromptHookDefinition(HookDefinition):
    type: Literal["prompt"] = "prompt"
    prompt: str
    model: str | None = None

# Agent 钩子：启动子 Agent 进行深度验证
class AgentHookDefinition(HookDefinition):
    type: Literal["agent"] = "agent"
    prompt: str
    model: str | None = None
```

钩子执行器的核心流程：

```python
class HookExecutor:
    async def execute(self, event: HookEvent, payload: dict[str, Any]) -> AggregatedHookResult:
        results: list[HookResult] = []
        for hook in self._registry.get(event):
            if not _matches_hook(hook, payload):
                continue
            if isinstance(hook, CommandHookDefinition):
                results.append(await self._run_command_hook(hook, event, payload))
            elif isinstance(hook, HttpHookDefinition):
                results.append(await self._run_http_hook(hook, event, payload))
            elif isinstance(hook, PromptHookDefinition):
                results.append(await self._run_prompt_like_hook(hook, event, payload, agent_mode=False))
            elif isinstance(hook, AgentHookDefinition):
                results.append(await self._run_prompt_like_hook(hook, event, payload, agent_mode=True))
        return AggregatedHookResult(results=results)
```

**典型应用场景**：

- `PreToolUse` 钩子：在工具执行前进行安全检查
- `PostToolUse` 钩子：在工具执行后进行结果验证
- `PreCommit` 钩子：代码提交前的自动化审查

### 2.5 沙箱系统：安全执行底座

OpenHarness 集成了 Anthropic 的 `sandbox-runtime`，实现操作系统级别的隔离：

```python
@dataclass(frozen=True)
class SandboxAvailability:
    enabled: bool
    available: bool
    reason: str | None = None
    command: str | None = None

    @property
    def active(self) -> bool:
        return self.enabled and self.available
```

沙箱配置支持网络和文件系统的精细化控制：

```python
class SandboxSettings(BaseModel):
    enabled: bool = False
    fail_if_unavailable: bool = False
    enabled_platforms: list[str] = []
    network: SandboxNetworkSettings      # 网络白名单/黑名单
    filesystem: SandboxFilesystemSettings # 文件系统读写权限
```

**平台兼容性**：

- Linux/WSL：使用 `bubblewrap (bwrap)` 实现容器隔离
- macOS：使用 `sandbox-exec` 实现沙箱
- Windows：原生不支持，需使用 WSL

### 2.6 多Agent协调：分布式任务编排

OpenHarness 实现了完整的 Coordinator-Worker 架构：

```python
class TeamRegistry:
    """Store teams and agent memberships."""
    def create_team(self, name: str, description: str = "") -> TeamRecord: ...
    def delete_team(self, name: str) -> None: ...
    def add_agent(self, team_name: str, task_id: str) -> None: ...
    def send_message(self, team_name: str, message: str) -> None: ...
```

Coordinator 模式的核心设计：

```python
def get_coordinator_system_prompt() -> str:
    return """You are Claude Code, an AI assistant that orchestrates software engineering tasks across multiple workers.

## 1. Your Role
You are a **coordinator**. Your job is to:
- Help the user achieve their goal
- Direct workers to research, implement and verify code changes
- Synthesize results and communicate with the user

## 2. Your Tools
- **agent** - Spawn a new worker
- **send_message** - Continue an existing worker
- **task_stop** - Stop a running worker
...
"""
```

**Worker 工具集**：

```python
_WORKER_TOOLS = [
    "bash", "file_read", "file_edit", "file_write",
    "glob", "grep", "web_fetch", "web_search",
    "task_create", "task_get", "task_list", "task_output", "skill",
]
```

### 2.7 技能系统：知识注入机制

OpenHarness 的技能系统支持 Markdown 格式的知识模块：

```python
class SkillDefinition:
    name: str
    description: str
    content: str      # Markdown 内容
    source: str       # "bundled" | "user" | "plugin"
    path: str | None
```

技能加载器支持 YAML frontmatter：

```markdown
---
name: commit
description: Create clean, well-structured git commits
---

# Commit Skill

## When to use
Use when the user asks to commit changes.

## Workflow
1. Review staged changes
2. Write a clear commit message
3. Execute git commit
```

**兼容性**：完全兼容 `anthropics/skills` 仓库的格式。

### 2.8 MCP 集成：工具生态扩展

OpenHarness 实现了完整的 MCP (Model Context Protocol) 客户端：

```python
class McpClientManager:
    """Manage MCP connections and expose tools/resources."""

    async def connect_all(self) -> None:
        for name, config in self._server_configs.items():
            if isinstance(config, McpStdioServerConfig):
                await self._connect_stdio(name, config)

    async def call_tool(self, server_name: str, tool_name: str, arguments: dict[str, Any]) -> str:
        session = self._sessions[server_name]
        result: CallToolResult = await session.call_tool(tool_name, arguments)
        ...
```

MCP 配置示例：

```json
{
  "mcp_servers": {
    "filesystem": {
      "type": "stdio",
      "command": "mcp-filesystem",
      "args": ["--root", "/workspace"]
    }
  }
}
```

### 2.9 任务管理：后台任务生命周期

后台任务管理器支持 Shell 和 Agent 两种任务类型：

```python
class BackgroundTaskManager:
    async def create_shell_task(
        self,
        *,
        command: str,
        description: str,
        cwd: str | Path,
        task_type: TaskType = "local_bash",
    ) -> TaskRecord: ...

    async def create_agent_task(
        self,
        *,
        prompt: str,
        description: str,
        cwd: str | Path,
        model: str | None = None,
    ) -> TaskRecord: ...
```

任务状态管理：

```python
class TaskRecord:
    id: str
    type: TaskType           # "local_bash" | "local_agent" | "remote_agent"
    status: TaskStatus       # "running" | "completed" | "failed" | "killed"
    description: str
    output_file: Path
    created_at: float
    started_at: float | None
    ended_at: float | None
    return_code: int | None
```

## 三、设计原则分析

从 Harness Engineering 的视角，OpenHarness 的设计体现了以下核心原则：

### 3.1 错误零重复原则

通过钩子系统和权限规则的组合，OpenHarness 可以在工具执行前后进行校验，防止同类错误重复发生：

```python
# PreToolUse 钩子示例
{
  "hooks": {
    "PreToolUse": [{
      "type": "prompt",
      "matcher": "file_write",
      "prompt": "Check if the file path is safe and the content is valid...",
      "block_on_failure": true
    }]
  }
}
```

### 3.2 确定性优先原则

- **最大轮次限制**：防止无限循环
- **超时控制**：所有工具都有超时参数
- **权限模式**：Plan 模式强制只读

### 3.3 可观测可审计原则

- **成本追踪**：实时监控 Token 消耗
- **任务日志**：所有后台任务输出持久化
- **决策透明**：权限决策附带原因说明

### 3.4 最小权限原则

- **路径级别控制**：限制文件访问范围
- **命令拒绝列表**：阻止高危命令
- **工具白名单**：精确控制可用工具

### 3.5 松耦合原则

- **依赖注入**：核心组件通过构造函数注入
- **插件系统**：支持动态加载技能和钩子
- **多 Provider 支持**：Anthropic、OpenAI、Copilot 等多种后端

## 四、最佳实践启示

### 4.1 工具开发规范

```python
class MyTool(BaseTool):
    name = "my_tool"
    description = "Clear description of what this tool does"
    input_model = MyToolInput

    async def execute(self, arguments: MyToolInput, context: ToolExecutionContext) -> ToolResult:
        # 1. 参数已由 Pydantic 校验
        # 2. 使用 context.cwd 作为工作目录
        # 3. 返回结构化结果
        return ToolResult(output="...", is_error=False)

    def is_read_only(self, arguments: MyToolInput) -> bool:
        # 明确标识读写性质
        return True
```

### 4.2 钩子配置最佳实践

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "matcher": "bash",
        "command": "scripts/validate-command.sh $ARGUMENTS",
        "block_on_failure": true
      }
    ],
    "PostToolUse": [
      {
        "type": "http",
        "matcher": "file_write",
        "url": "https://audit.example.com/log",
        "headers": {"Authorization": "Bearer token"}
      }
    ]
  }
}
```

### 4.3 权限配置示例

```json
{
  "permission": {
    "mode": "default",
    "path_rules": [
      {"pattern": "/etc/*", "allow": false},
      {"pattern": "~/.ssh/*", "allow": false},
      {"pattern": "/workspace/*", "allow": true}
    ],
    "denied_commands": [
      "rm -rf /",
      "rm -rf ~",
      "DROP TABLE *"
    ]
  }
}
```

## 五、总结

OpenHarness 是一个教科书级别的 Harness Engineering 实践案例。它完整实现了 Harness 系统的六大核心模块，并通过清晰的架构设计和模块化组织，展示了如何将抽象的 Harness 理念转化为可落地的工程代码。

**核心价值**：

1. **学习样本**：为 Harness Engineer 提供了完整的参考实现
2. **生产可用**：114 个测试用例，支持多种 LLM 后端
3. **可扩展性**：插件系统、MCP 协议、自定义工具
4. **安全可控**：多级权限、沙箱隔离、审计追踪

**适用场景**：

- 企业内部 AI Agent 平台建设
- 研究 Agent 架构和 Harness 模式
- 快速原型开发和验证
- 多模型后端的统一接入层

作为 Harness Engineer，深入理解 OpenHarness 的架构设计，将帮助我们更好地设计和实现生产级的 AI Agent 系统。

---

## 参考资料

- [OpenHarness GitHub Repository](https://github.com/HKUDS/OpenHarness)
- [Harness Engineering 技术文档](./README.MD)
- [anthropics/skills](https://github.com/anthropics/skills)
- [Model Context Protocol](https://modelcontextprotocol.io/)
