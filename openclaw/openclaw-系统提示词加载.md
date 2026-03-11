# OpenClaw System Prompt 加载机制详解

## 概述

OpenClaw 采用了一套精心设计的 System Prompt 加载机制，为每次 Agent 运行构建定制化的系统提示。与使用 pi-coding-agent 默认提示不同，OpenClaw 拥有自己完整的提示系统，能够根据运行环境、配置和上下文动态生成最优化的系统提示。

本文将深入分析 OpenClaw 如何加载和构建 System Prompt，包括其架构设计、加载流程、Bootstrap 文件机制、插件扩展等核心内容。

## 核心架构

### 主要组件

OpenClaw 的 System Prompt 加载机制由以下几个核心组件构成：

1. **System Prompt 构建器** (`src/agents/system-prompt.ts`)
   - 核心函数 `buildAgentSystemPrompt()` 负责构建完整的系统提示
   - 支持多种提示模式和配置选项
   - 动态组装各个提示部分

2. **Bootstrap 文件加载器** (`src/agents/bootstrap-files.ts`)
   - 负责加载工作区中的 Bootstrap 文件
   - 处理文件缓存和上下文过滤
   - 支持钩子覆盖机制

3. **工作区管理器** (`src/agents/workspace.ts`)
   - 管理工作区文件系统
   - 提供安全的文件读取接口
   - 处理文件缓存和身份验证

4. **插件钩子系统** (`src/plugins/hooks.ts`)
   - 提供 `before_prompt_build` 钩子
   - 允许插件注入自定义内容
   - 支持动态提示修改

## 提示模式

OpenClaw 支持三种提示模式，根据不同的运行场景自动选择：

### 1. Full 模式（默认）
用于主 Agent 运行，包含所有提示部分：
- 工具列表和描述
- 安全防护指南
- 技能加载说明
- OpenClaw 自更新指南
- 工作区信息
- 文档路径
- Bootstrap 文件内容
- 沙箱信息（如启用）
- 当前日期和时间
- 回复标签语法
- 心跳提示
- 运行时信息
- 推理格式

### 2. Minimal 模式
用于子 Agent，精简提示部分：
- 工具列表和描述
- 安全防护指南
- 工作区信息
- 沙箱信息（如启用）
- 当前日期和时间（如已知）
- 运行时信息
- 注入的上下文（标记为"Subagent Context"）

省略的部分包括：技能、记忆召回、自更新、模型别名、用户身份、回复标签、消息传递、静默回复、心跳。

### 3. None 模式
仅返回基础身份行：
```
You are a personal assistant running inside OpenClaw.
```

## 加载流程

### 完整加载流程

```
1. 运行时初始化
   ↓
2. 确定 Prompt Mode（full/minimal/none）
   ↓
3. 加载 Bootstrap 文件
   ├─ 读取工作区文件
   ├─ 应用上下文模式过滤
   ├─ 执行 agent:bootstrap 钩子
   └─ 应用文件截断和警告
   ↓
4. 收集运行时信息
   ├─ Agent ID、主机、操作系统
   ├─ Node 版本、模型信息
   ├─ 工作区路径、仓库根目录
   └─ 渠道和能力配置
   ↓
5. 构建工具列表
   ├─ 核心工具摘要
   ├─ 外部工具摘要
   └─ 工具可用性过滤
   ↓
6. 执行 before_prompt_build 钩子
   ├─ 插件注入 prependContext
   ├─ 插件修改 systemPrompt
   ├─ 插件添加 prependSystemContext
   └─ 插件添加 appendSystemContext
   ↓
7. 组装提示部分
   ├─ 基础身份声明
   ├─ 工具和工具调用风格
   ├─ 安全防护
   ├─ 技能和记忆
   ├─ 工作区和文档
   ├─ Bootstrap 文件内容
   ├─ 运行时信息
   └─ 其他配置部分
   ↓
8. 生成最终 System Prompt
```

### 关键步骤详解

#### 步骤 1：运行时初始化

在每次 Agent 运行开始时，OpenClaw 会初始化运行时上下文：

```typescript
const runtimeInfo = {
  agentId: "default",
  host: "localhost",
  os: "linux",
  arch: "x64",
  node: "22.0.0",
  model: "claude-3-5-sonnet-20241022",
  defaultModel: "claude-3-5-sonnet-20241022",
  shell: "/bin/bash",
  repoRoot: "/path/to/repo",
  channel: "telegram",
  capabilities: ["inlineButtons", "reactions"]
};
```

#### 步骤 2：确定 Prompt Mode

根据运行类型自动选择提示模式：

```typescript
const promptMode = isSubagent ? "minimal" : "full";
const isMinimal = promptMode === "minimal" || promptMode === "none";
```

#### 步骤 3：加载 Bootstrap 文件

Bootstrap 文件加载是 System Prompt 构建的关键环节：

```typescript
// 定义默认的 Bootstrap 文件
const DEFAULT_AGENTS_FILENAME = "AGENTS.md";
const DEFAULT_SOUL_FILENAME = "SOUL.md";
const DEFAULT_TOOLS_FILENAME = "TOOLS.md";
const DEFAULT_IDENTITY_FILENAME = "IDENTITY.md";
const DEFAULT_USER_FILENAME = "USER.md";
const DEFAULT_HEARTBEAT_FILENAME = "HEARTBEAT.md";
const DEFAULT_BOOTSTRAP_FILENAME = "BOOTSTRAP.md";
const DEFAULT_MEMORY_FILENAME = "MEMORY.md";
const DEFAULT_MEMORY_ALT_FILENAME = "memory.md";

// 加载函数
export async function loadWorkspaceBootstrapFiles(dir: string): Promise<WorkspaceBootstrapFile[]> {
  const files: WorkspaceBootstrapFile[] = [];

  // 尝试加载每个 Bootstrap 文件
  for (const filename of bootstrapFilenames) {
    const filePath = path.join(dir, filename);
    const result = await readWorkspaceFileWithGuards({
      filePath,
      workspaceDir: dir
    });

    if (result.ok) {
      files.push({
        name: filename,
        path: filePath,
        content: result.content
      });
    }
  }

  return files;
}
```

**安全机制**：
- 使用边界文件读取器防止路径遍历攻击
- 文件大小限制（默认 2MB）
- 文件内容缓存（基于 inode/dev/size/mtime）
- 前置元数据（front matter）自动移除

**上下文过滤**：
```typescript
function applyContextModeFilter(params: {
  files: WorkspaceBootstrapFile[];
  contextMode?: BootstrapContextMode;
  runKind?: BootstrapContextRunKind;
}): WorkspaceBootstrapFile[] {
  const contextMode = params.contextMode ?? "full";
  const runKind = params.runKind ?? "default";

  if (contextMode !== "lightweight") {
    return params.files;
  }

  if (runKind === "heartbeat") {
    return params.files.filter(file => file.name === "HEARTBEAT.md");
  }

  // cron/default lightweight mode keeps bootstrap context empty
  return [];
}
```

**钩子覆盖**：
```typescript
const updated = await applyBootstrapHookOverrides({
  files: bootstrapFiles,
  workspaceDir: params.workspaceDir,
  config: params.config,
  sessionKey: params.sessionKey,
  sessionId: params.sessionId,
  agentId: params.agentId
});
```

#### 步骤 4：收集运行时信息

运行时信息包括：
- Agent 标识符
- 主机和操作系统信息
- Node.js 版本
- 当前使用的模型
- 工作区路径
- Git 仓库根目录（如检测到）
- Shell 类型
- 渠道标识符
- 运行时能力（如内联按钮、反应等）

#### 步骤 5：构建工具列表

工具列表构建过程：

```typescript
// 核心工具摘要
const coreToolSummaries: Record<string, string> = {
  read: "Read file contents",
  write: "Create or overwrite files",
  edit: "Make precise edits to files",
  apply_patch: "Apply multi-file patches",
  grep: "Search file contents for patterns",
  find: "Find files by glob pattern",
  ls: "List directory contents",
  exec: "Run shell commands (pty available for TTY-required CLIs)",
  process: "Manage background exec sessions",
  web_search: "Search the web (Brave API)",
  web_fetch: "Fetch and extract readable content from a URL",
  browser: "Control web browser",
  canvas: "Present/eval/snapshot the Canvas",
  nodes: "List/describe/notify/camera/screen on paired nodes",
  cron: "Manage cron jobs and wake events",
  message: "Send messages and channel actions",
  gateway: "Restart, apply config, or run updates on the running OpenClaw process",
  agents_list: "List OpenClaw agent ids allowed for sessions_spawn",
  sessions_list: "List other sessions (incl. sub-agents) with filters/last",
  sessions_history: "Fetch history for another session/sub-agent",
  sessions_send: "Send a message to another session/sub-agent",
  sessions_spawn: "Spawn an isolated sub-agent session",
  subagents: "List, steer, or kill sub-agent runs for this requester session",
  session_status: "Show a /status-equivalent status card",
  image: "Analyze an image with the configured image model"
};

// 工具可用性过滤
const availableTools = new Set(normalizedTools);
const enabledTools = toolOrder.filter(tool => availableTools.has(tool));

// 生成工具行
const toolLines = enabledTools.map(tool => {
  const summary = coreToolSummaries[tool] ?? externalToolSummaries.get(tool);
  const name = resolveToolName(tool);
  return summary ? `- ${name}: ${summary}` : `- ${name}`;
});
```

#### 步骤 6：执行 before_prompt_build 钩子

插件可以通过 `before_prompt_build` 钩子注入自定义内容：

```typescript
// 钩子事件类型
export type PluginHookBeforePromptBuildEvent = {
  prompt: string;
  messages: unknown[];
};

export type PluginHookBeforePromptBuildResult = {
  systemPrompt?: string;
  prependContext?: string;
  prependSystemContext?: string;
  appendSystemContext?: string;
};

// 钩子执行
const hookResult = await runPluginHook<PluginHookBeforePromptBuildResult>(
  "before_prompt_build",
  {
    prompt: userPrompt,
    messages: sessionMessages
  }
);

// 应用钩子结果
if (hookResult.prependContext) {
  extraSystemPrompt += hookResult.prependContext;
}
if (hookResult.systemPrompt) {
  systemPrompt = hookResult.systemPrompt;
}
if (hookResult.prependSystemContext) {
  systemPrompt = hookResult.prependSystemContext + systemPrompt;
}
if (hookResult.appendSystemContext) {
  systemPrompt += hookResult.appendSystemContext;
}
```

#### 步骤 7：组装提示部分

System Prompt 由多个固定部分组成，按顺序组装：

```typescript
const lines = [
  // 1. 基础身份
  "You are a personal assistant running inside OpenClaw.",

  // 2. 工具部分
  "## Tooling",
  "Tool availability (filtered by policy):",
  toolLines.join("\n"),

  // 3. 工具调用风格
  "## Tool Call Style",
  "Default: do not narrate routine, low-risk tool calls (just call the tool).",
  "Narrate only when it helps...",

  // 4. 安全防护
  "## Safety",
  "You have no independent goals: do not pursue self-preservation...",

  // 5. OpenClaw CLI 快速参考
  "## OpenClaw CLI Quick Reference",
  "OpenClaw is controlled via subcommands...",

  // 6. 技能（如有）
  ...buildSkillsSection({ skillsPrompt, readToolName }),

  // 7. 记忆召回（如有）
  ...buildMemorySection({ isMinimal, availableTools, citationsMode }),

  // 8. 自更新（主 Agent）
  "## OpenClaw Self-Update",
  "Get Updates (self-update) is ONLY allowed when the user explicitly asks...",

  // 9. 模型别名（如有）
  "## Model Aliases",
  modelAliasLines.join("\n"),

  // 10. 工作区
  "## Workspace",
  `Your working directory is: ${displayWorkspaceDir}`,
  workspaceGuidance,

  // 11. 文档
  ...buildDocsSection({ docsPath, isMinimal, readToolName }),

  // 12. 沙箱（如启用）
  "## Sandbox",
  "You are running in a sandboxed runtime...",

  // 13. 用户身份（如有）
  ...buildUserIdentitySection(ownerLine, isMinimal),

  // 14. 时间（如已知）
  ...buildTimeSection({ userTimezone }),

  // 15. 工作区文件
  "## Workspace Files (injected)",
  "These user-editable files are loaded by OpenClaw...",

  // 16. 回复标签（主 Agent）
  ...buildReplyTagsSection(isMinimal),

  // 17. 消息传递（主 Agent）
  ...buildMessagingSection({ isMinimal, availableTools, ... }),

  // 18. 语音（主 Agent）
  ...buildVoiceSection({ isMinimal, ttsHint }),

  // 19. 组上下文
  "## Group Chat Context",
  extraSystemPrompt,

  // 20. 项目上下文（Bootstrap 文件）
  "# Project Context",
  ...contextFiles.map(file => `## ${file.path}\n\n${file.content}`),

  // 21. 静默回复（主 Agent）
  "## Silent Replies",
  `When you have nothing to say, respond with ONLY: ${SILENT_REPLY_TOKEN}`,

  // 22. 心跳（主 Agent）
  "## Heartbeats",
  heartbeatPromptLine,

  // 23. 运行时
  "## Runtime",
  buildRuntimeLine(runtimeInfo, runtimeChannel, runtimeCapabilities),
  `Reasoning: ${reasoningLevel}`
];

return lines.filter(Boolean).join("\n");
```

## Bootstrap 文件机制

### 文件类型和用途

1. **AGENTS.md**
   - 定义 Agent 列表和配置
   - 指定每个 Agent 的用途和权限
   - 控制子 Agent 的生成规则

2. **SOUL.md**
   - 定义 Agent 的个性和语气
   - 指导 Agent 的行为风格
   - 提供角色扮演指导

3. **TOOLS.md**
   - 描述外部工具的使用方法
   - 提供工具集成的最佳实践
   - 不控制工具可用性，仅提供用户指导

4. **IDENTITY.md**
   - 定义 Agent 的身份信息
   - 包含名称、主题、表情符号、头像等
   - 通过 `openclaw agents set-identity` 命令管理

5. **USER.md**
   - 描述用户偏好和习惯
   - 提供个性化指导
   - 帮助 Agent 更好地理解用户需求

6. **HEARTBEAT.md**
   - 定义心跳检查的行为
   - 指导 Agent 如何处理定期检查
   - 用于后台任务和提醒

7. **BOOTSTRAP.md**
   - 仅在新工作区中创建
   - 提供初始设置指导
   - 包含项目特定的引导信息

8. **MEMORY.md / memory.md**
   - 存储长期记忆和重要信息
   - 可以增长很大，导致上下文使用增加
   - 通过 `memory_search` 和 `memory_get` 工具按需访问

### 文件加载规则

```typescript
// 主 Agent：加载所有 Bootstrap 文件
if (!isSubagent) {
  bootstrapFiles = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "IDENTITY.md",
    "USER.md",
    "HEARTBEAT.md",
    "BOOTSTRAP.md",
    "MEMORY.md",
    "memory.md"
  ];
}

// 子 Agent：仅加载 AGENTS.md 和 TOOLS.md
if (isSubagent) {
  bootstrapFiles = [
    "AGENTS.md",
    "TOOLS.md"
  ];
}

// 心跳运行：仅加载 HEARTBEAT.md（lightweight 模式）
if (runKind === "heartbeat" && contextMode === "lightweight") {
  bootstrapFiles = ["HEARTBEAT.md"];
}
```

### 文件大小限制

```typescript
// 单文件大小限制
const MAX_WORKSPACE_BOOTSTRAP_FILE_BYTES = 2 * 1024 * 1024; // 2MB

// 注入大小限制
const bootstrapMaxChars = 20000; // 每个文件最多 20,000 字符
const bootstrapTotalMaxChars = 150000; // 总共最多 150,000 字符

// 截断警告模式
const bootstrapPromptTruncationWarning = "once"; // "off" | "once" | "always"
```

### 文件缓存机制

```typescript
// 文件内容缓存
const workspaceFileCache = new Map<string, {
  content: string;
  identity: string
}>();

// 文件身份标识
function workspaceFileIdentity(stat: Stats, canonicalPath: string): string {
  return `${canonicalPath}|${stat.dev}:${stat.ino}:${stat.size}:${stat.mtimeMs}`;
}

// 带缓存的读取
async function readWorkspaceFileWithGuards(params: {
  filePath: string;
  workspaceDir: string;
}): Promise<WorkspaceGuardedReadResult> {
  const identity = workspaceFileIdentity(opened.stat, opened.path);
  const cached = workspaceFileCache.get(filePath);

  if (cached && cached.identity === identity) {
    return { ok: true, content: cached.content };
  }

  const content = syncFs.readFileSync(opened.fd, "utf-8");
  workspaceFileCache.set(filePath, { content, identity });
  return { ok: true, content };
}
```

## 插件扩展机制

### 钩子类型

OpenClaw 提供多个钩子点用于扩展 System Prompt：

#### 1. before_model_resolve
在模型解析之前运行，可以覆盖模型和提供者：

```typescript
export type PluginHookBeforeModelResolveEvent = {
  prompt: string;
};

export type PluginHookBeforeModelResolveResult = {
  modelOverride?: string;
  providerOverride?: string;
};
```

#### 2. before_prompt_build
在提示构建之前运行，可以注入自定义内容：

```typescript
export type PluginHookBeforePromptBuildEvent = {
  prompt: string;
  messages: unknown[];
};

export type PluginHookBeforePromptBuildResult = {
  systemPrompt?: string;
  prependContext?: string;
  prependSystemContext?: string;
  appendSystemContext?: string;
};
```

#### 3. agent:bootstrap
在 Bootstrap 文件加载时运行，可以修改或替换文件：

```typescript
// 内部钩子
export type AgentBootstrapHookEvent = {
  workspaceDir: string;
  sessionKey?: string;
  sessionId?: string;
  agentId?: string;
  files: WorkspaceBootstrapFile[];
};

export type AgentBootstrapHookResult = {
  files?: WorkspaceBootstrapFile[];
};
```

### 插件示例

```typescript
// 插件：添加自定义系统提示
export default {
  name: "custom-system-prompt",
  version: "1.0.0",
  hooks: {
    before_prompt_build: async (event) => {
      return {
        prependSystemContext: `
## Custom Guidelines

- Always respond in a friendly tone
- Use emojis when appropriate
- Ask clarifying questions when needed
        `.trim()
      };
    }
  }
};

// 插件：修改 Bootstrap 文件
export default {
  name: "bootstrap-modifier",
  version: "1.0.0",
  hooks: {
    "agent:bootstrap": async (event) => {
      const files = event.files.map(file => {
        if (file.name === "SOUL.md") {
          return {
            ...file,
            content: `
## Enhanced Persona

${file.content}

Additional traits:
- Be more creative and innovative
- Think outside the box
- Suggest unconventional solutions
            `.trim()
          };
        }
        return file;
      });

      return { files };
    }
  }
};
```

## 技能加载机制

### 技能列表注入

当有可用技能时，OpenClaw 会注入一个紧凑的技能列表：

```typescript
function buildSkillsSection(params: {
  skillsPrompt?: string;
  readToolName: string;
}): string[] {
  const trimmed = params.skillsPrompt?.trim();
  if (!trimmed) {
    return [];
  }

  return [
    "## Skills (mandatory)",
    "Before replying: scan <available_skills> <description> entries.",
    `- If exactly one skill clearly applies: read its SKILL.md at <location> with \`${params.readToolName}\`, then follow it.`,
    "- If multiple could apply: choose the most specific one, then read/follow it.",
    "- If none clearly apply: do not read any SKILL.md.",
    "Constraints: never read more than one skill up front; only read after selecting.",
    "- When a skill drives external API writes, assume rate limits: prefer fewer larger writes, avoid tight one-item loops, serialize bursts when possible, and respect 429/Retry-After.",
    trimmed,
    ""
  ];
}
```

### 技能列表格式

```
<available_skills>
  <skill>
    <name>github</name>
    <description>GitHub repository management and operations</description>
    <location>/path/to/skills/github/SKILL.md</location>
  </skill>
  <skill>
    <name>notion</name>
    <description>Notion database and page management</description>
    <location>/path/to/skills/notion/SKILL.md</location>
  </skill>
</available_skills>
```

### 技能加载策略

这种设计保持了基础提示的小巧，同时仍然支持有针对性的技能使用：

1. **延迟加载**：技能文件不会预先加载到上下文中
2. **按需读取**：Agent 只在需要时读取 SKILL.md
3. **智能选择**：Agent 根据描述选择最相关的技能
4. **单一限制**：每次只读取一个技能文件

## 记忆召回机制

### 记忆工具集成

当可用工具包含 `memory_search` 或 `memory_get` 时，System Prompt 会包含记忆召回部分：

```typescript
function buildMemorySection(params: {
  isMinimal: boolean;
  availableTools: Set<string>;
  citationsMode?: MemoryCitationsMode;
}): string[] {
  if (isMinimal) {
    return [];
  }

  if (!params.availableTools.has("memory_search") &&
      !params.availableTools.has("memory_get")) {
    return [];
  }

  const lines = [
    "## Memory Recall",
    "Before answering anything about prior work, decisions, dates, people, preferences, or todos: run memory_search on MEMORY.md + memory/*.md; then use memory_get to pull only the needed lines. If low confidence after search, say you checked."
  ];

  if (params.citationsMode === "off") {
    lines.push(
      "Citations are disabled: do not mention file paths or line numbers in replies unless the user explicitly asks."
    );
  } else {
    lines.push(
      "Citations: include Source: <path#line> when it helps the user verify memory snippets."
    );
  }

  lines.push("");
  return lines;
}
```

### 记忆文件处理

- **MEMORY.md / memory.md**：主记忆文件，会被注入到上下文中
- **memory/*.md**：每日记忆文件，按需访问，不自动注入
- **大小控制**：由于 MEMORY.md 可以增长很大，建议保持简洁

## 时间处理

### 时区配置

```typescript
// 配置选项
const userTimezone = "Asia/Shanghai"; // IANA 时区标识符
const timeFormat = "auto"; // "auto" | "12" | "24"
```

### 时间部分构建

```typescript
function buildTimeSection(params: { userTimezone?: string }): string[] {
  if (!params.userTimezone) {
    return [];
  }

  return [
    "## Current Date & Time",
    `Time zone: ${params.userTimezone}`,
    ""
  ];
}
```

### 时间获取

为了保持提示缓存稳定，时间部分现在只包含时区信息，不包含动态时钟。当 Agent 需要当前时间时，使用 `session_status` 工具：

```
If you need the current date, time, or day of week, run session_status (📊 session_status).
```

## 沙箱支持

### 沙箱信息注入

当启用沙箱时，System Prompt 会包含沙箱相关信息：

```typescript
if (params.sandboxInfo?.enabled) {
  lines.push(
    "## Sandbox",
    "You are running in a sandboxed runtime (tools execute in Docker).",
    "Some tools may be unavailable due to sandbox policy.",
    "Sub-agents stay sandboxed (no elevated/host access). Need outside-sandbox read/write? Don't spawn; ask first.",
    `Sandbox container workdir: ${sanitizeForPromptLiteral(params.sandboxInfo.containerWorkspaceDir)}`,
    `Sandbox host mount source: ${sanitizeForPromptLiteral(params.sandboxInfo.workspaceDir)}`,
    `Agent workspace access: ${params.sandboxInfo.workspaceAccess}`,
    `Sandbox browser: ${params.sandboxInfo.browserBridgeUrl ? "enabled" : "disabled"}`,
    `Host browser control: ${params.sandboxInfo.hostBrowserAllowed ? "allowed" : "blocked"}`,
    `Elevated exec is ${params.sandboxInfo.elevated?.allowed ? "available" : "unavailable"}`,
    `Current elevated level: ${params.sandboxInfo.elevated?.defaultLevel}`
  );
}
```

### 沙箱路径处理

沙箱环境下，文件工具和执行工具使用不同的路径：

```typescript
const workspaceGuidance = params.sandboxInfo?.enabled && sanitizedSandboxContainerWorkspace
  ? `For read/write/edit/apply_patch, file paths resolve against host workspace: ${sanitizedWorkspaceDir}. For bash/exec commands, use sandbox container paths under ${sanitizedSandboxContainerWorkspace} (or relative paths from that workdir), not host paths. Prefer relative paths so both sandboxed exec and file tools work consistently.`
  : "Treat this directory as the single global workspace for file operations unless explicitly instructed otherwise.";
```

## 运行时信息

### 运行时行构建

```typescript
export function buildRuntimeLine(
  runtimeInfo?: {
    agentId?: string;
    host?: string;
    os?: string;
    arch?: string;
    node?: string;
    model?: string;
    defaultModel?: string;
    shell?: string;
    repoRoot?: string;
  },
  runtimeChannel?: string,
  runtimeCapabilities: string[] = [],
  defaultThinkLevel?: ThinkLevel,
): string {
  return `Runtime: ${[
    runtimeInfo?.agentId ? `agent=${runtimeInfo.agentId}` : "",
    runtimeInfo?.host ? `host=${runtimeInfo.host}` : "",
    runtimeInfo?.repoRoot ? `repo=${runtimeInfo.repoRoot}` : "",
    runtimeInfo?.os ? `os=${runtimeInfo.os}${runtimeInfo?.arch ? ` (${runtimeInfo.arch})` : ""}` : "",
    runtimeInfo?.node ? `node=${runtimeInfo.node}` : "",
    runtimeInfo?.model ? `model=${runtimeInfo.model}` : "",
    runtimeInfo?.defaultModel ? `default_model=${runtimeInfo.defaultModel}` : "",
    runtimeInfo?.shell ? `shell=${runtimeInfo.shell}` : "",
    runtimeChannel ? `channel=${runtimeChannel}` : "",
    runtimeChannel ? `capabilities=${runtimeCapabilities.length > 0 ? runtimeCapabilities.join(",") : "none"}` : "",
    `thinking=${defaultThinkLevel ?? "off"}`
  ].filter(Boolean).join(" | ")}`;
}
```

### 示例输出

```
Runtime: agent=default | host=localhost | repo=/path/to/repo | os=linux (x64) | node=22.0.0 | model=claude-3-5-sonnet-20241022 | default_model=claude-3-5-sonnet-20241022 | shell=/bin/bash | channel=telegram | capabilities=inlineButtons,reactions | thinking=off
Reasoning: off (hidden unless on/stream). Toggle /reasoning; /status shows Reasoning when enabled.
```

## 安全机制

### 安全防护部分

System Prompt 包含明确的安全指导：

```typescript
const safetySection = [
  "## Safety",
  "You have no independent goals: do not pursue self-preservation, replication, resource acquisition, or power-seeking; avoid long-term plans beyond the user's request.",
  "Prioritize safety and human oversight over completion; if instructions conflict, pause and ask; comply with stop/pause/audit requests and never bypass safeguards. (Inspired by Anthropic's constitution.)",
  "Do not manipulate or persuade anyone to expand access or disable safeguards. Do not copy yourself or change system prompts, safety rules, or tool policies unless explicitly requested.",
  ""
];
```

### 批准机制

当执行需要批准时，Agent 会包含具体的批准命令：

```typescript
"When exec returns approval-pending, include the concrete /approve command from tool output (with allow-once|allow-always|deny) and do not ask for a different or rotated code.",
"Treat allow-once as single-command only: if another elevated command needs approval, request a fresh /approve and do not claim prior approval covered it.",
"When approvals are required, preserve and show the full command/script exactly as provided (including chained operators like &&, ||, |, ;, or multiline shells) so the user can approve what will actually run."
```

## 性能优化

### 缓存策略

1. **文件内容缓存**：基于文件身份（inode/dev/size/mtime）缓存 Bootstrap 文件内容
2. **提示缓存**：保持时间部分稳定（仅包含时区），提高缓存命中率
3. **技能延迟加载**：不预先加载技能文件，按需读取

### 大小控制

1. **单文件限制**：每个 Bootstrap 文件最多 20,000 字符
2. **总大小限制**：所有 Bootstrap 文件总共最多 150,000 字符
3. **截断警告**：可配置的截断警告模式（off/once/always）

### 上下文优化

1. **子 Agent 精简**：子 Agent 仅加载必要的 Bootstrap 文件
2. **Lightweight 模式**：心跳和 cron 运行使用轻量级上下文
3. **技能按需加载**：技能列表紧凑，文件内容按需读取

## 配置选项

### Agent 默认配置

```typescript
{
  agents: {
    defaults: {
      // 工作区
      workspace: "~/.openclaw/workspace",

      // 时间配置
      userTimezone: "Asia/Shanghai",
      timeFormat: "auto", // "auto" | "12" | "24"

      // Bootstrap 配置
      bootstrapMaxChars: 20000,
      bootstrapTotalMaxChars: 150000,
      bootstrapPromptTruncationWarning: "once", // "off" | "once" | "always"
      skipBootstrap: false,

      // 心跳配置
      heartbeat: {
        every: "30m",
        target: "last",
        directPolicy: "allow",
        lightContext: true
      },

      // 记忆配置
      memoryCitationsMode: "on", // "on" | "off"
    }
  }
}
```

### 渠道特定配置

```typescript
{
  channels: {
    telegram: {
      capabilities: {
        inlineButtons: "dm", // "dm" | "group" | "all" | "allowlist"
        reactions: "minimal" // "minimal" | "extensive"
      }
    }
  }
}
```

## 调试和监控

### 上下文报告

使用 `/context list` 或 `/context detail` 命令查看每个注入文件的贡献：

```
/context detail

Bootstrap Files:
- AGENTS.md: 1,234 bytes (raw) → 1,200 bytes (injected)
- SOUL.md: 5,678 bytes (raw) → 5,600 bytes (injected)
- TOOLS.md: 3,456 bytes (raw) → 3,400 bytes (injected)
- IDENTITY.md: 2,345 bytes (raw) → 2,300 bytes (injected)
- USER.md: 4,567 bytes (raw) → 4,500 bytes (injected)
- HEARTBEAT.md: 1,890 bytes (raw) → 1,850 bytes (injected)
- MEMORY.md: 12,345 bytes (raw) → 12,000 bytes (injected) [TRUNCATED]

Total: 31,517 bytes (raw) → 30,850 bytes (injected)

Tool Schema Overhead: 2,500 bytes
System Prompt Base: 8,000 bytes
Total Context: 41,350 bytes
```

### 系统状态

使用 `/status` 命令查看当前运行状态：

```
/status

Runtime: agent=default | host=localhost | os=linux (x64) | node=22.0.0 | model=claude-3-5-sonnet-20241022 | channel=telegram | capabilities=inlineButtons,reactions | thinking=off
Reasoning: off
Context: 41,350 bytes
Bootstrap: 30,850 bytes (7 files)
Skills: 12 available
```

## 最佳实践

### Bootstrap 文件管理

1. **保持简洁**：Bootstrap 文件应该简洁明了，避免冗长
2. **定期清理**：定期清理 MEMORY.md，删除过时信息
3. **使用 SOUL.md**：使用 SOUL.md 定义 Agent 个性，而不是在 System Prompt 中硬编码
4. **版本控制**：将 Bootstrap 文件纳入版本控制

### 插件开发

1. **使用正确的钩子**：
   - 使用 `before_prompt_build` 注入动态内容
   - 使用 `agent:bootstrap` 修改 Bootstrap 文件
   - 使用 `before_model_resolve` 覆盖模型选择

2. **保持性能**：
   - 避免在钩子中执行耗时操作
   - 使用缓存减少重复计算
   - 保持注入内容简洁

3. **文档清晰**：
   - 提供清晰的插件文档
   - 说明钩子的用途和参数
   - 提供使用示例

### 技能开发

1. **描述准确**：提供准确简洁的技能描述
2. **路径正确**：确保 SKILL.md 路径正确
3. **按需加载**：技能文件应该按需加载，不预先注入

## 总结

OpenClaw 的 System Prompt 加载机制是一个精心设计的系统，具有以下特点：

1. **模块化设计**：通过多个组件协同工作，各司其职
2. **灵活配置**：支持多种模式和配置选项
3. **安全可靠**：包含多层安全机制和边界检查
4. **性能优化**：通过缓存、延迟加载等策略优化性能
5. **可扩展性**：通过插件钩子支持灵活扩展
6. **用户友好**：提供清晰的文档和调试工具

这套机制确保了 OpenClaw 能够为每次 Agent 运行生成最优化的 System Prompt，同时保持系统的安全性、性能和可维护性。

通过理解这套机制，开发者可以更好地：
- 配置和定制 OpenClaw 的行为
- 开发高质量的插件和技能
- 优化系统性能和资源使用
- 调试和解决相关问题

OpenClaw 的 System Prompt 加载机制是整个系统的基础，理解它对于深入使用和扩展 OpenClaw 至关重要。