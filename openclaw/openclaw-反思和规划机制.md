# OpenClaw 反思和规划机制详解

## 概述

OpenClaw 采用了一套多层次、多角度的反思和规划机制，使 AI Agent 不仅能够响应用户请求，还能主动思考、定期反思、规划任务并持久化重要信息。这套机制包括 Thinking/Reasoning 推理系统、Heartbeat 定期检查、Memory 记忆管理、Compaction 上下文压缩和 Cron 定时任务等多个组件，共同构成了一个完整的智能体自我管理和优化系统。

本文将深入分析 OpenClaw 的反思和规划机制，包括其设计理念、核心组件、工作流程和最佳实践。

## 核心设计理念

OpenClaw 的反思和规划机制基于以下核心设计理念：

1. **主动思考**：不仅被动响应，还要主动推理和规划
2. **定期反思**：通过定时机制定期检查和总结
3. **持久化记忆**：将重要信息保存到磁盘，避免遗忘
4. **上下文优化**：通过压缩和清理保持上下文窗口高效
5. **灵活配置**：支持多种模式和级别，适应不同场景

## 核心组件

### 1. Thinking/Reasoning 推理系统

Thinking/Reasoning 系统是 OpenClaw 反思机制的核心，允许模型在不同级别上进行推理和思考。

#### 思考级别（ThinkLevel）

OpenClaw 支持多种思考级别，从简单到复杂：

```typescript
export type ThinkLevel =
  | "off"          // 关闭思考
  | "minimal"       // 最小思考
  | "low"           // 低级思考
  | "medium"         // 中级思考
  | "high"           // 高级思考
  | "xhigh"         // 超高级思考（仅特定模型）
  | "adaptive";      // 自适应思考
```

**级别说明**：

- **off**: 完全关闭思考，模型直接输出答案
- **minimal**: 最小思考，适合简单任务
- **low**: 低级思考，适合日常任务
- **medium**: 中级思考，平衡性能和质量
- **high**: 高级思考，适合复杂问题
- **xhigh**: 超高级思考，仅支持特定模型（GPT-5.x、Codex 等）
- **adaptive**: 自适应，根据任务复杂度自动调整

**支持的模型**：

```typescript
// 支持 xhigh 的模型列表
const XHIGH_MODEL_REFS = [
  "openai/gpt-5.4",
  "openai/gpt-5.4-pro",
  "openai/gpt-5.2",
  "openai-codex/gpt-5.4",
  "openai-codex/gpt-5.3-codex",
  "openai-codex/gpt-5.3-codex-spark",
  "openai-codex/gpt-5.2-codex",
  "openai-codex/gpt-5.1-codex",
  "github-copilot/gpt-5.2-codex",
  "github-copilot/gpt-5.2",
];
```

#### 推理级别（ReasoningLevel）

推理级别控制推理内容的可见性：

```typescript
export type ReasoningLevel =
  | "off"     // 关闭推理，不显示推理过程
  | "on"      // 开启推理，显示推理结果
  | "stream";  // 流式推理，实时显示推理过程
```

#### 推理标签处理

OpenClaw 支持多种推理标签格式，用于标记和提取推理内容：

```typescript
// 支持的推理标签
const REASONING_TAG_PREFIXES = [
  "<think",
  "<thinking",
  "<thought",
  "<antthinking",
  "</think",
  "</thinking",
  "</thought",
  "</antthinking",
];
```

**推理内容提取**：

```typescript
function extractThinkingFromTaggedStreamOutsideCode(text: string): string {
  const codeRegions = findCodeRegions(text);
  let result = "";
  let lastIndex = 0;
  let inThinking = false;

  for (const match of text.matchAll(THINKING_TAG_RE)) {
    const idx = match.index ?? 0;

    // 跳过代码块内的标签
    if (isInsideCode(idx, codeRegions)) {
      continue;
    }

    if (inThinking) {
      result += text.slice(lastIndex, idx);
    }

    const isClose = match[1] === "/";
    inThinking = !isClose;
    lastIndex = idx + match[0].length;
  }

  if (inThinking) {
    result += text.slice(lastIndex);
  }

  return result.trim();
}
```

**推理内容清理**：

```typescript
export function stripReasoningTagsFromText(
  text: string,
  options?: {
    mode?: ReasoningTagMode;  // "strict" | "preserve"
    trim?: ReasoningTagTrim;   // "none" | "start" | "both"
  },
): string {
  // 移除推理标签，保留最终答案
  // 支持严格模式和保留模式
  // 支持不同的修剪选项
}
```

#### 推理内容分发

在支持多消息的渠道（如 Telegram），推理内容和最终答案可以分开发送：

```typescript
export type TelegramReasoningSplit = {
  reasoningText?: string;  // 推理内容
  answerText?: string;      // 最终答案
};

export function splitTelegramReasoningText(text?: string): TelegramReasoningSplit {
  // 从完整响应中分离推理和答案
  // 推理内容可以单独发送或隐藏
  // 最终答案发送给用户
}
```

#### 推理协调器

推理协调器管理推理内容的状态和发送时机：

```typescript
export function createTelegramReasoningStepState() {
  let reasoningStatus: "none" | "hinted" | "delivered" = "none";
  let bufferedFinalAnswer: BufferedFinalAnswer | undefined;

  const noteReasoningHint = () => {
    if (reasoningStatus === "none") {
      reasoningStatus = "hinted";
      // 发送推理提示
    }
  };

  const deliverReasoning = () => {
    if (reasoningStatus === "hinted") {
      reasoningStatus = "delivered";
      // 发送推理内容
    }
  };

  return { noteReasoningHint, deliverReasoning };
}
```

### 2. Heartbeat 定期检查机制

Heartbeat 机制是 OpenClaw 的定期反思系统，让 Agent 主动检查需要注意的事项。

#### Heartbeat 配置

```typescript
type HeartbeatConfig = {
  every: string;              // 间隔时间（如 "30m", "1h"）
  target: string;              // 目标（"none", "last", 或频道 ID）
  directPolicy: string;         // 直接消息策略（"allow", "block"）
  lightContext: boolean;        // 轻量级上下文（仅 HEARTBEAT.md）
  activeHours?: {              // 活跃时间窗口
    start: string;            // 开始时间（"08:00"）
    end: string;              // 结束时间（"24:00"）
  };
  includeReasoning: boolean;   // 包含推理内容
  prompt: string;             // 自定义提示词
  ackMaxChars: number;        // 确认最大字符数
  model?: string;             // 覆盖模型
};
```

#### 默认配置

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",              // 默认 30 分钟
        target: "none",            // 默认不发送
        directPolicy: "allow",      // 允许直接消息
        lightContext: false,        // 完整上下文
        includeReasoning: false,    // 不包含推理
        prompt: "Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK.",
        ackMaxChars: 300,         // 确认最大 300 字符
      },
    },
  },
}
```

#### Heartbeat 工作流程

```
1. 定时器触发
   ↓
2. 检查活跃时间窗口
   ↓
3. 加载 Bootstrap 文件
   ├─ 完整模式：所有文件
   └─ 轻量模式：仅 HEARTBEAT.md
   ↓
4. 构建 Heartbeat 提示
   ├─ 系统提示中的 Heartbeat 部分
   └─ 用户提示（自定义或默认）
   ↓
5. 执行 Agent 运行
   ↓
6. 处理响应
   ├─ HEARTBEAT_OK：确认并丢弃
   ├─ 有内容：发送给目标
   └─ 推理内容：可选发送
   ↓
7. 记录 Heartbeat 事件
```

#### HEARTBEAT.md 文件

`HEARTBEAT.md` 是一个可选的工作区文件，用于指导 Heartbeat 行为：

```markdown
# Heartbeat Checklist

## Daily Check

- [ ] Review inbox and prioritize emails
- [ ] Check calendar for upcoming meetings
- [ ] Review pending tasks
- [ ] Check system health

## Weekly Review

- [ ] Summarize completed work
- [ ] Plan next week's priorities
- [ ] Update documentation

## Alerts

- [ ] Monitor system resources
- [ ] Check for security alerts
- [ ] Verify backups are running
```

#### Heartbeat 响应契约

- **无事项**：回复 `HEARTBEAT_OK`
- **有事项**：仅返回提醒文本，不包含 `HEARTBEAT_OK`
- **确认规则**：
  - `HEARTBEAT_OK` 在开头或结尾时被视为确认
  - 确认后剩余内容 ≤ `ackMaxChars` 时丢弃
  - `HEARTBEAT_OK` 在中间时不特殊处理

#### 活跃时间窗口

```typescript
function isWithinActiveHours(
  activeHours?: { start: string; end: string },
  timezone?: string,
): boolean {
  if (!activeHours) {
    return true; // 无限制
  }

  const now = getCurrentTime(timezone);
  const start = parseTime(activeHours.start);
  const end = parseTime(activeHours.end);

  return now >= start && now <= end;
}
```

**配置示例**：

```json5
{
  heartbeat: {
    activeHours: {
      start: "08:00",  // 上午 8 点开始
      end: "24:00",    // 午夜 12 点结束
    },
  },
}
```

### 3. Memory 记忆管理机制

Memory 机制是 OpenClaw 的持久化反思系统，将重要信息保存到磁盘。

#### 记忆文件结构

```
workspace/
├── MEMORY.md              # 长期记忆（精心整理）
└── memory/
    ├── 2025-01-01.md   # 每日日志（追加）
    ├── 2025-01-02.md
    └── ...
```

#### 记忆类型

**MEMORY.md**：
- 精心整理的长期记忆
- 决策、偏好、持久性事实
- 仅在主私人会话中加载
- 不在群组上下文中加载

**memory/YYYY-MM-DD.md**：
- 每日日志（仅追加）
- 日常笔记和运行上下文
- 会话开始时读取今天和昨天
- 可以增长很大，需要定期清理

#### 记忆工具

OpenClaw 提供两个记忆工具：

1. **memory_search**：语义搜索
   ```typescript
   memory_search({
     query: "user preferences for code style",
     limit: 10,
     since: "30d"
   });
   ```

2. **memory_get**：目标读取
   ```typescript
   memory_get({
     path: "MEMORY.md",
     lineRange: "1-50"
   });
   ```

#### 自动记忆刷新

在会话接近自动压缩时，OpenClaw 触发静默的记忆刷新：

```typescript
type MemoryFlushConfig = {
  enabled: boolean;              // 是否启用
  softThresholdTokens: number;   // 软阈值（token）
  systemPrompt: string;         // 系统提示
  prompt: string;               // 用户提示
};
```

**默认配置**：

```json5
{
  agents: {
    defaults: {
      compaction: {
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000,
          systemPrompt: "Session nearing compaction. Store durable memories now.",
          prompt: "Write any lasting notes to memory/YYYY-MM-DD.md; reply with NO_REPLY if nothing to store.",
        },
      },
    },
  },
}
```

**刷新触发条件**：

```
会话 token 估计 ≥ 上下文窗口 - reserveTokensFloor - softThresholdTokens
```

**刷新流程**：

```
1. 检测到接近压缩
   ↓
2. 触发静默 Agent 轮次
   ├─ 系统提示：刷新提醒
   └─ 用户提示：写入记忆指令
   ↓
3. Agent 处理
   ├─ 读取当前上下文
   ├─ 识别需要持久化的信息
   ├─ 写入 MEMORY.md 或 memory/YYYY-MM-DD.md
   └─ 回复 NO_REPLY（通常）
   ↓
4. 记录刷新事件
```

#### 向量记忆搜索

OpenClaw 支持向量索引，实现语义搜索：

**配置选项**：

```json5
{
  agents: {
    defaults: {
      memorySearch: {
        provider: "auto",          // auto | openai | gemini | voyage | mistral | ollama | local
        local: {
          modelPath: "/path/to/model.gguf"
        },
        remote: {
          apiKey: "sk-...",
          headers: {}
        },
        enabled: true
      },
    },
  },
}
```

**自动选择逻辑**：

1. `local`：如果配置了本地模型路径
2. `openai`：如果可解析 OpenAI 密钥
3. `gemini`：如果可解析 Gemini 密钥
4. `voyage`：如果可解析 Voyage 密钥
5. `mistral`：如果可解析 Mistral 密钥
6. 否则禁用，直到配置

**QMD 后端（实验性）**：

```json5
{
  memory: {
    backend: "qmd"  // 使用 QMD 侧边车
  }
}
```

QMD 特点：
- 本地优先（BM25 + 向量 + 重排序）
- Markdown 保持为真相来源
- 通过 Bun + node-llama-cpp 运行
- 自动下载 GGUF 模型
- 支持 macOS 和 Linux

### 4. Compaction 上下文压缩机制

Compaction 机制是 OpenClaw 的上下文优化系统，通过压缩会话保持上下文窗口高效。

#### 压缩触发条件

```typescript
type CompactionTrigger = {
  tokenThreshold: number;      // token 阈值
  idleMinutes?: number;       // 空闲分钟数
  manual?: boolean;           // 手动触发
};
```

**默认配置**：

```json5
{
  agents: {
    defaults: {
      compaction: {
        reserveTokensFloor: 20000,      // 保留 token 下限
        memoryFlush: { ... },               // 记忆刷新配置
      },
    },
  },
}
```

#### 压缩流程

```
1. 检测触发条件
   ├─ token 阈值
   ├─ 空闲超时
   └─ 手动命令（/compact）
   ↓
2. 触发记忆刷新（如启用）
   ↓
3. 构建压缩提示
   ├─ 系统提示：压缩指令
   └─ 用户提示：压缩指令（可选）
   ↓
4. 执行压缩 Agent 运行
   ├─ 读取完整会话历史
   ├─ 总结关键信息
   ├─ 保留重要决策
   ├─ 保留待办事项
   └─ 生成压缩摘要
   ↓
5. 替换会话历史
   ├─ 保留压缩摘要
   ├─ 保留最近消息
   └─ 清理旧消息
   ↓
6. 记录压缩事件
   ↓
7. 报告剩余上下文预算
```

#### 压缩提示

```typescript
const COMPACTION_SYSTEM_PROMPT = `
You are running in a compaction turn. Your task is to summarize the conversation history into a compact form while preserving:

1. Key decisions and their rationale
2. Important context and background
3. Pending tasks and action items
4. User preferences and requirements

Be concise but comprehensive. This summary will replace the full conversation history.

Format:
## Summary
[Brief overview of the conversation]

## Key Decisions
- [Decision 1]: Rationale
- [Decision 2]: Rationale

## Pending Tasks
- [ ] Task 1
- [ ] Task 2

## Context Notes
[Any other important context]
`;
```

#### 手动压缩

用户可以随时触发手动压缩：

```
/compact Focus on decisions and open questions
```

#### 上下文修剪

除了压缩，OpenClaw 还支持会话修剪：

- **压缩**：总结并持久化到 JSONL
- **修剪**：仅裁剪旧的工具结果（在内存中）

**修剪策略**：

```typescript
type PruningStrategy = {
  maxToolResults: number;      // 最大工具结果数
  maxToolResultAge: number;   // 最大工具结果年龄（分钟）
  keepRecentMessages: number;  // 保留最近消息数
};
```

### 5. Cron 定时任务机制

Cron 机制是 OpenClaw 的任务规划系统，支持复杂的定时任务。

#### Cron 配置

```typescript
type CronConfig = {
  id: string;
  name: string;
  enabled: boolean;
  schedule: string;              // cron 表达式
  agentId: string;              // 目标 Agent
  systemEvent?: string;         // 系统事件文本
  timeout?: string;             // 超时时间
  timezone?: string;            // 时区
};
```

#### Cron 表达式

```
* * * * * *
│ │ │ │ │ │
│ │ │ │ │ └─ 星期几 (0-6, 0=周日)
│ │ │ └─────── 月份 (1-12)
│ └─────────── 日期 (1-31)
└──────────── 小时 (0-23)

示例：
0 9 * * *        # 每天 9:00
0 */6 * * *      # 每 6 小时
0 9 * * 1        # 每周一 9:00
0 9 1 * *        # 每月 1 号 9:00
```

#### Cron vs Heartbeat

**Heartbeat**：
- 定期 Agent 轮次
- 让模型主动检查
- 适合：后台任务、健康检查、定期提醒

**Cron**：
- 精确时间调度
- 系统事件触发
- 适合：定时报告、数据同步、维护任务

#### Cron 工作流程

```
1. Cron 调度器触发
   ↓
2. 检查时区和时间
   ↓
3. 构建系统事件提示
   ├─ 系统提示：事件上下文
   └─ 用户提示：systemEvent 文本
   ↓
4. 执行 Agent 运行
   ↓
5. 处理响应
   ├─ 执行任务
   ├─ 记录结果
   └─ 可选：发送通知
   ↓
6. 记录 Cron 事件
```

#### 系统事件

```typescript
type SystemEvent = {
  type: "cron" | "exec" | "wake";
  text: string;
  timestamp: number;
  metadata?: Record<string, unknown>;
};
```

**事件类型**：

- **cron**：定时触发的事件
- **exec**：命令执行完成事件
- **wake**：唤醒事件

#### Cron 配置示例

```json5
{
  cron: {
    jobs: [
      {
        id: "daily-report",
        name: "Daily Status Report",
        enabled: true,
        schedule: "0 9 * * *",
        agentId: "default",
        systemEvent: "Generate daily status report. Check system health, review pending tasks, and summarize completed work.",
        timeout: "10m",
        timezone: "Asia/Shanghai"
      },
      {
        id: "weekly-cleanup",
        name: "Weekly Cleanup",
        enabled: true,
        schedule: "0 10 * * 0",
        agentId: "default",
        systemEvent: "Perform weekly cleanup. Review and archive old logs, clear temporary files, and update documentation.",
        timeout: "30m",
        timezone: "Asia/Shanghai"
      }
    ]
  }
}
```

## 集成工作流程

### 完整的反思和规划流程

```
用户交互
    ↓
Thinking/Reasoning
    ├─ 选择思考级别
    ├─ 执行推理
    └─ 生成响应
    ↓
Memory 写入
    ├─ 识别重要信息
    ├─ 写入 MEMORY.md
    └─ 写入 memory/YYYY-MM-DD.md
    ↓
Heartbeat 触发
    ├─ 定期检查
    ├─ 读取 HEARTBEAT.md
    ├─ 评估状态
    └─ 发送提醒或 HEARTBEAT_OK
    ↓
Compaction 触发
    ├─ 检测上下文使用
    ├─ 触发记忆刷新
    ├─ 压缩会话历史
    └─ 优化上下文窗口
    ↓
Cron 触发
    ├─ 定时执行
    ├─ 处理系统事件
    └─ 执行计划任务
    ↓
持续优化
    ├─ 向量索引更新
    ├─ 记忆搜索优化
    └─ 性能监控
```

### 组件交互

```
┌─────────────────────────────────────────────────────────────┐
│                   用户请求                          │
└──────────────────────┬──────────────────────────────────┘
                       ↓
┌──────────────────────────────────────────────────────┐
│              Thinking/Reasoning               │
│  ├─ 思考级别选择                               │
│  ├─ 推理内容生成                               │
│  └─ 最终答案输出                                 │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│                  Memory 写入                   │
│  ├─ MEMORY.md (长期记忆)                       │
│  └─ memory/YYYY-MM-DD.md (每日日志)              │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│                Heartbeat 检查                  │
│  ├─ 定期触发 (30m/1h)                         │
│  ├─ HEARTBEAT.md 指导                           │
│  └─ 状态评估和提醒                              │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│               Compaction 压缩                  │
│  ├─ 记忆刷新 (预压缩)                          │
│  ├─ 会话历史压缩                               │
│  └─ 上下文窗口优化                              │
└──────────────────┬───────────────────────────────────┘
                   ↓
┌──────────────────────────────────────────────────────┐
│                 Cron 定时任务                  │
│  ├─ 精确时间调度                               │
│  ├─ 系统事件处理                               │
│  └─ 计划任务执行                                │
└──────────────────────────────────────────────────────┘
```

## 配置和定制

### 全局配置

```json5
{
  agents: {
    defaults: {
      // Thinking 配置
      thinkingDefault: "medium",        // 默认思考级别

      // Heartbeat 配置
      heartbeat: {
        every: "30m",
        target: "last",
        lightContext: false,
        includeReasoning: false,
        activeHours: { start: "08:00", end: "24:00" }
      },

      // Compaction 配置
      compaction: {
        reserveTokensFloor: 20000,
        memoryFlush: {
          enabled: true,
          softThresholdTokens: 4000
        }
      },

      // Memory 配置
      memorySearch: {
        provider: "auto",
        enabled: true
      }
    }
  }
}
```

### Agent 特定配置

```json5
{
  agents: {
    list: [
      {
        id: "default",
        heartbeat: {
          every: "1h",              // 覆盖默认
          prompt: "Custom heartbeat prompt"
        },
        thinkingDefault: "high",      // 覆盖默认
      },
      {
        id: "assistant",
        heartbeat: {
          every: "15m",
          target: "telegram",
          lightContext: true          // 轻量级上下文
        },
        thinkingDefault: "adaptive"    // 自适应思考
      }
    ]
  }
}
```

### 渠道特定配置

```json5
{
  channels: {
    telegram: {
      capabilities: {
        inlineButtons: "dm",
        reactions: "minimal"
      }
    },
    slack: {
      capabilities: {
        inlineButtons: "all",
        reactions: "extensive"
      }
    }
  }
}
```

## 最佳实践

### Thinking/Reasoning 使用

1. **选择合适的级别**：
   - 简单任务：`low` 或 `minimal`
   - 复杂任务：`high` 或 `xhigh`
   - 不确定：`adaptive`

2. **推理内容管理**：
   - 使用推理标签标记推理过程
   - 保持推理简洁但完整
   - 避免在推理中重复信息

3. **推理可见性**：
   - 开发/调试：`stream` 实时查看
   - 生产环境：`off` 或 `on` 根据需求
   - 用户透明：考虑 `on` 让用户了解推理过程

### Heartbeat 配置

1. **间隔选择**：
   - 频繁检查：`15m` 或 `30m`
   - 适度检查：`1h` 或 `2h`
   - 稀疏检查：`4h` 或更长

2. **目标设置**：
   - 默认：`target: "none"` 不打扰用户
   - 通知：`target: "last"` 发送给最后联系人
   - 特定：`target: "telegram"` 发送到特定频道

3. **HEARTBEAT.md 编写**：
   - 保持简洁和可操作
   - 使用清单格式
   - 包含日常和每周检查项

### Memory 管理

1. **MEMORY.md 维护**：
   - 定期清理过时信息
   - 保持结构化（决策、偏好、事实）
   - 使用清晰的标题和分类

2. **每日日志管理**：
   - 每日一个文件
   - 仅追加，不修改历史
   - 定期归档旧日志

3. **记忆搜索优化**：
   - 使用描述性标题
   - 包含关键词和标签
   - 定期重建向量索引

### Compaction 优化

1. **触发时机**：
   - 自动：基于 token 阈值
   - 手动：用户触发 `/compact`
   - 定期：结合 Heartbeat 或 Cron

2. **压缩策略**：
   - 保留关键决策和理由
   - 保留待办事项和行动项
   - 保留重要上下文
   - 移除冗余和重复

3. **记忆刷新**：
   - 在压缩前触发
   - 写入持久化信息
   - 避免信息丢失

### Cron 规划

1. **任务选择**：
   - 日常任务：每日报告、健康检查
   - 周期任务：清理、归档、总结
   - 月度任务：备份、审计、规划

2. **时间安排**：
   - 避免高峰时段
   - 考虑时区差异
   - 设置合理的超时

3. **错误处理**：
   - 记录失败事件
   - 设置重试策略
   - 发送错误通知

## 性能优化

### Thinking 性能

1. **级别选择**：
   - 简单任务使用低级别
   - 复杂任务使用高级别
   - 避免不必要的推理

2. **推理缓存**：
   - 缓存推理结果
   - 避免重复推理
   - 使用增量推理

### Memory 性能

1. **向量索引**：
   - 使用本地模型（如可能）
   - 定期重建索引
   - 优化嵌入维度

2. **文件管理**：
   - 限制文件大小
   - 定期归档旧日志
   - 使用增量写入

### Compaction 性能

1. **触发优化**：
   - 合理设置 token 阈值
   - 避免频繁压缩
   - 使用空闲时间压缩

2. **压缩效率**：
   - 保留关键信息
   - 移除冗余内容
   - 使用简洁摘要

### Heartbeat 性能

1. **间隔优化**：
   - 根据需求调整间隔
   - 避免过于频繁
   - 使用活跃时间窗口

2. **上下文优化**：
   - 使用轻量级上下文
   - 仅加载必要文件
   - 避免重复加载

## 调试和监控

### Thinking 调试

1. **推理内容查看**：
   ```
   /reasoning on    # 开启推理显示
   /reasoning stream # 流式显示推理
   ```

2. **级别测试**：
   ```
   /thinking low     # 测试低级思考
   /thinking high    # 测试高级思考
   ```

### Memory 调试

1. **记忆搜索测试**：
   ```
   /memory search "user preferences"
   ```

2. **记忆内容查看**：
   ```
   /memory get MEMORY.md 1-50
   ```

### Heartbeat 调试

1. **Heartbeat 状态**：
   ```
   /status heartbeat
   ```

2. **手动触发**：
   ```
   /heartbeat now
   ```

### Compaction 调试

1. **上下文查看**：
   ```
   /context detail
   ```

2. **手动压缩**：
   ```
   /compact Focus on decisions
   ```

### Cron 调试

1. **Cron 列表**：
   ```
   /cron list
   ```

2. **Cron 状态**：
   ```
   /cron status <id>
   ```

## 总结

OpenClaw 的反思和规划机制是一个多层次、多角度的智能体自我管理和优化系统，具有以下特点：

1. **Thinking/Reasoning**：支持多级别推理，从简单到复杂
2. **Heartbeat**：定期主动检查，让 Agent 保持警觉
3. **Memory**：持久化重要信息，避免遗忘
4. **Compaction**：优化上下文窗口，提高效率
5. **Cron**：精确时间调度，执行计划任务

这套机制确保了 OpenClaw 能够：
- 主动思考和推理
- 定期反思和检查
- 持久化重要信息
- 优化上下文使用
- 执行计划任务

通过合理配置和使用这些机制，可以显著提升 OpenClaw 的智能性、可靠性和效率。理解这套机制对于深入使用和定制 OpenClaw 至关重要。