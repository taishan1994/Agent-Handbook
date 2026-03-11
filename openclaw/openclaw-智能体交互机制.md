# OpenClaw智能体交互机制

OpenClaw的智能体交互系统是其多智能体协作的核心功能，允许智能体之间进行消息传递、任务委托和结果汇总。本文将详细介绍OpenClaw中智能体之间的各种交互方式。

## 智能体交互概述

在OpenClaw中，智能体交互主要通过以下机制实现：

1. **子智能体生成**：主智能体可以创建独立的子智能体来执行特定任务
2. **智能体间消息传递**：智能体之间可以直接发送消息进行通信
3. **结果通告机制**：子智能体完成任务后向父智能体通告结果
4. **嵌套协作模式**：支持多级嵌套的智能体协作结构
5. **线程绑定会话**：支持持久的线程绑定以实现持续交互

## 子智能体机制

### 基本概念

子智能体是从现有智能体运行中生成的后台智能体实例，它们在独立的会话中运行（`agent:<agentId>:subagent:<uuid>`），并在完成后将结果**通告**回请求者聊天渠道。

### 子智能体生成工具

`sessions_spawn`是生成子智能体的核心工具：

```typescript
const SessionsSpawnToolSchema = Type.Object({
  task: Type.String(),                    // 必需：任务描述
  label: Type.Optional(Type.String()),       // 可选：子智能体标签
  runtime: optionalStringEnum(["subagent", "acp"]),
  agentId: Type.Optional(Type.String()),    // 可选：目标智能体ID
  model: Type.Optional(Type.String()),       // 可选：覆盖模型
  thinking: Type.Optional(Type.String()),    // 可选：思考级别
  cwd: Type.Optional(Type.String()),       // 可选：工作目录
  runTimeoutSeconds: Type.Optional(Type.Number({ minimum: 0 })),
  thread: Type.Optional(Type.Boolean()),     // 可选：线程绑定
  mode: optionalStringEnum(["run", "session"]),
  cleanup: optionalStringEnum(["delete", "keep"]),
  sandbox: optionalStringEnum(["inherit", "require"]),
  attachments: Type.Optional(Type.Array(...)), // 可选：附件
});
```

### 子智能体生成流程

```typescript
export function createSessionsSpawnTool(opts?: {
  agentSessionKey?: string;
  agentChannel?: GatewayMessageChannel;
  agentAccountId?: string;
  agentTo?: string;
  agentThreadId?: string | number;
  sandboxed?: boolean;
  requesterAgentIdOverride?: string;
}): AnyAgentTool {
  return {
    label: "Sessions",
    name: "sessions_spawn",
    description: '生成隔离的会话（runtime="subagent"或runtime="acp"）。mode="run"是一次性的，mode="session"是持久的/线程绑定的。子智能体自动继承父工作区目录。',
    parameters: SessionsSpawnToolSchema,
    execute: async (_toolCallId, args) => {
      const params = args as Record<string, unknown>;
      const task = readStringParam(params, "task", { required: true });
      const runtime = params.runtime === "acp" ? "acp" : "subagent";
      
      // 执行子智能体生成逻辑
      const result = await spawnSubagentDirect(
        {
          task,
          label: label || undefined,
          agentId: requestedAgentId,
          model: modelOverride,
          thinking: thinkingOverrideRaw,
          runTimeoutSeconds,
          thread,
          mode,
          cleanup,
          sandbox,
          expectsCompletionMessage: true,
          attachments,
        },
        context
      );
      
      return jsonResult(result);
    },
  };
}
```

### 子智能体特性

**隔离性**：
- 子智能体在独立的会话中运行
- 拥有独立的上下文和token使用
- 默认不获得会话工具

**非阻塞**：
- `sessions_spawn`立即返回`{ status: "accepted", runId, childSessionKey }`
- 主智能体不会被阻塞等待子智能体完成

**结果通告**：
- 子智能体完成后运行通告步骤
- 将结果发布到请求者聊天渠道
- 包含运行时统计和token使用情况

## 智能体间消息传递

### sessions_send工具

`sessions_send`工具允许智能体之间直接发送消息：

```typescript
const SessionsSendToolSchema = Type.Object({
  sessionKey: Type.Optional(Type.String()),     // 目标会话键
  label: Type.Optional(Type.String()),          // 目标会话标签
  agentId: Type.Optional(Type.String()),       // 目标智能体ID
  message: Type.String(),                     // 消息内容
  timeoutSeconds: Type.Optional(Type.Number({ minimum: 0 })),
});
```

### 消息传递流程

```typescript
export function createSessionsSendTool(opts?: {
  agentSessionKey?: string;
  agentChannel?: GatewayMessageChannel;
  sandboxed?: boolean;
}): AnyAgentTool {
  return {
    label: "Session Send",
    name: "sessions_send",
    description: "向另一个会话发送消息。使用sessionKey或label来识别目标。",
    parameters: SessionsSendToolSchema,
    execute: async (_toolCallId, args) => {
      const params = args as Record<string, unknown>;
      const message = readStringParam(params, "message", { required: true });
      
      // 解析目标会话
      const resolvedSession = await resolveSessionReference({
        sessionKey,
        alias,
        mainKey,
        requesterInternalKey: effectiveRequesterKey,
        restrictToSpawned,
      });
      
      // 构建智能体到智能体的消息上下文
      const agentMessageContext = buildAgentToAgentMessageContext({
        requesterSessionKey: opts?.agentSessionKey,
        requesterChannel: opts?.agentChannel,
        targetSessionKey: displayKey,
      });
      
      // 发送消息
      const response = await callGateway<{ runId: string }>({
        method: "agent",
        params: {
          message,
          sessionKey: resolvedKey,
          idempotencyKey,
          deliver: false,
          channel: INTERNAL_MESSAGE_CHANNEL,
          lane: AGENT_LANE_NESTED,
          extraSystemPrompt: agentMessageContext,
          inputProvenance: {
            kind: "inter_session",
            sourceSessionKey: opts?.agentSessionKey,
            sourceChannel: opts?.agentChannel,
            sourceTool: "sessions_send",
          },
        },
        timeoutMs: 10_000,
      });
      
      // 等待响应
      const wait = await callGateway<{ status?: string; error?: string }>({
        method: "agent.wait",
        params: { runId, timeoutMs },
        timeoutMs: timeoutMs + 2000,
      });
      
      // 获取历史记录
      const history = await callGateway<{ messages: Array<unknown> }>({
        method: "chat.history",
        params: { sessionKey: resolvedKey, limit: 50 },
      });
      
      const reply = extractAssistantText(last);
      return jsonResult({
        runId,
        status: "ok",
        reply,
        sessionKey: displayKey,
      });
    },
  };
}
```

### 消息传递特性

**Ping-Pong机制**：
- 支持智能体之间的请求-响应模式
- 自动处理多轮对话
- 可配置最大轮次限制

**超时控制**：
- 支持自定义超时时间
- 默认30秒超时
- 超时后返回错误状态

**会话解析**：
- 支持通过sessionKey直接指定
- 支持通过label间接指定
- 支持通过agentId跨智能体查找

## 通告机制

### 通告步骤

子智能体通过通告步骤向父智能体报告结果：

```typescript
// 通告步骤在子智能体会话中运行
// 如果子智能体精确回复"ANNOUNCE_SKIP"，则不发布任何内容
// 否则根据请求者深度决定传递方式：
// - 顶级请求者会话：使用外部传递的follow-up agent调用
// - 嵌套请求者子智能体会话：接收内部follow-up注入
```

### 通告内容

通告包含以下信息：

```typescript
interface AnnounceContent {
  source: "subagent" | "cron";           // 来源
  childSessionKey: string;                    // 子会话键
  childSessionId: string;                    // 子会话ID
  announceType: string;                        // 通告类型
  taskLabel: string;                          // 任务标签
  status: "success" | "error" | "timeout" | "unknown";  // 状态
  result: string;                             // 结果内容
  runtime: string;                            // 运行时间
  tokenUsage: TokenUsage;                     // Token使用
  estimatedCost?: number;                      // 估算成本
  transcriptPath: string;                      // 转录路径
}
```

### 通告传递规则

**顶级请求者**：
- 使用follow-up `agent`调用进行外部传递（`deliver=true`）
- 直接发送到用户聊天渠道

**嵌套请求者**：
- 接收内部follow-up注入（`deliver=false`）
- 允许编排器在会话内合成子结果
- 如果嵌套请求者会话已消失，则回退到该会话的请求者

**静默模式**：
- 子智能体精确回复`ANNOUNCE_SKIP`时保持静默
- 不发布任何内容到请求者渠道

## 嵌套智能体协作

### 深度级别

OpenClaw支持多级嵌套的智能体结构：

| 深度 | 会话键格式                          | 角色                    | 能否生成子智能体？         |
| ----- | ------------------------------------ | ----------------------- | ---------------------------- |
| 0     | `agent:<id>:main`                 | 主智能体                | 始终                       |
| 1     | `agent:<id>:subagent:<uuid>`        | 子智能体（编排器）       | 仅当`maxSpawnDepth >= 2`时 |
| 2     | `agent:<id>:subagent:<uuid>:subagent:<uuid>` | 子子智能体（工作器） | 永不                        |

### 配置嵌套深度

```json5
{
  agents: {
    defaults: {
      subagents: {
        maxSpawnDepth: 2,        // 允许子智能体生成子智能体（默认：1）
        maxChildrenPerAgent: 5,    // 每个智能体会话的最大活动子智能体数（默认：5）
        maxConcurrent: 8,          // 全局并发通道上限（默认：8）
        runTimeoutSeconds: 900,     // sessions_spawn省略时的默认超时（0 = 无超时）
      },
    },
  },
}
```

### 编排器模式

当`maxSpawnDepth >= 2`时，支持编排器模式：

**主智能体 → 编排器子智能体 → 工作器子子智能体**

```typescript
// 深度1编排器子智能体可以管理其子智能体
if (maxSpawnDepth >= 2) {
  // 编排器子智能体获得以下工具：
  // - sessions_spawn：生成子智能体
  // - subagents：列出/控制子智能体
  // - sessions_list：列出会话
  // - sessions_history：获取历史记录
}
```

### 结果流向上传递

```
1. 深度2工作器完成 → 向其父级（深度1编排器）通告
2. 深度1编排器接收通告，合成结果，完成 → 向主智能体通告
3. 主智能体接收通告并传递给用户
```

每个层级只看到其直接子智能体的通告。

### 级联停止

停止深度1编排器会自动停止其所有深度2子智能体：

```typescript
async function cascadeKillChildren(params: {
  cfg: ReturnType<typeof loadConfig>;
  parentChildSessionKey: string;
  cache: Map<string, Record<string, SessionEntry>>;
  seenChildSessionKeys?: Set<string>;
}): Promise<{ killed: number; labels: string[] }> {
  const childRuns = listSubagentRunsForRequester(params.parentChildSessionKey);
  const seenChildSessionKeys = params.seenChildSessionKeys ?? new Set<string>();
  let killed = 0;
  const labels: string[] = [];

  for (const run of childRuns) {
    const childKey = run.childSessionKey?.trim();
    if (!childKey || seenChildSessionKeys.has(childKey)) {
      continue;
    }
    seenChildSessionKeys.add(childKey);

    if (!run.endedAt) {
      const stopResult = await killSubagentRun({
        cfg: params.cfg,
        entry: run,
        cache: params.cache,
      });
      if (stopResult.killed) {
        killed += 1;
        labels.push(resolveSubagentLabel(run));
      }
    }

    // 即使父级已结束，也递归遍历孙级
    const cascade = await cascadeKillChildren({
      cfg: params.cfg,
      parentChildSessionKey: childKey,
      cache: params.cache,
      seenChildSessionKeys,
    });
    killed += cascade.killed;
    labels.push(...cascade.labels);
  }

  return { killed, labels };
}
```

## 线程绑定会话

### 持久线程绑定

当为通道启用线程绑定时，子智能体可以绑定到线程，以便该线程中的后续用户消息继续路由到同一子智能体会话。

### 支持线程绑定的通道

- **Discord**（当前唯一支持的通道）：支持持久的线程绑定子智能体会话（`sessions_spawn`使用`thread: true`）、手动线程控制（`/focus`、`/unfocus`、`/agents`、`/session idle`、`/session max-age`）和适配器键

### 快速流程

1. 使用`thread: true`（以及可选的`mode: "session"`）通过`sessions_spawn`生成
2. OpenClaw在活动通道中创建或绑定线程到该会话目标
3. 该线程中的回复和后续消息路由到绑定的会话
4. 使用`/session idle`检查/更新非活动自动解除焦点
5. 使用`/session max-age`控制硬性上限
6. 使用`/unfocus`手动解除绑定

### 手动控制

- `/focus <target>`：将当前线程（或创建一个）绑定到子智能体/会话目标
- `/unfocus`：移除当前绑定线程的绑定
- `/agents`：列出活动运行和绑定状态（`thread:<id>`或`unbound`）
- `/session idle`和`/session max-age`：仅对焦点绑定的线程有效

### 配置开关

```json5
{
  session: {
    threadBindings: {
      enabled: true,           // 全局默认
      idleHours: 24,          // 非活动自动解除焦点时间
      maxAgeHours: 168,        // 硬性上限（7天）
    },
  },
}
```

## 子智能体管理工具

### subagents工具

`subagents`工具用于列出、终止或引导生成的子智能体：

```typescript
const SubagentsToolSchema = Type.Object({
  action: optionalStringEnum(["list", "kill", "steer"]),
  target: Type.Optional(Type.String()),
  message: Type.Optional(Type.String()),
  recentMinutes: Type.Optional(Type.Number({ minimum: 1 })),
});
```

### 列出子智能体

```typescript
if (action === "list") {
  const now = Date.now();
  const recentCutoff = now - recentMinutes * 60_000;
  
  // 构建活动子智能体列表
  const active = runs
    .filter((entry) => isActiveRun(entry))
    .map((entry) => buildListEntry(entry, now - entry.startedAt));
  
  // 构建最近子智能体列表
  const recent = runs
    .filter((entry) =>
      !isActiveRun(entry) && 
      !!entry.endedAt && 
      entry.endedAt >= recentCutoff
    )
    .map((entry) =>
      buildListEntry(entry, entry.endedAt - entry.startedAt)
    );
  
  const text = buildListText({ active, recent, recentMinutes });
  return jsonResult({
    status: "ok",
    action: "list",
    total: runs.length,
    active: active.map((entry) => entry.view),
    recent: recent.map((entry) => entry.view),
    text,
  });
}
```

### 终止子智能体

```typescript
if (action === "kill") {
  const target = readStringParam(params, "target", { required: true });
  
  if (target === "all" || target === "*") {
    // 终止所有子智能体
    for (const entry of runs) {
      const stopResult = await killSubagentRun({ cfg, entry, cache });
      // 级联终止子智能体的子智能体
      const cascade = await cascadeKillChildren({
        cfg,
        parentChildSessionKey: entry.childSessionKey,
        cache,
      });
    }
  } else {
    // 终止特定子智能体
    const resolved = resolveSubagentTarget(runs, target, {
      recentMinutes,
      isActive: isActiveRun,
    });
    const stopResult = await killSubagentRun({
      cfg,
      entry: resolved.entry,
      cache,
    });
    const cascade = await cascadeKillChildren({
      cfg,
      parentChildSessionKey: resolved.entry.childSessionKey,
      cache,
    });
  }
}
```

### 引导子智能体

```typescript
if (action === "steer") {
  const target = readStringParam(params, "target", { required: true });
  const message = readStringParam(params, "message", { required: true });
  
  // 速率限制
  const now = Date.now();
  const lastSteerTime = steerRateLimit.get(target) ?? 0;
  if (now - lastSteerTime < STEER_RATE_LIMIT_MS) {
    return jsonResult({
      status: "error",
      action: "steer",
      target,
      error: "Steer rate limit exceeded. Please wait before steering again.",
    });
  }
  
  // 解析目标并发送引导消息
  const resolved = resolveSubagentTarget(runs, target, {
    recentMinutes,
    isActive: isActiveRun,
  });
  
  // 通过sessions_send发送引导消息
  const steerResult = await sendSteerMessage({
    targetSessionKey: resolved.entry.childSessionKey,
    message,
  });
  
  return jsonResult({
    status: "ok",
    action: "steer",
    target,
    runId: resolved.entry.runId,
    sessionKey: resolved.entry.childSessionKey,
  });
}
```

## 智能体间安全策略

### 访问控制

**允许列表**：
```json5
{
  agents: {
    list: [
      {
        id: "main",
        subagents: {
          allowAgents: ["research", "coder"],  // 允许的智能体ID
        },
      },
    ],
  },
}
```

**沙箱继承保护**：
- 如果请求者会话是沙箱化的，`sessions_spawn`拒绝将运行非沙箱化的目标

**工具策略**：
- 默认情况下，子智能体获得除会话工具外的所有工具
- 当`maxSpawnDepth >= 2`时，深度1编排器子智能体额外获得`sessions_spawn`、`subagents`、`sessions_list`和`sessions_history`

### 智能体到智能体消息策略

```json5
{
  tools: {
    agentToAgent: {
      enabled: true,           // 启用智能体到智能体消息
      allow: ["main", "coder"], // 允许的目标智能体
    },
  },
}
```

### 会话可见性

沙箱隔离的会话可以使用会话工具，但默认情况下只能看到通过`sessions_spawn`生成的会话：

```json5
{
  agents: {
    defaults: {
      sandbox: {
        sessionToolsVisibility: "spawned",  // 或 "all"
      },
    },
  },
}
```

## 认证机制

子智能体认证通过**智能体ID**解析，而不是会话类型：

- 子智能体会话键是`agent:<agentId>:subagent:<uuid>`
- 认证存储从该智能体的`agentDir`加载
- 主智能体的认证配置作为**回退**合并；智能体配置在冲突时覆盖主配置

**注意**：合并是累加的，因此主配置始终可用作回退。目前不支持完全隔离的智能体认证。

## 最佳实践

### 1. 任务分解

将复杂任务分解为多个子智能体可以并行处理的独立任务：

```typescript
// 主智能体生成多个研究子智能体
const researchTasks = [
  "研究最新的AI技术趋势",
  "分析竞争对手的产品",
  "收集市场数据"
];

for (const task of researchTasks) {
  await sessions_spawn({
    task,
    label: `research-${task.substring(0, 20)}`,
    agentId: "research",
  });
}
```

### 2. 模型分层

为子智能体使用更便宜的模型，主智能体使用更高质量的模型：

```json5
{
  agents: {
    defaults: {
      model: "claude-3-5-sonnet-20241022",  // 主智能体模型
      subagents: {
        model: "claude-3-haiku-20240307",  // 子智能体模型
      },
    },
  },
}
```

### 3. 超时控制

为长时间运行的任务设置合理的超时：

```typescript
await sessions_spawn({
  task: "执行长时间运行的数据分析",
  runTimeoutSeconds: 1800,  // 30分钟超时
});
```

### 4. 结果聚合

使用编排器模式聚合多个子智能体的结果：

```typescript
// 编排器子智能体
const orchestrator = await sessions_spawn({
  task: "协调并聚合研究结果",
  agentId: "orchestrator",
});

// 编排器生成多个工作器子智能体
const workerTasks = [
  "分析数据集A",
  "分析数据集B",
  "分析数据集C"
];

for (const task of workerTasks) {
  await sessions_spawn({
    task,
    agentId: "worker",
  });
}
```

### 5. 错误处理

妥善处理子智能体失败和超时：

```typescript
const result = await sessions_spawn({
  task: "执行关键任务",
  runTimeoutSeconds: 600,
});

if (result.status === "timeout") {
  // 重试或使用备用策略
  await sessions_spawn({
    task: "使用备用方法执行任务",
    agentId: "fallback",
  });
}
```

## 总结

OpenClaw的智能体交互机制通过子智能体生成、智能体间消息传递、通告机制和嵌套协作模式，为用户提供了强大而灵活的多智能体协作能力。通过合理配置和使用这些交互机制，可以构建出高效的智能体编排系统，实现复杂的任务分解、并行执行和结果聚合。