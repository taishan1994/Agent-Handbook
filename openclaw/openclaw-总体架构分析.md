# OpenClaw 架构分析文档

## 项目概述

OpenClaw 是一个个人 AI 助手系统，运行在用户自己的设备上，支持多种消息渠道和平台。它采用模块化架构，通过插件和技能系统提供高度可扩展的能力。

### 核心特性
- 多渠道支持：WhatsApp、Telegram、Slack、Discord、Google Chat、Signal、iMessage、BlueBubbles、IRC、Microsoft Teams、Matrix、Feishu、LINE、Mattermost、Nextcloud Talk、Nostr、Synology Chat、Tlon、Twitch、Zalo 等
- 跨平台支持：macOS、iOS、Android、Linux、Windows（WSL2）
- 浏览器自动化：基于 Playwright 的网页操作能力
- 语音交互：支持 macOS/iOS/Android 的语音输入输出
- Canvas 渲染：实时可控制的画布界面
- 插件系统：丰富的扩展能力

## 整体架构

### 架构层次

```
┌─────────────────────────────────────────────────────────────┐
│                    用户交互层                              │
│  CLI / Web UI / Mobile Apps / Messaging Channels          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Gateway 网关层                           │
│  WebSocket Server / HTTP Server / Session Management       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  核心服务层                               │
│  Channels / Plugins / Skills / Browser / Media          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  基础设施层                               │
│  Config / Process / Hooks / Logging / Security          │
└─────────────────────────────────────────────────────────────┘
```

## 核心模块详解

### 1. Gateway 网关模块 (`src/gateway/`)

网关是 OpenClaw 的核心服务器，负责协调所有组件的交互。

**主要组件：**
- **服务器实现** (`server/`): WebSocket 和 HTTP 服务器
  - WebSocket 连接管理
  - HTTP 路由处理
  - 认证和授权
  - 健康检查和就绪状态

- **协议定义** (`protocol/`): 通信协议和模式定义
  - Schema 定义
  - 消息格式
  - 错误码

- **服务器方法** (`server-methods/`): 各种功能实现
  - `agent.ts` - Agent 交互
  - `chat.ts` - 聊天处理
  - `channels.ts` - 渠道管理
  - `browser.ts` - 浏览器控制
  - `config.ts` - 配置管理
  - `secrets.ts` - 密钥管理
  - `models.ts` - 模型管理
  - `skills.ts` - 技能管理
  - `exec-approval.ts` - 执行批准

- **安全机制**：
  - 认证模式策略 (`auth-mode-policy.ts`)
  - 连接认证 (`connection-auth.ts`)
  - 设备认证 (`device-auth.ts`)
  - 安全路径 (`security-path.ts`)

### 2. Channels 渠道模块 (`src/channels/`)

负责与各种消息平台的集成和消息路由。

**核心功能：**
- **渠道注册表** (`registry.ts`): 管理所有可用渠道
- **消息处理**:
  - 入站消息标准化 (`plugins/normalize/`)
  - 出站消息发送 (`plugins/outbound/`)
  - 消息动作处理 (`plugins/message-actions.ts`)

- **会话管理**:
  - 会话绑定 (`thread-bindings/`)
  - 会话状态 (`session.ts`)
  - 目标解析 (`targets.ts`)

- **访问控制**:
  - 允许列表匹配 (`allowlist-match.ts`)
  - 提及控制 (`mention-gating.ts`)
  - 命令控制 (`command-gating.ts`)
  - 组策略 (`group-policy-warnings.ts`)

**支持的平台：**
- Telegram (`telegram/`)
- Slack (`plugins/outbound/slack.ts`)
- Discord (`plugins/outbound/discord.ts`)
- Signal (`plugins/outbound/signal.ts`)
- iMessage (`plugins/outbound/imessage.ts`)
- WhatsApp Web (`web/`)

### 3. Plugins 插件系统 (`src/plugins/`)

提供可扩展的功能模块，支持动态加载和配置。

**核心组件：**
- **插件注册表** (`registry.ts`): 管理已安装的插件
- **插件加载器** (`loader.ts`): 动态加载插件
- **运行时** (`runtime/`): 插件运行时环境
  - 核心类型 (`types-core.ts`)
  - 渠道类型 (`types-channel.ts`)
  - 配置运行时 (`runtime-config.ts`)
  - 系统运行时 (`runtime-system.ts`)
  - 媒体运行时 (`runtime-media.ts`)
  - 工具运行时 (`runtime-tools.ts`)

- **钩子系统** (`hooks.ts`): 插件生命周期钩子
- **工具系统** (`tools.ts`): 工具注册和管理
- **配置状态** (`config-state.ts`): 插件配置管理
- **HTTP 路由** (`http-registry.ts`): 插件 HTTP 路由注册

**插件类型：**
- 渠道插件（扩展消息平台）
- 工具插件（提供新能力）
- 内存插件（持久化存储）
- 认证插件（OAuth 集成）

### 4. Browser 浏览器模块 (`src/browser/`)

基于 Playwright 的浏览器自动化能力。

**主要功能：**
- **客户端管理** (`client.ts`): Playwright 客户端封装
- **会话管理** (`pw-session.ts`): 浏览器会话生命周期
- **配置文件** (`profiles.ts`): 浏览器配置文件管理
- **AI 工具** (`pw-ai.ts`): AI 辅助的浏览器操作

**路由系统** (`routes/`):
- 基本操作 (`basic.ts`)
- Agent 交互 (`agent.ts`)
- 存储操作 (`agent.storage.ts`)
- 快照功能 (`agent.snapshot.ts`)
- 调试功能 (`agent.debug.ts`)
- 标签页操作 (`tabs.ts`)
- 路径输出 (`path-output.ts`)

**安全特性：**
- CDP (Chrome DevTools Protocol) 认证
- HTTP 认证
- 扩展中继认证
- 控制平面安全

### 5. Media 媒体模块 (`src/media/`)

处理文件、图像、音频等媒体内容。

**核心功能：**
- **媒体存储** (`store.ts`): 媒体文件管理
- **媒体服务器** (`server.ts`): 媒体内容服务
- **文件解析** (`parse.ts`): 媒体类型识别
- **图像处理** (`image-ops.ts`): 图像操作
- **音频处理** (`audio.ts`): 音频转换
- **PDF 提取** (`pdf-extract.ts`): PDF 内容提取
- **Base64 处理** (`base64.ts`): 编码解码

**安全机制：**
- 入站路径策略 (`inbound-path-policy.ts`)
- MIME 类型检查 (`mime.ts`)
- 文件大小限制
- FFmpeg 执行限制

### 6. CLI 命令行模块 (`src/cli/`)

提供用户与系统交互的命令行界面。

**主要组件：**
- **程序构建** (`program/`): Commander.js 程序结构
  - 路由注册 (`routes.ts`)
  - 子命令注册 (`register.subclis.ts`)
  - 配置命令 (`register.configure.ts`)
  - Agent 命令 (`register.agent.ts`)
  - 消息命令 (`register.message/`)
  - 节点命令 (`nodes-cli/`)
  - 浏览器命令 (`browser-cli/`)

- **网关 CLI** (`gateway-cli/`): 网关管理命令
- **频道 CLI** (`channels-cli.ts`): 频道管理
- **插件 CLI** (`plugins-cli.ts`): 插件管理
- **技能 CLI** (`skills-cli.ts`): 技能管理

### 7. Infrastructure 基础设施模块 (`src/infra/`)

提供底层支撑功能。

**关键组件：**
- **配置管理**:
  - 环境变量 (`env.ts`)
  - Dotenv 加载 (`dotenv.ts`)
  - 配置加载 (`config/`)

- **进程管理**:
  - 执行包装器 (`exec-wrapper-resolution.ts`)
  - 执行安全 (`exec-safety.ts`)
  - 执行批准 (`exec-approvals.ts`)
  - 允许列表 (`exec-allowlist-pattern.ts`)

- **文件系统**:
  - 路径安全 (`path-safety.ts`)
  - 文件锁定 (`file-lock.ts`)
  - 档案路径 (`archive-path.ts`)

- **网络**:
  - 端口探测 (`ports-probe.ts`)
  - SSH 隧道 (`ssh-tunnel.ts`)
  - Bonjour 发现 (`bonjour.ts`)
  - Tailscale 集成 (`tailscale.ts`)

- **安全**:
  - 运行时守卫 (`runtime-guard.ts`)
  - 主机环境安全 (`host-env-security.policy.json`)
  - 凭证管理

### 8. Hooks 钩子系统 (`src/hooks/`)

提供系统生命周期钩子。

**钩子类型：**
- Gateway 钩子
- Agent 钩子
- LLM 钩子
- 消息钩子
- 会话钩子
- 子 Agent 钩子

**内置钩子** (`src/hooks/bundled/`):
- 命令日志 (`command-logger/`)
- 会话内存 (`session-memory/`)
- 启动额外文件 (`bootstrap-extra-files/`)
- 启动 Markdown (`boot-md/`)

### 9. Process 进程模块 (`src/process/`)

处理系统命令执行。

**主要功能：**
- 命令执行 (`exec.ts`)
- 命令包装 (`exec-wrapper.ts`)
- 执行限制
- 输出捕获
- 超时处理

## 扩展系统

### Extensions (`extensions/`)

第三方扩展，提供额外的渠道和功能。

**主要扩展：**
- **消息渠道**:
  - Matrix (`matrix/`)
  - Microsoft Teams (`msteams/`)
  - LINE (`line/`)
  - Nostr (`nostr/`)
  - Twitch (`twitch/`)
  - Zalo (`zalo/`)
  - Tlon (`tlon/`)
  - Feishu (`feishu/`)
  - Google Chat (`googlechat/`)

- **功能扩展**:
  - Voice Call (`voice-call/`)
  - Memory Core (`memory-core/`)
  - Memory LanceDB (`memory-lancedb/`)
  - Open Prose (`open-prose/`)
  - Lobster (`lobster/`)
  - Diffs (`diffs/`)
  - Device Pair (`device-pair/`)
  - Diagnostics OTEL (`diagnostics-otel/`)

- **认证扩展**:
  - Google Gemini CLI Auth (`google-gemini-cli-auth/`)
  - Qwen Portal Auth (`qwen-portal-auth/`)
  - Minimax Portal Auth (`minimax-portal-auth/`)

### Skills (`skills/`)

AI 助手的技能包，提供特定能力。

**内置技能：**
- Weather (`weather/`)
- GitHub (`github/`)
- Notion (`notion/`)
- Obsidian (`obsidian/`)
- Apple Notes (`apple-notes/`)
- Apple Reminders (`apple-reminders/`)
- 1Password (`1password/`)
- Slack (`slack/`)
- Discord (`discord/`)
- Trello (`trello/`)
- Spotify Player (`spotify-player/`)
- Canvas (`canvas/`)
- Voice Call (`voice-call/`)
- OpenAI Image Gen (`openai-image-gen/`)
- Model Usage (`model-usage/`)
- Coding Agent (`coding-agent/`)
- ClawHub (`clawhub/`)

## 移动应用 (`apps/`)

### iOS 应用 (`apps/ios/`)
- Swift 实现
- Watch App 支持
- Activity Widget
- Fastlane 自动化

### Android 应用 (`apps/android/`)
- Kotlin 实现
- Gradle 构建系统
- Material Design

### macOS 应用 (`apps/macos/`)
- Swift 实现
- OpenClawKit 共享框架
- 设备模型支持

## Web UI (`ui/`)

- 基于 React 的 Web 界面
- Vite 构建系统
- TypeScript 支持
- 实时通信

## 数据流

### 消息处理流程

```
用户消息 (Channel)
    ↓
消息标准化 (normalize)
    ↓
访问控制检查 (allowlist/mention-gating)
    ↓
会话绑定 (thread-bindings)
    ↓
Gateway 接收 (WebSocket/HTTP)
    ↓
Agent 处理 (LLM + Tools)
    ↓
工具执行 (Browser/Exec/Media)
    ↓
响应生成
    ↓
出站发送 (outbound)
    ↓
用户接收 (Channel)
```

### 插件加载流程

```
插件安装 (npm install)
    ↓
清单解析 (manifest.ts)
    ↓
依赖检查 (native-deps.ts)
    ↓
配置验证 (config-schema.ts)
    ↓
运行时注册 (runtime/)
    ↓
钩子注册 (hooks.ts)
    ↓
工具注册 (tools.ts)
    ↓
HTTP 路由注册 (http-registry.ts)
    ↓
插件就绪
```

## 安全架构

### 安全层级

1. **认证层**:
   - 设备认证
   - 连接认证
   - OAuth 集成
   - API 密钥管理

2. **授权层**:
   - 允许列表
   - 角色控制
   - 命令门控
   - 组策略

3. **执行层**:
   - 命令批准
   - 执行包装器
   - 路径安全
   - 沙箱限制

4. **数据层**:
   - 密钥加密
   - 安全存储
   - 传输加密 (TLS)
   - 输入验证

### 安全策略

- **默认安全**: 强安全默认值
- **显式控制**: 风险操作需要显式批准
- **最小权限**: 最小权限原则
- **审计日志**: 完整的操作审计

## 配置管理

### 配置层次

1. **全局配置** (`config/config.ts`)
   - Gateway 设置
   - 模型配置
   - 渠道配置
   - 插件配置

2. **会话配置** (`config/sessions.ts`)
   - 会话状态
   - 用户偏好
   - 临时设置

3. **插件配置**
   - 插件特定配置
   - 运行时配置
   - 用户自定义

### 配置存储

- 文件系统 (`~/.openclaw/`)
- 环境变量
- 密钥管理 (`secrets/`)
- 数据库（可选）

## 测试架构

### 测试类型

1. **单元测试** (`*.test.ts`)
   - 组件测试
   - 函数测试
   - 工具测试

2. **集成测试** (`*.integration.test.ts`)
   - 模块集成
   - API 测试
   - 数据流测试

3. **端到端测试** (`*.e2e.test.ts`)
   - 完整流程
   - 用户场景
   - 跨模块测试

4. **实时测试** (`*.live.test.ts`)
   - 外部服务集成
   - 真实 API 调用
   - 网络测试

### 测试工具

- Vitest: 测试框架
- Playwright: 浏览器测试
- Mock 工具: 模拟外部依赖
- 测试夹具: 测试数据

## 部署架构

### 部署方式

1. **本地部署**
   - npm 全局安装
   - 开发模式运行
   - 系统服务 (launchd/systemd)

2. **容器部署**
   - Docker 镜像
   - Docker Compose
   - Kubernetes

3. **移动部署**
   - App Store (iOS)
   - Google Play (Android)
   - TestFlight

### 守护进程

- **macOS**: launchd
- **Linux**: systemd
- **Windows**: Windows Service
- **Docker**: 容器重启策略

## 性能优化

### 优化策略

1. **缓存机制**
   - 配置缓存
   - 媒体缓存
   - 目录缓存
   - 会话缓存

2. **并发控制**
   - 异步处理
   - 队列管理
   - 连接池
   - 限流

3. **资源管理**
   - 内存限制
   - 文件句柄管理
   - 连接超时
   - 清理机制

### 监控指标

- 性能指标
- 错误率
- 响应时间
- 资源使用

## 技术栈

### 核心技术

- **运行时**: Node.js 22+
- **语言**: TypeScript
- **包管理**: pnpm / Bun
- **构建**: tsdown / Vite

### 主要依赖

- **Web 框架**: Express
- **WebSocket**: ws
- **浏览器自动化**: Playwright
- **CLI**: Commander.js
- **日志**: 自定义日志系统
- **配置**: dotenv + JSON5
- **验证**: AJV
- **媒体**: FFmpeg, pdfjs-dist

### 渠道 SDK

- **WhatsApp**: @whiskeysockets/baileys
- **Telegram**: grammy
- **Slack**: @slack/bolt
- **Discord**: discord.js
- **Signal**: libsignal
- **Matrix**: matrix-js-sdk

## 开发工作流

### 开发命令

```bash
# 安装依赖
pnpm install

# 开发模式
pnpm dev

# 构建
pnpm build

# 测试
pnpm test

# Lint
pnpm lint

# 类型检查
pnpm tsgo
```

### Git 工作流

- 功能分支开发
- Pull Request 审查
- CI/CD 自动化
- 语义化版本

## 文档结构

- `docs/`: 用户文档
- `docs/zh-CN/`: 中文文档（自动生成）
- `SKILL.md`: 技能文档
- `README.md`: 项目说明
- `AGENTS.md`: Agent 指南
- `VISION.md`: 项目愿景

## 总结

OpenClaw 采用高度模块化的架构设计，通过清晰的层次划分和插件系统实现了强大的可扩展性。核心架构包括：

1. **Gateway 网关层**: 协调所有组件的核心服务器
2. **Channels 渠道层**: 多平台消息集成
3. **Plugins 插件层**: 可扩展的功能模块
4. **Browser 浏览器层**: 网页自动化能力
5. **Media 媒体层**: 文件和媒体处理
6. **Infrastructure 基础设施层**: 底层支撑功能
7. **CLI 命令行层**: 用户交互界面

这种架构设计使得 OpenClaw 能够：
- 支持多种消息平台
- 提供丰富的 AI 能力
- 保持高度可扩展性
- 确保安全性
- 跨平台运行

通过插件和技能系统，开发者可以轻松扩展 OpenClaw 的功能，而无需修改核心代码。这使得 OpenClaw 成为一个强大且灵活的个人 AI 助手平台。