# OpenClaw智能体创建机制

OpenClaw的智能体创建系统是其核心功能之一，允许用户配置和管理多个具有不同特性的AI智能体。本文将详细介绍OpenClaw如何创建、配置和管理智能体。

## 智能体概述

在OpenClaw中，智能体是具有独立配置、工作区和行为特征的AI实体。每个智能体可以：

- 拥有独立的工作区和文件系统
- 配置不同的模型和参数
- 定义个性化的人设和行为
- 绑定到特定的消息渠道
- 使用不同的技能和工具集

## 智能体配置

### 配置文件结构

智能体通过OpenClaw配置文件中的`agents.list`进行定义：

```typescript
interface AgentConfig {
  id: string;                    // 智能体唯一标识符
  name?: string;                 // 智能体显示名称
  workspace?: string;             // 工作区路径
  agentDir?: string;             // 智能体目录路径
  model?: string | {             // 模型配置
    primary?: string;
    fallbacks?: string[];
  };
  skills?: string[];              // 技能过滤列表
  memorySearch?: MemorySearchConfig;
  humanDelay?: HumanDelayConfig;
  heartbeat?: HeartbeatConfig;
  identity?: AgentIdentity;      // 智能体身份
  groupChat?: GroupChatConfig;
  subagents?: SubagentConfig;
  sandbox?: SandboxConfig;
  tools?: AgentToolsConfig;
  default?: boolean;             // 是否为默认智能体
}
```

### 配置示例

```json5
{
  agents: {
    defaults: {
      workspace: "~/.openclaw/workspace",
      model: "claude-3-5-sonnet-20241022",
    },
    list: [
      {
        id: "main",
        name: "主助手",
        default: true,
        workspace: "~/.openclaw/workspace",
        model: "claude-3-5-sonnet-20241022",
        skills: ["weather", "github", "file"],
      },
      {
        id: "coder",
        name: "代码助手",
        workspace: "~/.openclaw/coder-workspace",
        model: "claude-3-5-sonnet-20241022",
        skills: ["github", "file", "test"],
      },
      {
        id: "research",
        name: "研究助手",
        workspace: "~/.openclaw/research-workspace",
        model: "claude-3-opus-20240229",
      },
    ],
  },
}
```

## 智能体工作区

### 工作区结构

每个智能体都有独立的工作区目录，包含以下标准文件：

```
~/.openclaw/workspace/
├── AGENTS.md          # 智能体操作指令和记忆
├── SOUL.md            # 人设、语气和边界
├── TOOLS.md           # 工具使用说明
├── IDENTITY.md        # 智能体身份信息
├── USER.md            # 用户配置文件
├── HEARTBEAT.md       # 心跳任务清单
├── BOOTSTRAP.md       # 首次运行引导（完成后删除）
├── MEMORY.md          # 记忆存储
└── .openclaw/
    └── workspace-state.json  # 工作区状态
```

### 工作区创建

OpenClaw通过`ensureAgentWorkspace`函数自动创建和初始化工作区：

```typescript
export async function ensureAgentWorkspace(params?: {
  dir?: string;
  ensureBootstrapFiles?: boolean;
}): Promise<{
  dir: string;
  agentsPath?: string;
  soulPath?: string;
  toolsPath?: string;
  identityPath?: string;
  userPath?: string;
  heartbeatPath?: string;
  bootstrapPath?: string;
}>
```

**工作区创建流程：**

1. **创建目录结构**：如果工作区目录不存在，则递归创建
2. **初始化引导文件**：从模板复制标准文件到工作区
3. **Git仓库初始化**：如果可用，为新工作区初始化Git仓库
4. **状态管理**：创建和更新工作区状态文件

### 引导文件模板

OpenClaw使用模板系统来初始化工作区文件：

```typescript
async function loadTemplate(name: string): Promise<string> {
  const templateDir = await resolveWorkspaceTemplateDir();
  const templatePath = path.join(templateDir, name);
  const content = await fs.readFile(templatePath, "utf-8");
  return stripFrontMatter(content);
}
```

模板文件位于`docs/reference/templates/`目录，包括：
- `AGENTS.md` - 智能体基本指令模板
- `SOUL.md` - 人设和语气模板
- `TOOLS.md` - 工具使用说明模板
- `IDENTITY.md` - 身份信息模板
- `USER.md` - 用户配置模板
- `HEARTBEAT.md` - 心跳任务模板
- `BOOTSTRAP.md` - 首次运行引导模板

## 智能体身份系统

### 身份文件解析

智能体身份通过`IDENTITY.md`文件定义，包含以下信息：

```markdown
---
name: Claude
emoji: 🤖
creature: AI assistant
vibe: helpful and precise
theme: technology
avatar: https://example.com/avatar.png
---
```

### 身份解析实现

```typescript
export type AgentIdentityFile = {
  name?: string;
  emoji?: string;
  theme?: string;
  creature?: string;
  vibe?: string;
  avatar?: string;
};

export function parseIdentityMarkdown(content: string): AgentIdentityFile {
  const identity: AgentIdentityFile = {};
  const lines = content.split(/\r?\n/);
  
  for (const line of lines) {
    const cleaned = line.trim().replace(/^\s*-\s*/, "");
    const colonIndex = cleaned.indexOf(":");
    
    if (colonIndex === -1) continue;
    
    const label = cleaned.slice(0, colonIndex)
      .replace(/[*_]/g, "")
      .trim()
      .toLowerCase();
    const value = cleaned
      .slice(colonIndex + 1)
      .replace(/[*_]+/g, "")
      .trim();
    
    if (!value || isIdentityPlaceholder(value)) continue;
    
    if (label === "name") identity.name = value;
    if (label === "emoji") identity.emoji = value;
    if (label === "creature") identity.creature = value;
    if (label === "vibe") identity.vibe = value;
    if (label === "theme") identity.theme = value;
    if (label === "avatar") identity.avatar = value;
  }
  
  return identity;
}
```

### 身份加载

```typescript
export function loadAgentIdentityFromWorkspace(
  workspace: string
): AgentIdentityFile | null {
  const identityPath = path.join(workspace, DEFAULT_IDENTITY_FILENAME);
  const parsed = loadIdentityFromFile(identityPath);
  
  if (!parsed) return null;
  return identityHasValues(parsed) ? parsed : null;
}
```

## 智能体配置解析

### 智能体列表管理

```typescript
export function listAgentEntries(cfg: OpenClawConfig): AgentEntry[] {
  const list = cfg.agents?.list;
  if (!Array.isArray(list)) {
    return [];
  }
  return list.filter(
    (entry): entry is AgentEntry => 
      Boolean(entry && typeof entry === "object")
  );
}

export function listAgentIds(cfg: OpenClawConfig): string[] {
  const agents = listAgentEntries(cfg);
  if (agents.length === 0) {
    return [DEFAULT_AGENT_ID];
  }
  
  const seen = new Set<string>();
  const ids: string[] = [];
  
  for (const entry of agents) {
    const id = normalizeAgentId(entry?.id);
    if (seen.has(id)) continue;
    seen.add(id);
    ids.push(id);
  }
  
  return ids.length > 0 ? ids : [DEFAULT_AGENT_ID];
}
```

### 默认智能体解析

```typescript
export function resolveDefaultAgentId(cfg: OpenClawConfig): string {
  const agents = listAgentEntries(cfg);
  if (agents.length === 0) {
    return DEFAULT_AGENT_ID;
  }
  
  const defaults = agents.filter((agent) => agent?.default);
  if (defaults.length > 1 && !defaultAgentWarned) {
    defaultAgentWarned = true;
    log.warn(
      "Multiple agents marked default=true; " +
      "using the first entry as default."
    );
  }
  
  const chosen = (defaults[0] ?? agents[0])?.id?.trim();
  return normalizeAgentId(chosen || DEFAULT_AGENT_ID);
}
```

### 智能体配置解析

```typescript
export function resolveAgentConfig(
  cfg: OpenClawConfig,
  agentId: string,
): ResolvedAgentConfig | undefined {
  const id = normalizeAgentId(agentId);
  const entry = resolveAgentEntry(cfg, id);
  
  if (!entry) return undefined;
  
  return {
    name: typeof entry.name === "string" ? entry.name : undefined,
    workspace: typeof entry.workspace === "string" 
      ? entry.workspace 
      : undefined,
    agentDir: typeof entry.agentDir === "string" 
      ? entry.agentDir 
      : undefined,
    model: typeof entry.model === "string" || 
            (entry.model && typeof entry.model === "object")
      ? entry.model 
      : undefined,
    skills: Array.isArray(entry.skills) ? entry.skills : undefined,
    memorySearch: entry.memorySearch,
    humanDelay: entry.humanDelay,
    heartbeat: entry.heartbeat,
    identity: entry.identity,
    groupChat: entry.groupChat,
    subagents: typeof entry.subagents === "object" && entry.subagents
      ? entry.subagents 
      : undefined,
    sandbox: entry.sandbox,
    tools: entry.tools,
  };
}
```

## 智能体工作区解析

### 工作区路径解析

```typescript
export function resolveAgentWorkspaceDir(
  cfg: OpenClawConfig,
  agentId: string
) {
  const id = normalizeAgentId(agentId);
  const configured = resolveAgentConfig(cfg, id)?.workspace?.trim();
  
  if (configured) {
    return stripNullBytes(resolveUserPath(configured));
  }
  
  const defaultAgentId = resolveDefaultAgentId(cfg);
  if (id === defaultAgentId) {
    const fallback = cfg.agents?.defaults?.workspace?.trim();
    if (fallback) {
      return stripNullBytes(resolveUserPath(fallback));
    }
    return stripNullBytes(resolveDefaultAgentWorkspaceDir(process.env));
  }
  
  const stateDir = resolveStateDir(process.env);
  return stripNullBytes(path.join(stateDir, `workspace-${id}`));
}
```

### 智能体目录解析

```typescript
export function resolveAgentDir(cfg: OpenClawConfig, agentId: string) {
  const id = normalizeAgentId(agentId);
  const configured = resolveAgentConfig(cfg, id)?.agentDir?.trim();
  
  if (configured) {
    return resolveUserPath(configured);
  }
  
  const root = resolveStateDir(process.env);
  return path.join(root, "agents", id, "agent");
}
```

## 智能体创建流程

### 1. 配置阶段

用户通过配置文件定义智能体：

```typescript
export function applyAgentConfig(
  cfg: OpenClawConfig,
  params: {
    agentId: string;
    name?: string;
    workspace?: string;
    agentDir?: string;
    model?: string;
  },
): OpenClawConfig {
  const agentId = normalizeAgentId(params.agentId);
  const name = params.name?.trim();
  const list = listAgentEntries(cfg);
  const index = findAgentEntryIndex(list, agentId);
  
  const base = index >= 0 ? list[index] : { id: agentId };
  const nextEntry: AgentEntry = {
    ...base,
    ...(name ? { name } : {}),
    ...(params.workspace ? { workspace: params.workspace } : {}),
    ...(params.agentDir ? { agentDir: params.agentDir } : {}),
    ...(params.model ? { model: params.model } : {}),
  };
  
  const nextList = [...list];
  if (index >= 0) {
    nextList[index] = nextEntry;
  } else {
    if (nextList.length === 0 && 
        agentId !== normalizeAgentId(resolveDefaultAgentId(cfg))) {
      nextList.push({ id: resolveDefaultAgentId(cfg) });
    }
    nextList.push(nextEntry);
  }
  
  return {
    ...cfg,
    agents: {
      ...cfg.agents,
      list: nextList,
    },
  };
}
```

### 2. 工作区初始化

自动创建工作区并初始化引导文件：

```typescript
const result = await ensureAgentWorkspace({
  dir: workspacePath,
  ensureBootstrapFiles: true,
});
```

### 3. 身份设置

通过IDENTITY.md文件设置智能体身份：

```typescript
const identity = loadAgentIdentityFromWorkspace(workspace);
if (identity) {
  console.log(`Agent: ${identity.name} ${identity.emoji}`);
  console.log(`Vibe: ${identity.vibe}`);
}
```

### 4. 智能体激活

通过绑定规则将智能体激活到特定渠道：

```json5
{
  bindings: [
    {
      agentId: "main",
      match: { channel: "whatsapp" },
    },
    {
      agentId: "coder",
      match: { channel: "discord", guildId: "123456" },
    },
  ],
}
```

## 智能体生命周期

### 创建阶段

1. **配置定义**：在配置文件中添加智能体条目
2. **工作区初始化**：创建工作区目录和引导文件
3. **身份设置**：配置IDENTITY.md文件
4. **绑定激活**：通过绑定规则激活智能体

### 运行阶段

1. **会话启动**：当消息到达时，根据绑定规则选择智能体
2. **上下文加载**：加载工作区文件和智能体配置
3. **模型推理**：使用配置的模型进行推理
4. **工具执行**：调用智能体可用的工具和技能
5. **响应生成**：生成并返回响应

### 管理阶段

1. **配置更新**：修改智能体配置
2. **工作区维护**：更新工作区文件
3. **身份调整**：修改IDENTITY.md文件
4. **绑定管理**：调整智能体绑定规则

### 删除阶段

```typescript
export function pruneAgentConfig(
  cfg: OpenClawConfig,
  agentId: string,
): {
  config: OpenClawConfig;
  removedBindings: number;
  removedAllow: number;
} {
  const id = normalizeAgentId(agentId);
  const agents = listAgentEntries(cfg);
  const nextAgentsList = agents.filter(
    (entry) => normalizeAgentId(entry.id) !== id
  );
  
  const bindings = cfg.bindings ?? [];
  const filteredBindings = bindings.filter(
    (binding) => normalizeAgentId(binding.agentId) !== id
  );
  
  const allow = cfg.tools?.agentToAgent?.allow ?? [];
  const filteredAllow = allow.filter((entry) => entry !== id);
  
  return {
    config: {
      ...cfg,
      agents: nextAgentsList.length > 0 
        ? { ...cfg.agents, list: nextAgentsList }
        : undefined,
      bindings: filteredBindings.length > 0 
        ? filteredBindings 
        : undefined,
      tools: cfg.tools?.agentToAgent
        ? {
            ...cfg.tools,
            agentToAgent: {
              ...cfg.tools.agentToAgent,
              allow: filteredAllow.length > 0 
                ? filteredAllow 
                : undefined,
            },
          }
        : cfg.tools,
    },
    removedBindings: bindings.length - filteredBindings.length,
    removedAllow: allow.length - filteredAllow.length,
  };
}
```

## 智能体摘要

OpenClaw提供智能体摘要功能，用于显示智能体状态：

```typescript
export type AgentSummary = {
  id: string;
  name?: string;
  identityName?: string;
  identityEmoji?: string;
  identitySource?: "identity" | "config";
  workspace: string;
  agentDir: string;
  model?: string;
  bindings: number;
  bindingDetails?: string[];
  routes?: string[];
  providers?: string[];
  isDefault: boolean;
};

export function buildAgentSummaries(
  cfg: OpenClawConfig
): AgentSummary[] {
  const defaultAgentId = normalizeAgentId(resolveDefaultAgentId(cfg));
  const configuredAgents = listAgentEntries(cfg);
  const orderedIds = configuredAgents.length > 0
    ? configuredAgents.map((agent) => normalizeAgentId(agent.id))
    : [defaultAgentId];
  
  const bindingCounts = new Map<string, number>();
  for (const binding of listRouteBindings(cfg)) {
    const agentId = normalizeAgentId(binding.agentId);
    bindingCounts.set(
      agentId, 
      (bindingCounts.get(agentId) ?? 0) + 1
    );
  }
  
  const ordered = orderedIds.filter(
    (id, index) => orderedIds.indexOf(id) === index
  );
  
  return ordered.map((id) => {
    const workspace = resolveAgentWorkspaceDir(cfg, id);
    const identity = loadAgentIdentity(workspace);
    const configIdentity = configuredAgents.find(
      (agent) => normalizeAgentId(agent.id) === id
    )?.identity;
    
    return {
      id,
      name: resolveAgentName(cfg, id),
      identityName: identity?.name ?? configIdentity?.name?.trim(),
      identityEmoji: identity?.emoji ?? configIdentity?.emoji?.trim(),
      identitySource: identity
        ? "identity"
        : configIdentity && (identityName || identityEmoji)
          ? "config"
          : undefined,
      workspace,
      agentDir: resolveAgentDir(cfg, id),
      model: resolveAgentModel(cfg, id),
      bindings: bindingCounts.get(id) ?? 0,
      isDefault: id === defaultAgentId,
    };
  });
}
```

## 最佳实践

### 1. 智能体命名

- 使用简洁、描述性的ID（如`main`、`coder`、`research`）
- 提供清晰的显示名称
- 为不同用途创建专门的智能体

### 2. 工作区管理

- 为每个智能体使用独立的工作区
- 保持工作区文件的一致性
- 定期备份重要工作区

### 3. 身份配置

- 为智能体设置清晰的身份标识
- 使用表情符号增强识别度
- 定义明确的语气和行为特征

### 4. 模型选择

- 根据任务复杂度选择合适的模型
- 为不同智能体配置不同的模型
- 合理使用模型回退机制

### 5. 绑定规则

- 明确智能体的使用场景
- 避免绑定规则冲突
- 使用默认智能体处理未匹配的情况

## 总结

OpenClaw的智能体创建机制通过配置文件、工作区系统和身份管理，为用户提供了强大而灵活的多智能体管理能力。通过合理配置智能体，可以构建出适应不同场景和需求的AI助手生态系统。