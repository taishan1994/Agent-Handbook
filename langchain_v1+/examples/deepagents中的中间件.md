## 1. MemoryMiddleware（记忆中间件）

### 功能特点
- 从AGENTS.md文件加载agent记忆/上下文
- 支持多个记忆源，按顺序加载并合并
- 自动注入到系统提示中
- 提供记忆更新指导原则

### 适用场景
- ✅ 项目特定的上下文和指令
- ✅ 构建命令、代码风格指南
- ✅ 架构说明和最佳实践
- ✅ 持久化的用户偏好和配置

### 用法示例

```python
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.backends.filesystem import FilesystemBackend

# 初始化
backend = FilesystemBackend(root_dir="/")

middleware = MemoryMiddleware(
    backend=backend,
    sources=[
        "~/.deepagents/AGENTS.md",
        "./.deepagents/AGENTS.md",
    ],
)

# 使用
agent = create_deep_agent(middleware=[middleware])
```

### 记忆更新原则
- **何时更新**：用户明确要求记住、提供反馈、给出角色描述、提供工具使用信息
- **何时不更新**：临时信息、一次性任务、简单问答、过时信息
- **重要**：永远不要存储API密钥、访问令牌、密码等凭据

---

## 2. FilesystemMiddleware（文件系统中间件）

### 功能特点
- 提供完整的文件系统操作工具
- 支持多种backend（FilesystemBackend、StateBackend、StoreBackend、SandboxBackend）
- 提供ls、read_file、write_file、edit_file、glob、grep、execute工具
- 路径验证和安全控制

### 提供的工具
- `ls` - 列出目录文件
- `read_file` - 读取文件（支持分页）
- `write_file` - 创建新文件
- `edit_file` - 编辑文件（精确字符串替换）
- `glob` - 查找匹配模式的文件
- `grep` - 搜索文件中的文本
- `execute` - 在沙箱中执行shell命令（仅SandboxBackend支持）

### 用法示例

```python
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.backends.state import StateBackend

# 使用StateBackend（临时存储）
middleware = FilesystemMiddleware(
    backend=lambda rt: StateBackend(rt),
)

# 使用FilesystemBackend（直接文件系统）
from deepagents.backends.filesystem import FilesystemBackend
middleware = FilesystemMiddleware(
    backend=FilesystemBackend(root_dir="/workspace", virtual_mode=True),
)

# 使用StoreBackend（持久化存储）
from deepagents.backends.store import StoreBackend
middleware = FilesystemMiddleware(
    backend=StoreBackend(runtime),
)

# 使用SandboxBackend（安全执行）
from deepagents.backends.sandbox import DockerSandbox
middleware = FilesystemMiddleware(
    backend=DockerSandbox(),
)

# 使用CompositeBackend（混合存储）
from deepagents.backends.composite import CompositeBackend
middleware = FilesystemMiddleware(
    backend=CompositeBackend(
        default=StateBackend(rt),
        routes={
            "/memories/": StoreBackend(rt),
            "/persistent/": StoreBackend(rt),
        }
    ),
)

agent = create_deep_agent(middleware=[middleware])
```

### 路径规则
- 所有路径必须以`/`开头
- 不允许路径遍历（`..`、`~`）
- 不支持Windows绝对路径（如`C:/...`）
- 支持路径前缀限制

---

## 3. SkillsMiddleware（技能中间件）

### 功能特点
- 实现Anthropic的agent技能模式
- 渐进式披露：先显示元数据，按需读取完整指令
- 支持多源技能加载（base → user → project → team）
- 从backend加载技能，可移植性强

### 技能结构
```
/skills/user/web-research/
├── SKILL.md          # 必需：YAML frontmatter + markdown指令
└── helper.py         # 可选：辅助文件
```

### SKILL.md格式
```markdown
---
name: web-research
description: 结构化的网络研究方法
license: MIT
---

# Web Research Skill

## When to Use
- 用户要求研究某个主题
...
```

### 用法示例

```python
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.backends.filesystem import FilesystemBackend

# 初始化
backend = FilesystemBackend(root_dir="/path/to/skills")

middleware = SkillsMiddleware(
    backend=backend,
    sources=[
        "/skills/base/",
        "/skills/user/",
        "/skills/project/",
    ],
)

# 使用StateBackend
from deepagents.backends.state import StateBackend
middleware = SkillsMiddleware(
    backend=lambda rt: StateBackend(rt),
    sources=["/skills/base/"],
)

agent = create_deep_agent(middleware=[middleware])
```

### 技能元数据规范
- `name`：技能标识符（最多64字符，小写字母数字和连字符）
- `description`：技能功能描述（最多1024字符）
- `path`：SKILL.md文件路径
- 可选：`license`、`compatibility`、`metadata`、`allowed_tools`

### 渐进式披露
1. **识别适用技能**：检查任务是否匹配技能描述
2. **读取完整指令**：使用显示的路径读取SKILL.md
3. **遵循技能指令**：按步骤执行工作流
4. **访问辅助文件**：使用绝对路径访问辅助脚本

---

## 4. SubAgentMiddleware（子Agent中间件）

### 功能特点
- 通过`task`工具启动临时子agent
- 支持自定义子agent和通用子agent
- 隔离上下文窗口，减少主线程token使用
- 支持并行执行多个子agent

### 子Agent类型
1. **通用子agent**：具有主agent的所有工具
2. **自定义子agent**：专门的工具和系统提示

### 用法示例

```python
from deepagents.middleware.subagents import SubAgentMiddleware, SubAgent
from langchain.tools import StructuredTool

# 定义自定义子agent
research_agent: SubAgent = {
    "name": "research-analyst",
    "description": "进行复杂主题的深入研究",
    "system_prompt": "你是一个研究分析师。使用搜索工具收集信息，然后提供综合报告。",
    "tools": [search_tool, web_search_tool],
}

code_reviewer: SubAgent = {
    "name": "code-reviewer",
    "description": "审查代码并提供改进建议",
    "system_prompt": "审查代码的质量、安全性和最佳实践。",
    "tools": [read_file_tool, grep_tool],
}

# 初始化中间件
middleware = SubAgentMiddleware(
    default_model="gpt-4o",
    default_tools=[ls_tool, read_file_tool, write_file_tool],
    subagents=[research_agent, code_reviewer],
    general_purpose_agent=True,  # 包含通用子agent
)

agent = create_deep_agent(middleware=[middleware])
```

### Task工具使用场景

**何时使用task工具：**
- 复杂的多步骤任务，可以完全独立委托
- 任务独立，可以并行运行
- 需要专注推理或大量token/上下文使用
- 沙箱化提高可靠性（如代码执行、结构化搜索）
- 只关心子agent的输出，不关心中间步骤

**何时不使用task工具：**
- 需要看到子agent完成后的中间推理或步骤
- 任务简单（几个工具调用或简单查找）
- 委托不会减少token使用、复杂性或上下文切换
- 分割会增加延迟而没有好处

### 并行执行示例
```python
# 用户："研究LeBron James、Michael Jordan和Kobe Bryant的成就并比较"
# Agent并行启动3个研究子agent
task(description="研究LeBron James的成就", subagent_type="general-purpose")
task(description="研究Michael Jordan的成就", subagent_type="general-purpose")
task(description="研究Kobe Bryant的成就", subagent_type="general-purpose")
# 然后综合结果
```

---

## 5. SummarizationMiddleware（摘要中间件）

### 功能特点
- 对话历史摘要和卸载到backend
- 支持多种触发条件（消息数、token数、比例）
- 保留策略控制（保留多少上下文）
- 工具参数截断功能
- 持久化存储完整历史记录

### 存储格式
- 历史记录存储为markdown：`/conversation_history/{thread_id}.md`
- 每次摘要事件追加新部分，创建运行日志

### 用法示例

```python
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.backends.filesystem import FilesystemBackend

# 基本用法
middleware = SummarizationMiddleware(
    model="gpt-4o-mini",
    backend=FilesystemBackend(root_dir="/data"),
    trigger=("fraction", 0.85),  # 85%上下文窗口时触发
    keep=("fraction", 0.10),     # 保留10%上下文
)

# 使用StateBackend
from deepagents.backends.state import StateBackend
middleware = SummarizationMiddleware(
    model="gpt-4o-mini",
    backend=lambda rt: StateBackend(rt),
    trigger=("messages", 50),    # 50条消息时触发
    keep=("messages", 20),        # 保留20条消息
)

# 启用工具参数截断
middleware = SummarizationMiddleware(
    model="gpt-4o-mini",
    backend=FilesystemBackend(root_dir="/data"),
    trigger=("tokens", 100000),
    keep=("tokens", 20000),
    truncate_args_settings={
        "trigger": ("messages", 50),
        "keep": ("messages", 20),
        "max_length": 2000,
        "truncation_text": "...(truncated)"
    },
)

agent = create_deep_agent(middleware=[middleware])
```

### 触发条件类型
- `("messages", N)` - 消息数达到N时触发
- `("tokens", N)` - token数达到N时触发
- `("fraction", f)` - 上下文窗口比例达到f时触发

### 保留策略类型
- `("messages", N)` - 保留最近N条消息
- `("tokens", N)` - 保留最近N个token
- `("fraction", f)` - 保留上下文窗口的f比例

### 工具参数截断
- 自动截断旧消息中的大工具参数
- 减少摘要时的token使用
- 可配置触发条件和保留策略

---

## 6. PatchToolCallsMiddleware（工具调用修补中间件）

### 功能特点
- 修复消息历史中的悬空工具调用
- 自动为未完成的工具调用添加ToolMessage
- 防止消息历史不一致

### 适用场景
- ✅ 处理中断的工具调用
- ✅ 修复消息历史状态
- ✅ 防止agent状态错误

### 用法示例

```python
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware

middleware = PatchToolCallsMiddleware()

agent = create_deep_agent(middleware=[middleware])
```

### 工作原理
- 在agent运行前检查消息历史
- 找到没有对应ToolMessage的tool_calls
- 自动添加取消消息的ToolMessage

---

## Middleware对比总结

| 特性 | MemoryMiddleware | FilesystemMiddleware | SkillsMiddleware | SubAgentMiddleware | SummarizationMiddleware | PatchToolCallsMiddleware |
|------|------------------|---------------------|------------------|-------------------|-------------------------|-------------------------|
| 主要功能 | 加载记忆 | 文件系统工具 | 技能管理 | 子agent | 对话摘要 | 修复工具调用 |
| 持久性 | 持久化 | 取决于backend | 持久化 | 临时 | 持久化 | 临时 |
| 系统提示注入 | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 工具提供 | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| 适用场景 | 上下文持久化 | 文件操作 | 专用技能 | 任务委托 | 长对话 | 状态修复 |

## 组合使用示例

```python
from deepagents import create_deep_agent
from deepagents.middleware.memory import MemoryMiddleware
from deepagents.middleware.filesystem import FilesystemMiddleware
from deepagents.middleware.skills import SkillsMiddleware
from deepagents.middleware.subagents import SubAgentMiddleware
from deepagents.middleware.summarization import SummarizationMiddleware
from deepagents.middleware.patch_tool_calls import PatchToolCallsMiddleware
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.backends.state import StateBackend

# 创建完整的middleware栈
agent = create_deep_agent(
    model="gpt-4o",
    middleware=[
        # 1. 修复工具调用状态
        PatchToolCallsMiddleware(),
        
        # 2. 加载项目记忆
        MemoryMiddleware(
            backend=FilesystemBackend(root_dir="/"),
            sources=["~/.deepagents/AGENTS.md", "./.deepagents/AGENTS.md"],
        ),
        
        # 3. 提供文件系统工具
        FilesystemMiddleware(
            backend=lambda rt: StateBackend(rt),
        ),
        
        # 4. 加载技能库
        SkillsMiddleware(
            backend=lambda rt: StateBackend(rt),
            sources=["/skills/base/", "/skills/user/"],
        ),
        
        # 5. 支持子agent
        SubAgentMiddleware(
            default_model="gpt-4o",
            default_tools=[ls_tool, read_file_tool],
            subagents=[research_agent],
            general_purpose_agent=True,
        ),
        
        # 6. 对话摘要
        SummarizationMiddleware(
            model="gpt-4o-mini",
            backend=lambda rt: StateBackend(rt),
            trigger=("messages", 50),
            keep=("messages", 20),
        ),
    ],
)
```

## 最佳实践

1. **Middleware顺序**：按功能依赖顺序排列（如PatchToolCallsMiddleware在前）
2. **Backend选择**：根据持久性需求选择合适的backend
3. **技能组织**：按层级组织技能（base → user → project → team）
4. **子agent设计**：保持子agent专注，避免功能重叠
5. **摘要策略**：根据对话长度和token预算调整触发条件
6. **安全考虑**：生产环境使用SandboxBackend和适当的路径限制

这些middleware提供了灵活的agent能力扩展，可以根据具体需求组合使用，构建功能强大的AI agent系统。