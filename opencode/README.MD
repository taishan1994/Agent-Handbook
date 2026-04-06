# OpenCode - Harness Engineer 视角深度解析

## 目录

1. [项目概述](#项目概述)
2. [系统架构](#系统架构)
3. [核心组件详解](#核心组件详解)
4. [工具系统 (Tool System)](#工具系统-tool-system)
5. [会话管理 (Session Management)](#会话管理-session-management)
6. [提供者系统 (Provider System)](#提供者系统-provider-system)
7. [插件系统 (Plugin System)](#插件系统-plugin-system)
8. [权限系统 (Permission System)](#权限系统-permission-system)
9. [LSP 集成](#lsp-集成)
10. [存储层 (Storage Layer)](#存储层-storage-layer)
11. [服务器架构 (Server Architecture)](#服务器架构-server-architecture)
12. [构建与部署系统](#构建与部署系统)
13. [测试框架](#测试框架)
14. [配置管理](#配置管理)
15. [Effect 系统集成](#effect-系统集成)
16. [最佳实践与设计模式](#最佳实践与设计模式)

---

## 项目概述

OpenCode 是一个开源的 AI 编程助手，采用 TypeScript 开发，基于 Bun 运行时。从 Harness Engineer 角度来看，这是一个典型的**事件驱动架构**与**函数式响应式编程**相结合的现代 AI Agent 系统。

### 技术栈概览

| 层级 | 技术选型 |
|------|----------|
| 运行时 | Bun 1.3.11 |
| 语言 | TypeScript 5.8.2 |
| 构建系统 | Turborepo 2.8.13 |
| 函数式框架 | Effect 4.0.0-beta.43 |
| 数据库 | SQLite (Drizzle ORM) |
| Web 框架 | Hono 4.10.7 |
| AI SDK | Vercel AI SDK 6.0.138 |
| Schema | Zod 4.1.8 |

### 项目结构

```
opencode/
├── packages/
│   ├── opencode/          # 核心 CLI 和服务
│   ├── console/           # Web 控制台
│   ├── desktop/           # Tauri 桌面应用
│   ├── app/               # Web 应用
│   ├── sdk/               # SDK 包
│   └── storybook/         # 组件文档
├── sdks/
│   └── vscode/            # VS Code 扩展
├── infra/                 # 基础设施配置
└── specs/                 # 规格文档
```

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Layer                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   TUI       │  │   Web UI    │  │   Desktop   │              │
│  │  (Terminal) │  │  (Console)  │  │   (Tauri)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          └────────────────┼────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Server Layer (Hono)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │ Session API  │  │  Project API │  │  Provider API│           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   File API   │  │  Permission  │  │    MCP API   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Core Services Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Session    │  │    Agent     │  │   Provider   │           │
│  │   Manager    │  │   Service    │  │   Manager    │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │     Tool     │  │   Plugin     │  │   LSP        │           │
│  │   Registry   │  │   Loader     │  │   Client     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │   Database   │  │     Bus      │  │   Storage    │           │
│  │   (SQLite)   │  │   (Event)    │  │   (File)     │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### Effect 系统架构

OpenCode 采用 Effect 框架实现函数式响应式编程，核心设计如下：

```typescript
// Service 定义模式
export class Service extends ServiceMap.Service<Service, Interface>()("@opencode/ServiceName") {}

// Layer 组合模式
export const layer: Layer.Layer<
  Service,
  never,
  Dependency1 | Dependency2
> = Layer.effect(Service, Effect.gen(function* () {
  // 服务实现
}))
```

---

## 核心组件详解

### 1. 入口点 (Entry Point)

**文件**: `packages/opencode/src/index.ts`

```typescript
const cli = yargs(args)
  .parserConfiguration({ "populate--": true })
  .scriptName("opencode")
  .command(new RunCommand())
  .command(new GenerateCommand())
  .command(new ServeCommand())
  // ... 更多命令
```

核心命令包括：
- `run`: 启动交互式会话
- `serve`: 启动 HTTP 服务器
- `generate`: 生成 Agent 配置
- `providers`: 管理提供者
- `mcp`: MCP 服务器管理

### 2. 实例管理 (Instance Management)

**文件**: `packages/opencode/src/project/instance.ts`

实例是 OpenCode 运行时的核心抽象，管理项目级别的状态：

```typescript
export interface InstanceContext {
  projectID: ProjectID
  workspaceID?: WorkspaceID
  directory: string
  config: Config.Info
}
```

**InstanceState** 使用 Effect 的响应式状态管理：

```typescript
export const InstanceState = {
  make: <T>(init: Effect.Effect<T>) => Effect.Effect<{
    get: () => Effect.Effect<T>
    set: (value: T) => Effect.Effect<void>
    modify: (f: (t: T) => T) => Effect.Effect<T>
  }>
}
```

---

## 工具系统 (Tool System)

### 工具定义模式

**文件**: `packages/opencode/src/tool/tool.ts`

OpenCode 的工具系统采用**类型安全的定义模式**：

```typescript
export interface Def<Parameters extends z.ZodType = z.ZodType, M extends Metadata = Metadata> {
  description: string
  parameters: Parameters
  execute(
    args: z.infer<Parameters>,
    ctx: Context,
  ): Promise<{
    title: string
    metadata: M
    output: string
    attachments?: Omit<MessageV2.FilePart, "id" | "sessionID" | "messageID">[]
  }>
}
```

### 工具上下文

```typescript
export type Context<M extends Metadata = Metadata> = {
  sessionID: SessionID
  messageID: MessageID
  agent: string
  abort: AbortSignal
  callID?: string
  extra?: { [key: string]: any }
  messages: MessageV2.WithParts[]
  metadata(input: { title?: string; metadata?: M }): void
  ask(input: Omit<Permission.Request, "id" | "sessionID" | "tool">): Promise<void>
}
```

### 内置工具列表

| 工具 | 文件 | 功能描述 |
|------|------|----------|
| `read` | `tool/read.ts` | 文件读取 |
| `write` | `tool/write.ts` | 文件写入 |
| `edit` | `tool/edit.ts` | 文件编辑 (Search/Replace) |
| `grep` | `tool/grep.ts` | 内容搜索 |
| `glob` | `tool/glob.ts` | 文件模式匹配 |
| `bash` | `tool/bash.ts` | Shell 命令执行 |
| `task` | `tool/task.ts` | 子任务管理 |
| `lsp` | `tool/lsp.ts` | LSP 操作 |
| `plan` | `tool/plan.ts` | 计划管理 |
| `question` | `tool/question.ts` | 用户交互 |
| `batch` | `tool/batch.ts` | 批量操作 |
| `external-directory` | `tool/external-directory.ts` | 外部目录访问 |

### 工具截断机制

```typescript
// 自动输出截断，防止超出上下文限制
const truncated = await Truncate.output(result.output, {}, initCtx?.agent)
return {
  ...result,
  output: truncated.content,
  metadata: {
    ...result.metadata,
    truncated: truncated.truncated,
  },
}
```

---

## 会话管理 (Session Management)

### 会话数据模型

**文件**: `packages/opencode/src/session/index.ts`

```typescript
export interface Info {
  id: SessionID
  slug: string
  projectID: ProjectID
  workspaceID?: WorkspaceID
  directory: string
  parentID?: SessionID
  title: string
  version: number
  summary?: {
    additions: number
    deletions: number
    files: number
    diffs?: string
  }
  share?: { url: string }
  revert?: string
  permission?: Permission.Ruleset
  time: {
    created: number
    updated: number
    compacting?: number
    archived?: number
  }
}
```

### 消息系统 (Message V2)

**文件**: `packages/opencode/src/session/message-v2.ts`

消息采用**多部分结构**设计：

```typescript
export type Part = 
  | TextPart 
  | ReasoningPart 
  | ToolPart 
  | FilePart 
  | ImagePart

export interface Assistant {
  id: MessageID
  sessionID: SessionID
  role: "assistant"
  parts: Part[]
  // ...
}
```

### 会话处理器 (Session Processor)

**文件**: `packages/opencode/src/session/processor.ts`

处理器是会话的核心执行引擎：

```typescript
export interface Handle {
  readonly message: MessageV2.Assistant
  readonly partFromToolCall: (toolCallID: string) => MessageV2.ToolPart | undefined
  readonly abort: () => Effect.Effect<void>
  readonly process: (streamInput: LLM.StreamInput) => Effect.Effect<Result>
}

export type Result = "compact" | "stop" | "continue"
```

### LLM 集成

**文件**: `packages/opencode/src/session/llm.ts`

```typescript
export interface StreamInput {
  model: Provider.Model
  messages: MessageV2.WithParts[]
  tools: Tool.Info[]
  system: string
}
```

### 会话压缩 (Compaction)

**文件**: `packages/opencode/src/session/compaction.ts`

当会话超出上下文限制时，自动触发压缩：

```typescript
export function shouldCompact(session: Info, config: Config.Info): boolean {
  // 检查是否需要压缩
}
```

---

## 提供者系统 (Provider System)

### 提供者架构

**文件**: `packages/opencode/src/provider/provider.ts`

OpenCode 支持**多提供者架构**，内置以下提供者：

```typescript
// 内置提供者导入
import { createAmazonBedrock } from "@ai-sdk/amazon-bedrock"
import { createAnthropic } from "@ai-sdk/anthropic"
import { createAzure } from "@ai-sdk/azure"
import { createGoogleGenerativeAI } from "@ai-sdk/google"
import { createOpenAI } from "@ai-sdk/openai"
import { createOpenRouter } from "@openrouter/ai-sdk-provider"
import { createXai } from "@ai-sdk/xai"
import { createMistral } from "@ai-sdk/mistral"
import { createGroq } from "@ai-sdk/groq"
import { createCerebras } from "@ai-sdk/cerebras"
import { createCohere } from "@ai-sdk/cohere"
import { createTogetherAI } from "@ai-sdk/togetherai"
import { createPerplexity } from "@ai-sdk/perplexity"
import { createGitLab } from "gitlab-ai-provider"
// ... 更多
```

### 模型发现

**文件**: `packages/opencode/src/provider/models.ts`

从 `models.dev` 动态获取模型信息：

```typescript
export namespace ModelsDev {
  export async function fetch(): Promise<Model[]>
  export function get(modelID: string): Model | undefined
}
```

### 提供者服务接口

```typescript
export interface Interface {
  readonly list: () => Effect.Effect<Provider.Info[]>
  readonly get: (id: ProviderID) => Effect.Effect<Provider.Info>
  readonly model: (modelID: ModelID) => Effect.Effect<Provider.Model>
}
```

### SSE 超时处理

```typescript
function wrapSSE(res: Response, ms: number, ctl: AbortController) {
  // SSE 流超时保护
  const reader = res.body.getReader()
  // ... 超时逻辑
}
```

---

## 插件系统 (Plugin System)

### 插件架构

**文件**: `packages/opencode/src/plugin/index.ts`

OpenCode 采用**钩子系统**实现插件扩展：

```typescript
export interface Interface {
  readonly trigger: <Name extends TriggerName, Input, Output>(
    name: Name,
    input: Input,
    output: Output,
  ) => Effect.Effect<Output>
  readonly list: () => Effect.Effect<Hooks[]>
  readonly init: () => Effect.Effect<void>
}
```

### 内置插件

```typescript
const INTERNAL_PLUGINS: PluginInstance[] = [
  CodexAuthPlugin,           // OpenAI Codex 认证
  CopilotAuthPlugin,         // GitHub Copilot 认证
  GitlabAuthPlugin,          // GitLab 认证
  PoeAuthPlugin,             // Poe 认证
  CloudflareWorkersAuthPlugin,
  CloudflareAIGatewayAuthPlugin,
]
```

### 插件加载器

**文件**: `packages/opencode/src/plugin/loader.ts`

```typescript
export namespace PluginLoader {
  export interface Loaded {
    mod: Record<string, unknown>
    spec: Config.PluginSpec
    source: string
    target: string
    options: Config.PluginOptions
    pkg?: { name: string; version: string }
  }
}
```

### 插件规范

```typescript
export const PluginSpec = z.union([
  z.string(),                              // "plugin-name"
  z.tuple([z.string(), PluginOptions])     // ["plugin-name", { options }]
])
```

---

## 权限系统 (Permission System)

### 权限模型

**文件**: `packages/opencode/src/permission/index.ts`

```typescript
export const Action = z.enum(["allow", "deny", "ask"])

export const Rule = z.object({
  permission: z.string(),    // 权限类型
  pattern: z.string(),       // 匹配模式
  action: Action,            // 动作
})

export const Ruleset = Rule.array()
```

### 权限请求流程

```typescript
export const Request = z.object({
  id: PermissionID.zod,
  sessionID: SessionID.zod,
  permission: z.string(),
  patterns: z.string().array(),
  metadata: z.record(z.string(), z.any()),
  always: z.string().array(),
  tool: z.object({
    messageID: MessageID.zod,
    callID: z.string(),
  }).optional(),
})
```

### 错误类型

```typescript
export class RejectedError extends Schema.TaggedErrorClass()("PermissionRejectedError", {}) {}
export class CorrectedError extends Schema.TaggedErrorClass()("PermissionCorrectedError", {
  feedback: Schema.String,
}) {}
export class DeniedError extends Schema.TaggedErrorClass()("PermissionDeniedError", {
  ruleset: Schema.Any,
}) {}
```

### 权限评估

**文件**: `packages/opencode/src/permission/evaluate.ts`

使用通配符匹配进行权限评估：

```typescript
export function evaluate(ruleset: Ruleset, request: Request): Action {
  // 规则评估逻辑
}
```

---

## LSP 集成

### LSP 客户端架构

**文件**: `packages/opencode/src/lsp/index.ts`

```typescript
export const Status = z.object({
  id: z.string(),
  name: z.string(),
  root: z.string(),
  status: z.union([z.literal("connected"), z.literal("error")]),
})

export const Symbol = z.object({
  name: z.string(),
  kind: z.number(),
  location: z.object({
    uri: z.string(),
    range: Range,
  }),
})
```

### LSP 服务器管理

**文件**: `packages/opencode/src/lsp/server.ts`

```typescript
export namespace LSPServer {
  export function start(language: string, root: string): Promise<LSPClient>
  export function stop(id: string): Promise<void>
}
```

### 语言支持

**文件**: `packages/opencode/src/lsp/language.ts`

自动检测项目语言并启动相应的 LSP 服务器。

### LSP 启动器

**文件**: `packages/opencode/src/lsp/launch.ts`

```typescript
export function spawn(language: string, root: string): ChildProcess {
  // 启动 LSP 服务器进程
}
```

---

## 存储层 (Storage Layer)

### 数据库架构

**文件**: `packages/opencode/src/storage/db.ts`

使用 **Drizzle ORM** + **SQLite**：

```typescript
export namespace Database {
  export function getChannelPath() {
    if (["latest", "beta"].includes(CHANNEL))
      return path.join(Global.Path.data, "opencode.db")
    return path.join(Global.Path.data, `opencode-${safe}.db`)
  }
}
```

### 数据库优化配置

```typescript
db.run("PRAGMA journal_mode = WAL")
db.run("PRAGMA synchronous = NORMAL")
db.run("PRAGMA busy_timeout = 5000")
db.run("PRAGMA cache_size = -64000")
db.run("PRAGMA foreign_keys = ON")
```

### 迁移系统

```typescript
function migrations(dir: string): Journal {
  // 从文件系统加载迁移脚本
  // 按时间戳排序
}
```

### 数据库表定义

**文件**: `packages/opencode/src/session/session.sql.ts`

```typescript
export const SessionTable = sqliteTable("session", {
  id: text("id").primaryKey(),
  project_id: text("project_id").notNull(),
  workspace_id: text("workspace_id"),
  parent_id: text("parent_id"),
  slug: text("slug").notNull(),
  directory: text("directory").notNull(),
  title: text("title").notNull(),
  version: integer("version").notNull(),
  // ...
})
```

---

## 服务器架构 (Server Architecture)

### HTTP 服务器

**文件**: `packages/opencode/src/server/server.ts`

使用 **Hono** 框架构建：

```typescript
export const ControlPlaneRoutes = (opts?: { cors?: string[] }): Hono => {
  const app = new Hono()
  return app
    .onError(errorHandler(log))
    .use(basicAuth({ username, password }))
    .use(cors({ maxAge: 86_400, origin: ... }))
    .use(compress())
    .route("/global", GlobalRoutes())
    .route("/session", SessionRoutes())
    // ...
}
```

### 路由模块

| 路由文件 | 功能 |
|----------|------|
| `routes/session.ts` | 会话管理 API |
| `routes/project.ts` | 项目管理 API |
| `routes/provider.ts` | 提供者 API |
| `routes/file.ts` | 文件操作 API |
| `routes/permission.ts` | 权限管理 API |
| `routes/mcp.ts` | MCP 协议 API |
| `routes/config.ts` | 配置 API |
| `routes/event.ts` | 事件订阅 API |

### WebSocket 支持

```typescript
import { websocket } from "hono/bun"
// WebSocket 用于实时事件推送
```

### mDNS 服务发现

**文件**: `packages/opencode/src/server/mdns.ts`

```typescript
export namespace MDNS {
  export function announce(port: number): void
  export function discover(): Promise<Service[]>
}
```

---

## 构建与部署系统

### Turborepo 配置

**文件**: `turbo.json`

```json
{
  "tasks": {
    "typecheck": {},
    "build": {
      "dependsOn": [],
      "outputs": ["dist/**"]
    },
    "opencode#test": {
      "dependsOn": ["^build"],
      "outputs": [],
      "passThroughEnv": ["*"]
    }
  }
}
```

### SST 基础设施

**文件**: `sst.config.ts`

```typescript
export default $config({
  app(input) {
    return {
      name: "opencode",
      removal: input?.stage === "production" ? "retain" : "remove",
      protect: ["production"].includes(input?.stage),
      home: "cloudflare",
      providers: {
        stripe: { apiKey: process.env.STRIPE_SECRET_KEY! },
        planetscale: "0.4.1",
      },
    }
  },
  async run() {
    await import("./infra/app.js")
    await import("./infra/console.js")
    await import("./infra/enterprise.js")
  },
})
```

### GitHub Actions 工作流

| 工作流 | 功能 |
|--------|------|
| `publish.yml` | 发布到 npm、GitHub Releases |
| `test.yml` | 单元测试 + E2E 测试 |
| `deploy.yml` | SST 部署 |
| `typecheck.yml` | 类型检查 |
| `containers.yml` | Docker 镜像构建 |

### 发布流程

```yaml
jobs:
  version:
    # 版本计算
  build-cli:
    # CLI 构建 (多平台)
  build-desktop:
    # 桌面应用构建
  publish-npm:
    # npm 发布
  publish-github:
    # GitHub Release
```

### 多平台构建

- **CLI**: Linux (x64, arm64), macOS (x64, arm64), Windows (x64)
- **Desktop**: macOS (dmg), Windows (exe), Linux (deb, rpm, AppImage)

---

## 测试框架

### 测试结构

```
packages/opencode/test/
├── tool/              # 工具测试
├── session/           # 会话测试
├── provider/          # 提供者测试
├── plugin/            # 插件测试
├── storage/           # 存储测试
├── lsp/               # LSP 测试
├── permission/        # 权限测试
├── fixture/           # 测试夹具
└── lib/               # 测试工具库
```

### 测试配置

**文件**: `packages/opencode/test/preload.ts`

```typescript
// 测试环境预加载配置
```

### 测试夹具

**文件**: `packages/opencode/test/fixture/fixture.ts`

```typescript
export namespace Fixture {
  export function create(options: FixtureOptions): Promise<Fixture>
}
```

### CI 测试

```yaml
- name: Run unit tests
  run: bun turbo test:ci

- name: Publish unit reports
  uses: mikepenz/action-junit-report@v6
  with:
    report_paths: packages/*/.artifacts/unit/junit.xml
```

### E2E 测试

使用 **Playwright** 进行端到端测试：

```yaml
- name: Run E2E tests
  run: bun turbo e2e:ci
```

---

## 配置管理

### 配置层级

**文件**: `packages/opencode/src/config/config.ts`

```
1. 系统管理配置 (最高优先级)
   ├── macOS: /Library/Application Support/opencode
   ├── Windows: C:\ProgramData\opencode
   └── Linux: /etc/opencode

2. 全局配置
   └── ~/.config/opencode/opencode.json

3. 项目配置
   └── .opencode/opencode.json

4. 默认配置 (最低优先级)
```

### 配置 Schema

```typescript
export const PluginSpec = z.union([
  z.string(),
  z.tuple([z.string(), PluginOptions])
])

export type PluginOrigin = {
  spec: PluginSpec
  source: string
  scope: PluginScope
}
```

### MDM 集成

```typescript
export function parseManagedPlist(json: string, source: string): Info {
  // 解析 macOS MDM 配置
}
```

### 配置热重载

通过 Bus 系统实现配置变更通知：

```typescript
Bus.publish(Config.Event.Changed, { config })
```

---

## Effect 系统集成

### Service 定义模式

```typescript
export class Service extends ServiceMap.Service<Service, Interface>()("@opencode/ServiceName") {}
```

### Layer 组合

```typescript
export const layer: Layer.Layer<
  Service,
  never,
  Dependency1 | Dependency2
> = Layer.effect(Service, Effect.gen(function* () {
  const dep1 = yield* Dependency1.Service
  const dep2 = yield* Dependency2.Service
  
  return {
    method: Effect.fn("Service.method")(function* (input) {
      // 实现
    })
  }
}))
```

### Runtime 创建

**文件**: `packages/opencode/src/effect/run-service.ts`

```typescript
export function makeRuntime<L extends Layer.Layer<any, any, any>>(
  layer: L
): Effect.Effect<Layer.Layer.Success<L>, never, never>
```

### InstanceState

**文件**: `packages/opencode/src/effect/instance-state.ts`

```typescript
export const InstanceState = {
  make: <T>(init: Effect.Effect<T, E, R>) => 
    Effect.Effect<{
      get: () => Effect.Effect<T>
      set: (value: T) => Effect.Effect<void>
      modify: (f: (t: T) => T) => Effect.Effect<T>
    }, E, R>
}
```

---

## 最佳实践与设计模式

### 1. 命名空间模式

所有核心模块使用 TypeScript 命名空间组织：

```typescript
export namespace Session {
  export interface Info { ... }
  export function create(): Promise<Info> { ... }
}
```

### 2. 类型安全的 Schema

使用 Zod 定义所有数据结构：

```typescript
export const Info = z.object({
  id: z.string(),
  name: z.string(),
}).meta({ ref: "Info" })
```

### 3. 事件驱动架构

```typescript
export const Event = {
  Created: BusEvent.define("session.created", Session.Info),
  Updated: BusEvent.define("session.updated", Session.Info),
  Deleted: BusEvent.define("session.deleted", Session.Info),
}
```

### 4. 错误处理

使用命名错误类型：

```typescript
export const NotFoundError = NamedError.create(
  "NotFoundError",
  z.object({ message: z.string() })
)
```

### 5. 懒加载模式

```typescript
export const Default = lazy(() => ControlPlaneRoutes())
```

### 6. 函数式错误处理

```typescript
Effect.gen(function* () {
  const result = yield* Effect.try({
    try: () => riskyOperation(),
    catch: (error) => new OperationError({ cause: error })
  })
  return result
})
```

### 7. 依赖注入

通过 Effect Layer 实现依赖注入：

```typescript
const program = Effect.gen(function* () {
  const session = yield* Session.Service
  const config = yield* Config.Service
  // ...
})

Effect.runFork(program.pipe(
  Effect.provide(Layer.mergeAll(
    Session.layer,
    Config.layer,
  ))
))
```

### 8. 流式处理

```typescript
Stream.fromIterable(items).pipe(
  Stream.map(processItem),
  Stream.filter(isValid),
  Stream.runCollect
)
```

---

## 总结

OpenCode 是一个设计精良的 AI 编程助手系统，从 Harness Engineer 角度来看，它具有以下特点：

1. **模块化架构**: 清晰的关注点分离，每个模块职责单一
2. **类型安全**: 全面使用 TypeScript 和 Zod 确保类型安全
3. **函数式设计**: 采用 Effect 框架实现函数式响应式编程
4. **可扩展性**: 插件系统和提供者系统支持灵活扩展
5. **企业级特性**: 完善的权限管理、配置管理和审计能力
6. **多平台支持**: CLI、Web、Desktop 多端统一架构
7. **CI/CD 完善**: 自动化测试、构建、发布流程

对于想要深入理解或贡献 OpenCode 的开发者，建议从以下路径入手：

1. **入门**: 阅读 `packages/opencode/src/index.ts` 理解 CLI 入口
2. **核心**: 研究 `session/` 目录理解会话管理
3. **工具**: 查看 `tool/` 目录理解工具系统
4. **扩展**: 学习 `plugin/` 目录理解插件机制
5. **部署**: 研究 `.github/workflows/` 理解 CI/CD 流程
