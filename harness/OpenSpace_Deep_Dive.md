# OpenSpace 深度拆解：从 Harness Engineer 视角理解下一代 Agent 基础设施

## 引言

如果说 OpenHarness 是 Agent 系统的"操作系统内核"，那么 OpenSpace 则是面向实际生产环境的"全栈解决方案"。作为一个 Harness Engineer，在深入分析 OpenSpace 之后，我发现它不仅仅是一个简单的 Agent 框架，而是一个完整的、可扩展的、具备自我进化能力的智能体基础设施。

OpenSpace 的核心设计理念可以概括为：**Grounding（接地）+ Skill（技能）+ Evolution（进化）**。这三者构成了一个闭环系统，让 Agent 不仅能执行任务，还能从执行中学习、积累经验、持续进化。

---

## 一、架构总览：分层闭环设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ GroundingAgent│  │   MCP Server │  │   Dashboard Server   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Orchestration Layer                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    GroundingClient                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │ ProviderReg │  │ SessionMgr  │  │ SearchCoordinator│  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Backend Layer                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────┐ │
│  │   MCP   │  │  Shell  │  │   GUI   │  │   Web   │  │System│ │
│  │ Provider│  │ Provider│  │ Provider│  │ Provider│  │Prov. │ │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └──────┘ │
├─────────────────────────────────────────────────────────────────┤
│                        Skill Engine Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │
│  │SkillRegistry│  │SkillEvolver │  │  ExecutionAnalyzer    │  │
│  └─────────────┘  └─────────────┘  └───────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │
│  │ SkillRanker │  │  SkillStore │  │ ToolQualityManager    │  │
│  └─────────────┘  └─────────────┘  └───────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        Infrastructure Layer                     │
│  ┌─────────────┐  ┌─────────────┐  ┌───────────────────────┐  │
│  │  LLMClient  │  │   Recorder  │  │    Security/Sandbox   │  │
│  └─────────────┘  └─────────────┘  └───────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心设计原则

OpenSpace 的架构设计体现了以下几个关键原则：

1. **多后端统一抽象**：通过 Provider/Session 模式，将 MCP、Shell、GUI、Web 等不同后端统一为一致的工具调用接口
2. **技能驱动**：以 Skill 为核心的知识注入机制，让 Agent 能够快速获得领域专业知识
3. **质量感知**：工具质量追踪系统，为工具选择提供数据驱动的决策依据
4. **自我进化**：从执行中学习，自动改进和生成新技能

---

## 二、Grounding 系统：多后端统一接入

### 2.1 GroundingClient：全局入口

OpenSpace/openspace/grounding/core/grounding_client.py 是整个 Grounding 系统的核心入口，它负责：

```python
class GroundingClient:
    """
    Global Entry, Facing Agent/Application, only concerned with Provider & Session
    """
    def __init__(self, config: Optional[GroundingConfig] = None, recording_manager=None):
        self._config: GroundingConfig = config or get_config()
        self._registry: ProviderRegistry = ProviderRegistry()
        
        # Session management
        self._sessions: Dict[str, BaseSession] = {}
        self._server_session_map: dict[tuple[BackendType, str], str] = {}
        
        # Tool cache with TTL
        self._tool_cache: "OrderedDict[str, tuple[List[BaseTool], float]]" = OrderedDict()
        self._tool_cache_ttl: int = 300
        
        # Quality manager
        self._quality_manager = self._init_quality_manager()
```

**设计亮点**：

1. **延迟初始化**：Provider 只在首次使用时初始化，避免启动时阻塞
2. **工具缓存**：带 TTL 的 LRU 缓存，减少重复的工具发现开销
3. **质量集成**：内置 ToolQualityManager，为工具选择提供质量数据

### 2.2 Provider/Session 抽象

OpenSpace 定义了一套优雅的 Provider/Session 抽象：

#### Provider 层

OpenSpace/openspace/grounding/core/provider.py 是后端的工厂和管理者：

```python
class Provider(ABC, Generic[TSession]):
    """Backend provider base class"""
    def __init__(self, backend_type: BackendType, config: Dict[str, Any] = None):
        self.backend_type = backend_type
        self._sessions: Dict[str, TSession] = {}
        self.security_manager = SecurityPolicyManager()
    
    @abstractmethod
    async def create_session(self, session_config: SessionConfig) -> TSession:
        """Create session, update _sessions"""
        pass
    
    async def list_tools(self, session_name: Optional[str] = None) -> List[BaseTool]:
        """Return BaseTool list from specified or all sessions"""
        pass
    
    async def call_tool(self, session_name: str, tool_name: str, parameters: Dict) -> ToolResult:
        """Execute tool in specified session"""
        pass
```

#### Session 层

OpenSpace/openspace/grounding/core/session.py 代表一个具体的连接会话：

```python
class BaseSession(ABC):
    """Session manager for all backends."""
    def __init__(self, connector: BaseConnector, *, session_id: str, backend_type: BackendType):
        self.connector = connector
        self.session_id = session_id
        self.status: SessionStatus = SessionStatus.DISCONNECTED
        self.tools: List[BaseTool] = []
    
    async def __aenter__(self) -> "BaseSession":
        if self.auto_connect:
            await self.connect()
        if self.auto_initialize:
            self.session_info = await self.initialize()
        return self
    
    @abstractmethod
    async def initialize(self) -> Dict[str, Any]:
        """Negotiate with backend, discover tools"""
        pass
```

### 2.3 多后端实现

#### MCP Provider

OpenSpace/openspace/grounding/backends/mcp/provider.py 管理 MCP 协议服务器：

```python
class MCPProvider(Provider[MCPSession]):
    """MCP Provider manages multiple MCP server sessions."""
    
    def __init__(self, config: Dict | None = None, installer: Optional[MCPInstallerManager] = None):
        super().__init__(BackendType.MCP, config)
        
        self._client = MCPClient(
            config=config or {},
            sandbox=sandbox,
            timeout=timeout,
            max_retries=max_retries,
            installer=installer,
        )
        self._server_sessions: Dict[str, MCPSession] = {}
```

**关键特性**：
- 支持多种传输协议：stdio、SSE、WebSocket、HTTP
- 自动依赖安装：通过 MCPInstallerManager 管理 npm/uvx 依赖
- 沙箱隔离：可选的 E2B 沙箱执行环境

#### Shell Provider

OpenSpace/openspace/grounding/backends/shell/provider.py 提供命令行执行能力：

```python
class ShellProvider(Provider[ShellSession]):
    def _setup_security_policy(self, config: dict | None = None):
        security_policy = get_config().get_security_policy(self.backend_type.value)
        # OS-specific blocked commands
        self.security_manager.set_backend_policy(BackendType.SHELL, security_policy)
    
    async def create_session(self, session_config: SessionConfig) -> ShellSession:
        mode = getattr(shell_config, "mode", "local")
        
        if mode == "local":
            connector = LocalShellConnector(security_manager=self.security_manager)
        else:
            connector = ShellConnector(vm_ip=..., port=..., security_manager=self.security_manager)
```

**安全特性**：
- Token 级命令过滤：使用 `shlex.split` 防止空格/转义绕过
- OS 特定黑名单：支持 Linux/macOS/Windows 不同命令限制
- 沙箱模式：可选的隔离执行环境

#### GUI Provider

OpenSpace/openspace/grounding/backends/gui/provider.py 提供桌面 GUI 操作能力：

```python
class GUIProvider(Provider):
    """Provider for GUI desktop environment."""
    
    async def create_session(self, session_config: SessionConfig) -> BaseSession:
        mode = getattr(gui_config, "mode", "local")
        
        if mode == "local":
            connector = LocalGUIConnector(...)  # 直接进程内执行
        else:
            connector = GUIConnector(vm_ip=..., server_port=...)  # HTTP API
```

**支持两种模式**：
- **Local 模式**：直接在进程内执行 GUI 操作，无需服务器
- **Server 模式**：通过 HTTP API 连接 local_server

### 2.4 工具抽象

OpenSpace/openspace/grounding/core/tool/base.py 定义了统一的工具接口：

```python
class BaseTool(ABC):
    _name: ClassVar[str] = ""
    _description: ClassVar[str] = ""
    backend_type: ClassVar[BackendType] = BackendType.NOT_SET

    def __init__(self, schema: Optional[ToolSchema] = None, *, verbose: bool = False):
        self.schema: ToolSchema = schema or ToolSchema(
            name=self._name or self.__class__.__name__.lower(),
            description=self._description,
            parameters=self.get_parameters_schema(),
        )
        self._runtime_info: Optional[ToolRuntimeInfo] = None

    @classmethod
    @lru_cache
    def get_parameters_schema(cls) -> Dict[str, Any]:
        """Auto-generate JSON-schema from _run() or _arun() signature."""
        sig_src = cls._arun if cls._arun is not BaseTool._arun else cls._run
        sig = inspect.signature(sig_src)
        # ... 自动生成参数 schema
```

**设计亮点**：
- **自动 Schema 生成**：从方法签名自动生成 JSON Schema
- **运行时绑定**：ToolRuntimeInfo 携带 backend、session、server 等上下文
- **统一结果类型**：ToolResult 封装成功/错误状态和执行时间

---

## 三、Skill Engine：知识注入与进化系统

### 3.1 技能系统概述

OpenSpace 的 Skill Engine 是其最具创新性的部分。它实现了：

1. **技能发现与加载**：从文件系统自动发现 SKILL.md 文件
2. **智能选择**：基于 BM25 + Embedding 的混合检索
3. **质量追踪**：记录技能的使用效果
4. **自动进化**：从执行中学习，生成/改进技能

### 3.2 SkillRegistry：技能注册与发现

OpenSpace/openspace/skill_engine/registry.py 负责技能的发现、加载和选择：

```python
class SkillRegistry:
    """Discover, load, select, and inject skills into agent context."""
    
    def __init__(self, skill_dirs: Optional[List[Path]] = None) -> None:
        self._skill_dirs: List[Path] = skill_dirs or []
        self._skills: Dict[str, SkillMeta] = {}     # skill_id -> SkillMeta
        self._content_cache: Dict[str, str] = {}    # skill_id -> SKILL.md content
        self._ranker: Optional[SkillRanker] = None  # 延迟初始化
    
    def discover(self) -> List[SkillMeta]:
        """Scan all skill_dirs and populate the registry."""
        for skill_dir in self._skill_dirs:
            for skill_path in skill_dir.rglob("SKILL.md"):
                skill_meta = self._parse_skill_file(skill_path)
                self._skills[skill_meta.skill_id] = skill_meta
```

**技能格式**：

```markdown
---
name: git-commit-guide
description: Guide for creating semantic git commits
category: workflow
tags: [git, version-control]
tools: [shell]
---

# Git Commit Guide

## When to use
- After completing a logical unit of work
- Before pushing changes

## Steps
1. Stage changes: `git add <files>`
2. Create commit with semantic message
3. Verify commit history
```

### 3.3 SkillRanker：混合检索

OpenSpace/openspace/skill_engine/skill_ranker.py 实现了两阶段检索：

```python
class SkillRanker:
    """Hybrid BM25 + embedding ranker for skills."""
    
    def hybrid_rank(self, query: str, candidates: List[SkillCandidate], top_k: int = 10):
        """BM25 rough-rank → embedding re-rank → return top_k."""
        
        # Stage 1: BM25 rough-rank
        bm25_top = self._bm25_rank(query, candidates, top_k * 3)
        
        # Stage 2: Embedding re-rank
        emb_results = self._embedding_rank(query, bm25_top, top_k)
        
        return emb_results or bm25_top[:top_k]
```

**检索策略**：
- **BM25 阶段**：快速词法匹配，过滤大量无关技能
- **Embedding 阶段**：语义重排，提高相关性
- **缓存机制**：Embedding 结果持久化，跨会话复用

### 3.4 SkillStore：持久化存储

OpenSpace/openspace/skill_engine/store.py 使用 SQLite 存储技能元数据和进化记录：

```python
class SkillStore:
    """SQLite persistence engine — Skill quality tracking and evolution ledger."""
    
    # 数据库表结构
    _DDL = """
    CREATE TABLE IF NOT EXISTS skill_records (
        skill_id               TEXT PRIMARY KEY,
        name                   TEXT NOT NULL,
        category               TEXT NOT NULL DEFAULT 'workflow',
        lineage_origin         TEXT NOT NULL DEFAULT 'imported',
        lineage_generation     INTEGER NOT NULL DEFAULT 0,
        total_selections       INTEGER NOT NULL DEFAULT 0,
        total_applied          INTEGER NOT NULL DEFAULT 0,
        total_completions      INTEGER NOT NULL DEFAULT 0,
        ...
    );
    
    CREATE TABLE IF NOT EXISTS execution_analyses (
        task_id                 TEXT NOT NULL UNIQUE,
        task_completed          INTEGER NOT NULL DEFAULT 0,
        evolution_suggestions   TEXT NOT NULL DEFAULT '[]',
        ...
    );
    """
```

**关键表**：
- `skill_records`：技能主表，包含元数据和统计信息
- `skill_lineage_parents`：技能进化谱系（多对多）
- `execution_analyses`：执行分析记录
- `skill_judgments`：单次任务中的技能评估

### 3.5 SkillEvolver：技能进化

OpenSpace/openspace/skill_engine/evolver.py 实现了三种进化类型：

```python
class EvolutionType(str, Enum):
    FIX      = "fix"       # 修复损坏/过时的技能
    DERIVED  = "derived"   # 从现有技能派生/增强
    CAPTURED = "captured"  # 捕获新的可复用模式

class SkillEvolver:
    async def evolve(self, ctx: EvolutionContext) -> Optional[SkillRecord]:
        """Execute one evolution action."""
        if evo_type == EvolutionType.FIX:
            return await self._evolve_fix(ctx)
        elif evo_type == EvolutionType.DERIVED:
            return await self._evolve_derived(ctx)
        elif evo_type == EvolutionType.CAPTURED:
            return await self._evolve_captured(ctx)
```

**进化类型详解**：

| 类型 | 场景 | 父节点 | 示例 |
|------|------|--------|------|
| FIX | 技能指令过时/错误 | 1个父节点 | "修复 curl 参数格式" |
| DERIVED | 组合/增强现有技能 | 1+个父节点 | "组合天气+地理编码" |
| CAPTURED | 发现新的可复用模式 | 无父节点 | "捕获新的调试流程" |

**版本 DAG 模型**：

```
IMPORTED (root) ──┬──> FIXED v1 ──> FIXED v2 ──> FIXED v3
                  │
                  └──> DERIVED (composed with another skill)
                          
CAPTURED (root) ──────> DERIVED (enhanced)
```

### 3.6 ExecutionAnalyzer：执行分析

OpenSpace/openspace/skill_engine/analyzer.py 在任务完成后进行分析：

```python
class ExecutionAnalyzer:
    """Analyzes task execution results and tracks skill quality."""
    
    async def analyze_execution(
        self,
        task_id: str,
        recording_dir: str,
        execution_result: Dict[str, Any],
    ) -> Optional[ExecutionAnalysis]:
        """Run LLM analysis on a completed task and persist the result."""
        
        # 1. 加载执行轨迹
        trajectory = self._load_trajectory(recording_dir)
        
        # 2. LLM 分析
        analysis = await self._run_llm_analysis(trajectory, execution_result)
        
        # 3. 更新技能质量统计
        for judgment in analysis.skill_judgments:
            self._store.update_skill_stats(judgment.skill_id, judgment.skill_applied)
        
        # 4. 返回进化建议
        return analysis
```

**分析输出**：
- 任务是否完成
- 每个选中技能是否被正确应用
- 工具问题列表
- 进化建议（FIX/DERIVED/CAPTURED）

---

## 四、Tool Quality：质量感知系统

### 4.1 ToolQualityManager

OpenSpace/openspace/grounding/core/quality/manager.py 追踪工具执行质量：

```python
class ToolQualityManager:
    """Manages tool quality tracking and quality-aware ranking."""
    
    def __init__(self, db_path: Optional[Path] = None, evolve_interval: int = 5):
        self._records: Dict[str, ToolQualityRecord] = {}
        self._store = QualityStore(db_path=db_path)
        
    def record_execution(self, tool: "BaseTool", result: "ToolResult"):
        """Record tool execution result."""
        record = self.get_record(tool)
        record.total_calls += 1
        if result.is_success:
            record.successful_calls += 1
        record.avg_latency = (record.avg_latency * (record.total_calls - 1) + latency) / record.total_calls
```

**质量指标**：
- 成功率：`successful_calls / total_calls`
- 平均延迟：指数移动平均
- 描述质量：LLM 评估（可选）

### 4.2 与工具选择集成

质量数据被集成到工具搜索中：

```python
class SearchCoordinator:
    async def search_tools(self, query: str, top_k: int = 10) -> List[BaseTool]:
        # 1. 语义搜索
        candidates = await self._semantic_search(query)
        
        # 2. 质量调整排序
        if self._quality_manager:
            for tool in candidates:
                quality_score = self._quality_manager.get_quality_score(tool)
                tool._ranking_score *= (0.7 + 0.3 * quality_score)  # 质量加权
```

---

## 五、安全与隔离

### 5.1 SecurityPolicy

OpenSpace/openspace/grounding/core/types.py 定义了安全策略：

```python
class SecurityPolicy(BaseEntity):
    allow_shell_commands: bool = True
    allow_network_access: bool = True
    allow_file_access: bool = True
    allowed_domains: List[str] = []
    blocked_commands: List[str] = []
    sandbox_enabled: bool = False
    
    def check(self, *, command: str | None = None, domain: str | None = None) -> bool:
        """return True if allowed, False if denied."""
        if command:
            tokens = [t.lower() for t in shlex.split(command, posix=True)]
            blocked_set = {b.lower() for b in self.blocked_commands}
            if any(tok in blocked_set for tok in tokens):
                return False
        return True
```

**OS 特定黑名单**：

```yaml
blocked_commands:
  common: ["rm", "format"]
  linux: ["dd", "shutdown"]
  darwin: ["diskutil"]
  windows: ["format", "del"]
```

### 5.2 Sandbox 抽象

OpenSpace/openspace/grounding/core/security/sandbox.py 提供沙箱隔离：

```python
class BaseSandbox(ABC):
    @abstractmethod
    async def execute_safe(self, command: str, **kwargs) -> Any:
        pass
    
    @abstractmethod
    def get_connector(self) -> Any:
        pass

class SandboxManager:
    def __init__(self):
        self._sandboxes: Dict[BackendType, BaseSandbox] = {}
    
    async def start_all(self) -> None:
        for sandbox in self._sandboxes.values():
            await sandbox.start()
```

---

## 六、录制与回放

### 6.1 TrajectoryRecorder

OpenSpace/openspace/recording/recorder.py 记录执行轨迹：

```python
class TrajectoryRecorder:
    def __init__(self, task_name: str = "", log_dir: str = "./logs/trajectories"):
        self.trajectory_dir = Path(log_dir) / f"{task_name}_{timestamp}"
        self.steps: List[Dict] = []
        
    async def record_step(
        self,
        backend: str,
        tool: str,
        command: str,
        result: Optional[Dict] = None,
        screenshot: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Record one step operation."""
        step_info = {
            "step": self.step_counter,
            "timestamp": datetime.now().isoformat(),
            "backend": backend,
            "tool": tool,
            "command": command,
            "result": result,
        }
        
        if screenshot:
            screenshot_path = self.screenshots_dir / f"step_{step_num:03d}.png"
            step_info["screenshot"] = f"screenshots/{screenshot_filename}"
        
        self.steps.append(step_info)
        await self._append_to_traj_file(step_info)
```

**输出格式**：
```
logs/trajectories/task_name_20240101_120000/
├── metadata.json          # 任务元数据
├── traj.jsonl             # 步骤轨迹（流式写入）
└── screenshots/           # 截图目录
    ├── step_001.png
    ├── step_002.png
    └── ...
```

---

## 七、LLM 集成

### 7.1 LLMClient

OpenSpace/openspace/llm/client.py 基于 LiteLLM 提供统一的 LLM 调用：

```python
def _prepare_tools_for_llmclient(
    tools: List[BaseTool] | None,
    fmt: str = "openai",
) -> tuple[Sequence[Union[ToolSchema, ChatCompletionToolParam]], Dict[str, BaseTool]]:
    """Convert BaseTool list to LLMClient usable format, with deduplication."""
    
    for tool in tools:
        # 重命名冲突工具
        if name_count[original_name] > 1:
            llm_name = f"{server_name}__{original_name}"
        
        # 添加后端标签
        if backend_type:
            desc = f"[{backend_type.value.upper()}] {tool.schema.description}"
```

**Schema 兼容性处理**：
- 自动修复空对象 Schema
- 移除非标准字段（如 `title`）
- Claude API 兼容性适配

---

## 八、与 OpenHarness 的对比

| 维度 | OpenHarness | OpenSpace |
|------|-------------|-----------|
| **定位** | Agent 内核/框架 | 全栈解决方案 |
| **后端支持** | 单一 Shell | MCP/Shell/GUI/Web/System |
| **技能系统** | 简单 Skill 加载 | 完整进化系统 |
| **质量追踪** | 无 | ToolQualityManager |
| **安全模型** | 权限检查 | 多层安全策略 + 沙箱 |
| **录制系统** | 无 | 完整轨迹录制 |
| **适用场景** | 快速原型/研究 | 生产环境部署 |

---

## 九、最佳实践

### 9.1 技能设计原则

1. **单一职责**：每个技能专注一个明确的任务
2. **清晰触发条件**：When to use 部分要具体
3. **工具依赖声明**：明确列出所需工具
4. **版本控制**：技能文件纳入 Git 管理

### 9.2 后端选择策略

```python
# 优先使用 MCP 扩展生态
backend_priority = [
    BackendType.MCP,     # 丰富的第三方工具
    BackendType.SHELL,   # 系统命令
    BackendType.GUI,     # 桌面操作
    BackendType.WEB,     # 网页交互
]
```

### 9.3 质量监控

```python
# 定期执行质量进化
async def maintenance_cycle():
    quality_report = grounding_client.get_quality_report()
    if quality_report["low_quality_tools"]:
        await grounding_client.evolve_quality()
```

---

## 十、总结

OpenSpace 代表了 Agent 基础设施的下一代演进方向：

1. **多模态 Grounding**：统一抽象多种后端，让 Agent 能够与数字世界的各种系统交互
2. **知识驱动**：Skill 系统让 Agent 能够快速获得领域专业知识
3. **自我进化**：从执行中学习，持续改进技能库
4. **质量感知**：数据驱动的工具选择，提高任务成功率
5. **生产就绪**：完善的安全、录制、监控机制

作为一个 Harness Engineer，OpenSpace 给我最大的启发是：**Agent 系统不应该只是执行任务的工具，而应该是一个能够学习、进化、积累经验的智能体**。这种"边干边学"的能力，正是通向 AGI 的关键一步。

---

## 参考资料

- OpenSpace 源码
- GroundingClient 实现: OpenSpace/openspace/grounding/core/grounding_client.py
- Skill Engine 模块: OpenSpace/openspace/skill_engine/
- Tool Quality 系统: OpenSpace/openspace/grounding/core/quality/
