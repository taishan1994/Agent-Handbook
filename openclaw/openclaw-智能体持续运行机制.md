# OpenClaw智能体持续运行机制

## 概述

OpenClaw通过多种机制确保智能体能够持续运行并保持活跃状态。这些机制包括心跳检测、自动回复、后台进程、消息监听和定时任务等，共同构成了一个完整的智能体生命周期管理系统。

## 核心运行机制

### 1. 心跳机制（Heartbeat）

心跳是OpenClaw让智能体保持活跃的核心机制。它定期触发智能体运行，让智能体能够主动检查和处理任务。

#### 心跳工作原理

```typescript
// 心跳调度流程
1. 配置心跳间隔（默认30分钟）
2. 启动心跳调度器
3. 定期触发智能体运行
4. 智能体执行检查任务
5. 返回结果或HEARTBEAT_OK
```

#### 心跳配置

```json5
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "30m",           // 心跳间隔
        "target": "last",          // 消息目标
        "prompt": "Read HEARTBEAT.md if it exists...", // 心跳提示词
        "activeHours": {            // 活跃时间窗口
          "start": "08:00",
          "end": "24:00",
          "timezone": "Asia/Shanghai"
        },
        "lightContext": true,        // 轻量级上下文
        "includeReasoning": false    // 是否包含推理
      }
    }
  }
}
```

#### 心跳触发条件

心跳在以下情况下触发：

- **定时触发**: 按照配置的间隔定期触发
- **外部唤醒**: 通过API或事件触发
- **Cron触发**: 作为Cron任务的一部分
- **手动触发**: 通过命令行或API手动触发

#### HEARTBEAT.md检查清单

智能体在每次心跳时会读取工作区的`HEARTBEAT.md`文件：

```markdown
# Heartbeat checklist

- 检查邮件中的紧急消息
- 查看未来2小时内的日历事件
- 如果后台任务完成，总结结果
- 如果空闲超过8小时，发送简短问候
- 检查系统状态和错误日志
- 更新项目进度
```

#### 心跳响应协议

智能体对心跳的响应遵循特定协议：

- **无任务时**: 返回`HEARTBEAT_OK`
- **有任务时**: 返回任务描述和结果
- **紧急任务**: 直接返回警报信息

```typescript
// 心跳响应处理
if (response.includes("HEARTBEAT_OK")) {
  // 无需关注的任务，不发送消息
  if (response.length <= ackMaxChars) {
    dropMessage();
  }
} else {
  // 发送消息
  deliverMessage(response);
}
```

### 2. 自动回复机制（Auto-reply）

自动回复机制让智能体能够实时响应传入的消息，保持持续的交互能力。

#### 自动回复工作流程

```typescript
// 自动回复流程
1. 监听消息通道（Discord/WhatsApp/Web等）
2. 接收传入消息
3. 消息预处理和验证
4. 路由到智能体
5. 智能体生成回复
6. 发送回复
7. 等待下一条消息
```

#### 消息监听器

OpenClaw为每个消息通道实现专门的消息监听器：

##### Discord消息监听

```typescript
// Discord消息处理
async function processDiscordMessage(ctx: DiscordMessagePreflightContext) {
  // 1. 预检查
  const preflight = await preflightDiscordMessage(ctx);
  
  // 2. 消息处理
  const result = await processDiscordMessage(ctx);
  
  // 3. 回复交付
  await deliverDiscordReply(result);
  
  // 4. 状态更新
  updateStatus(result);
}
```

##### WhatsApp消息监听

```typescript
// WhatsApp消息监听
async function monitorWebInbox(options: {
  verbose: boolean;
  accountId: string;
  authDir: string;
  onMessage: (msg: WebInboundMessage) => Promise<void>;
  mediaMaxMb?: number;
  sendReadReceipts?: boolean;
  debounceMs?: number;
}) {
  // 1. 创建WebSocket连接
  const sock = await createWaSocket(false, options.verbose);
  
  // 2. 等待连接建立
  await waitForWaConnection(sock);
  
  // 3. 发送在线状态
  await sock.sendPresenceUpdate("available");
  
  // 4. 监听消息
  sock.ev.on("messages.upsert", async (messages) => {
    for (const msg of messages) {
      await options.onMessage(msg);
    }
  });
  
  // 5. 保持连接
  await waitForConnectionClose();
}
```

##### Web消息监听

```typescript
// Web消息监听
async function monitorWebInbox(options: {
  onMessage: (msg: WebInboundMessage) => Promise<void>;
  mediaMaxMb?: number;
  sendReadReceipts?: boolean;
  debounceMs?: number;
}) {
  // 1. 创建连接
  const sock = await createWaSocket(false, options.verbose);
  
  // 2. 设置消息处理器
  sock.ev.on("messages.upsert", async (messages) => {
    // 3. 消息去重
    const uniqueMessages = dedupeMessages(messages);
    
    // 4. 批量处理
    for (const msg of uniqueMessages) {
      await options.onMessage(msg);
    }
  });
  
  // 5. 保持监听
  await keepAlive();
}
```

#### 消息去重和防抖

```typescript
// 消息去重
function isRecentInboundMessage(msg: WebInboundMessage): boolean {
  const recentMessages = getRecentMessages();
  return recentMessages.some(recent => 
    recent.from === msg.from && 
    recent.body === msg.body &&
    (Date.now() - recent.timestamp) < 5000
  );
}

// 消息防抖
function createInboundDebouncer<T>(options: {
  debounceMs: number;
  buildKey: (msg: T) => string | null;
  onFlush: (entries: T[]) => Promise<void>;
}) {
  const batches = new Map<string, T[]>();
  
  return {
    add: (msg: T) => {
      const key = options.buildKey(msg);
      if (!key) return;
      
      const batch = batches.get(key) ?? [];
      batch.push(msg);
      batches.set(key, batch);
      
      // 延迟处理
      setTimeout(() => {
        options.onFlush(batch);
        batches.delete(key);
      }, options.debounceMs);
    }
  };
}
```

#### 消息分发

```typescript
// 消息分发
async function dispatchInboundMessage(params: {
  ctx: MsgContext | FinalizedMsgContext;
  cfg: OpenClawConfig;
  dispatcher: ReplyDispatcher;
  replyOptions?: GetReplyOptions;
}): Promise<DispatchInboundResult> {
  // 1. 完成上下文
  const finalized = finalizeInboundContext(params.ctx);
  
  // 2. 获取回复
  const result = await dispatchReplyFromConfig({
    ctx: finalized,
    cfg: params.cfg,
    dispatcher: params.dispatcher,
    replyOptions: params.replyOptions,
  });
  
  // 3. 返回结果
  return result;
}
```

### 3. 后台进程（Daemon/Service）

OpenClaw通过系统服务机制确保智能体作为后台进程持续运行。

#### 系统服务集成

##### Linux (systemd)

```bash
# 安装systemd服务
openclaw onboard --install-daemon

# 启动服务
systemctl --user start openclaw-gateway

# 启用开机自启
systemctl --user enable openclaw-gateway

# 查看状态
systemctl --user status openclaw-gateway
```

systemd服务配置：

```ini
[Unit]
Description=OpenClaw Gateway
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/node /path/to/openclaw.mjs gateway
Restart=always
RestartSec=10
User=openclaw

[Install]
WantedBy=default.target
```

##### macOS (launchd)

```bash
# 安装launchd服务
openclaw onboard --install-daemon

# 启动服务
launchctl start com.openclaw.gateway

# 查看状态
launchctl list | grep openclaw
```

launchd配置：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.gateway</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/node</string>
        <string>/path/to/openclaw.mjs</string>
        <string>gateway</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/openclaw-gateway.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/openclaw-gateway.err</string>
</dict>
</plist>
```

##### Windows (Windows Service)

```bash
# 安装Windows服务
openclaw onboard --install-daemon

# 启动服务
sc start OpenClawGateway

# 配置自动启动
sc config OpenClawGateway start= auto

# 查看状态
sc query OpenClawGateway
```

#### 服务持久化

```typescript
// 服务持久化配置
async function ensureServicePersistence() {
  // 1. 检查服务是否已安装
  const isInstalled = await service.isInstalled();
  
  if (!isInstalled) {
    // 2. 安装服务
    await service.install({
      name: "openclaw-gateway",
      command: "node openclaw.mjs gateway",
      autoStart: true,
      restartOnFailure: true,
    });
  }
  
  // 3. 启动服务
  await service.start();
  
  // 4. 确保服务运行
  await waitForServiceReady();
}
```

#### 进程监控和重启

```typescript
// 进程监控
async function monitorProcess() {
  while (true) {
    const status = await checkProcessStatus();
    
    if (!status.isRunning) {
      log.error("Process died, restarting...");
      await restartProcess();
    }
    
    await sleep(5000); // 每5秒检查一次
  }
}

// 自动重启
async function restartProcess() {
  // 1. 清理资源
  await cleanupResources();
  
  // 2. 重启进程
  const pid = await spawnProcess();
  
  // 3. 更新状态
  updateProcessStatus(pid);
  
  // 4. 通知监控
  notifyRestart();
}
```

### 4. Cron定时任务

Cron任务提供精确的定时执行能力，补充心跳机制。

#### Cron配置

```json5
{
  "cron": {
    "jobs": [
      {
        "id": "daily-report",
        "schedule": "0 9 * * *", // 每天9点
        "prompt": "生成每日报告",
        "model": "anthropic/claude-opus-4-6"
      },
      {
        "id": "weekly-cleanup",
        "schedule": "0 2 * * 0", // 每周日凌晨2点
        "prompt": "清理临时文件和日志",
        "session": "main"
      }
    ]
  }
}
```

#### Cron执行流程

```typescript
// Cron调度
async function scheduleCronJobs() {
  const jobs = loadCronJobs();
  
  for (const job of jobs) {
    // 1. 解析cron表达式
    const schedule = parseCronExpression(job.schedule);
    
    // 2. 设置定时器
    setInterval(async () => {
      if (schedule.shouldRun()) {
        // 3. 执行任务
        await executeCronJob(job);
      }
    }, 60000); // 每分钟检查
  }
}

// 执行Cron任务
async function executeCronJob(job: CronJob) {
  // 1. 创建会话
  const sessionKey = job.session ?? `cron:${job.id}`;
  
  // 2. 执行智能体
  const result = await runAgent({
    prompt: job.prompt,
    model: job.model,
    sessionKey,
  });
  
  // 3. 处理结果
  if (job.delivery === "announce") {
    await announceResult(result);
  }
}
```

#### Cron与Heartbeat的区别

| 特性 | Heartbeat | Cron |
|------|-----------|------|
| 触发方式 | 定期间隔 | 精确时间 |
| 上下文 | 主会话上下文 | 独立会话 |
| 灵活性 | 上下文感知 | 精确控制 |
| 用途 | 监控和检查 | 定时任务 |

### 5. 连接保持和重连

OpenClaw实现了智能的连接保持和重连机制。

#### 连接健康检查

```typescript
// 连接健康检查
async function checkConnectionHealth() {
  const status = {
    connected: false,
    lastPing: 0,
    latency: 0,
    errors: []
  };
  
  // 1. 发送ping
  const pingStart = Date.now();
  try {
    await sendPing();
    status.connected = true;
    status.lastPing = Date.now();
    status.latency = Date.now() - pingStart;
  } catch (err) {
    status.errors.push({
      timestamp: Date.now(),
      error: err.message
    });
  }
  
  return status;
}
```

#### 自动重连策略

```typescript
// 重连策略
interface ReconnectPolicy {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffFactor: number;
  jitter: number;
}

async function reconnectWithBackoff(policy: ReconnectPolicy) {
  let attempt = 0;
  let delay = policy.initialDelayMs;
  
  while (attempt < policy.maxAttempts) {
    attempt++;
    
    try {
      // 1. 尝试连接
      await establishConnection();
      log.info(`Reconnected after ${attempt} attempts`);
      return;
    } catch (err) {
      // 2. 计算延迟
      delay = Math.min(
        delay * policy.backoffFactor,
        policy.maxDelayMs
      );
      
      // 3. 添加抖动
      const jitter = delay * policy.jitter;
      delay += (Math.random() - 0.5) * jitter;
      
      // 4. 等待
      log.warn(`Reconnect attempt ${attempt} failed, retrying in ${delay}ms`);
      await sleep(delay);
    }
  }
  
  throw new Error(`Failed to reconnect after ${policy.maxAttempts} attempts`);
}
```

#### 心跳保持

```typescript
// WebSocket心跳
async function maintainWebSocketHeartbeat(ws: WebSocket) {
  const heartbeatInterval = 30000; // 30秒
  
  setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
      try {
        ws.ping();
        logVerbose("WebSocket ping sent");
      } catch (err) {
        log.error("WebSocket ping failed:", err);
        // 触发重连
        triggerReconnect();
      }
    }
  }, heartbeatInterval);
}
```

### 6. 消息队列和并发控制

OpenClaw使用消息队列和并发控制来处理高负载情况。

#### 消息队列

```typescript
// 消息队列
class MessageQueue {
  private queue: Message[] = [];
  private processing = false;
  
  async enqueue(message: Message): Promise<void> {
    this.queue.push(message);
    
    if (!this.processing) {
      this.processing = true;
      await this.processQueue();
    }
  }
  
  private async processQueue(): Promise<void> {
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      
      try {
        await processMessage(message);
      } catch (err) {
        log.error("Failed to process message:", err);
        // 重试或丢弃
      }
    }
    
    this.processing = false;
  }
}
```

#### 并发控制

```typescript
// 并发控制器
class ConcurrencyController {
  private activeRuns = 0;
  private maxConcurrent: number;
  private queue: Array<() => Promise<void>> = [];
  
  constructor(maxConcurrent: number) {
    this.maxConcurrent = maxConcurrent;
  }
  
  async run<T>(task: () => Promise<T>): Promise<T> {
    // 等待可用槽位
    await this.waitForSlot();
    
    this.activeRuns++;
    try {
      return await task();
    } finally {
      this.activeRuns--;
      this.processQueue();
    }
  }
  
  private async waitForSlot(): Promise<void> {
    if (this.activeRuns < this.maxConcurrent) {
      return;
    }
    
    return new Promise(resolve => {
      this.queue.push(resolve);
    });
  }
  
  private processQueue(): void {
    while (this.queue.length > 0 && this.activeRuns < this.maxConcurrent) {
      const resolve = this.queue.shift();
      resolve();
    }
  }
}
```

#### 忙碌状态管理

```typescript
// 忙碌状态
interface BusyState {
  activeRuns: number;
  busy: boolean;
  lastActivity: number;
  queueSize: number;
}

function updateBusyState(state: BusyState): void {
  state.activeRuns = getActiveRunCount();
  state.busy = state.activeRuns > 0;
  state.lastActivity = Date.now();
  state.queueSize = getQueueSize();
  
  // 通知状态更新
  emitStatusUpdate(state);
}

// 检查是否应该跳过心跳
function shouldSkipHeartbeat(state: BusyState): boolean {
  // 如果主队列忙碌，跳过心跳
  if (state.queueSize > 0) {
    return true;
  }
  
  // 如果有活跃运行，跳过心跳
  if (state.activeRuns > 0) {
    return true;
  }
  
  return false;
}
```

### 7. 会话持久化

OpenClaw通过会话持久化确保智能体状态在重启后能够恢复。

#### 会话存储

```typescript
// 会话存储
interface SessionEntry {
  sessionId: string;
  sessionKey: string;
  updatedAt: number;
  transcript: Message[];
  metadata: {
    agentId: string;
    model: string;
    context: any;
  };
}

async function saveSession(entry: SessionEntry): Promise<void> {
  // 1. 序列化会话
  const data = JSON.stringify(entry, null, 2);
  
  // 2. 写入文件
  await fs.writeFile(
    getSessionPath(entry.sessionKey),
    data,
    "utf8"
  );
  
  // 3. 更新索引
  updateSessionIndex(entry);
}

async function loadSession(sessionKey: string): Promise<SessionEntry | null> {
  // 1. 读取文件
  const data = await fs.readFile(
    getSessionPath(sessionKey),
    "utf8"
  );
  
  // 2. 解析数据
  const entry = JSON.parse(data);
  
  // 3. 验证完整性
  if (validateSession(entry)) {
    return entry;
  }
  
  return null;
}
```

#### 会话恢复

```typescript
// 会话恢复
async function restoreSession(sessionKey: string): Promise<void> {
  // 1. 加载会话
  const entry = await loadSession(sessionKey);
  
  if (!entry) {
    // 创建新会话
    await createNewSession(sessionKey);
    return;
  }
  
  // 2. 恢复上下文
  const context = buildContextFromSession(entry);
  
  // 3. 恢复智能体状态
  await restoreAgentState(context);
  
  // 4. 继续运行
  log.info(`Session ${sessionKey} restored`);
}
```

#### 会话压缩

```typescript
// 会话压缩
async function compactSession(sessionKey: string): Promise<void> {
  const entry = await loadSession(sessionKey);
  
  if (!entry) return;
  
  // 1. 分析会话历史
  const analysis = analyzeTranscript(entry.transcript);
  
  // 2. 决定是否需要压缩
  if (analysis.needsCompaction) {
    // 3. 生成摘要
    const summary = await generateSummary(entry.transcript);
    
    // 4. 压缩会话
    entry.transcript = [
      ...analysis.keepMessages,
      { role: "system", content: summary }
    ];
    
    // 5. 保存
    await saveSession(entry);
    
    log.info(`Session ${sessionKey} compacted`);
  }
}
```

### 8. 错误处理和恢复

OpenClaw实现了完善的错误处理和恢复机制。

#### 错误捕获

```typescript
// 全局错误处理
async function setupErrorHandling() {
  // 1. 未捕获的异常
  process.on('uncaughtException', async (err) => {
    log.error('Uncaught exception:', err);
    await handleCriticalError(err);
  });
  
  // 2. 未处理的Promise拒绝
  process.on('unhandledRejection', async (reason, promise) => {
    log.error('Unhandled rejection:', reason);
    await handleRejection(reason, promise);
  });
  
  // 3. 未捕获的异常（Promise）
  process.on('uncaughtExceptionMonitor', async (err) => {
    log.error('Uncaught exception monitor:', err);
    await handleCriticalError(err);
  });
}

// 错误处理
async function handleCriticalError(err: Error): Promise<void> {
  // 1. 记录错误
  await logError(err);
  
  // 2. 保存状态
  await saveCrashState();
  
  // 3. 通知
  await notifyError(err);
  
  // 4. 决定是否重启
  if (isRecoverable(err)) {
    await gracefulRestart();
  } else {
    await shutdown();
  }
}
```

#### 优雅重启

```typescript
// 优雅重启
async function gracefulRestart(): Promise<void> {
  log.info("Initiating graceful restart...");
  
  // 1. 停止接受新请求
  await stopAcceptingNewRequests();
  
  // 2. 等待当前请求完成
  await waitForActiveRequests();
  
  // 3. 保存状态
  await saveAllSessions();
  
  // 4. 关闭连接
  await closeAllConnections();
  
  // 5. 重启进程
  await restartProcess();
}

// 等待活跃请求完成
async function waitForActiveRequests(timeout: number = 30000): Promise<void> {
  const startTime = Date.now();
  
  while (getActiveRequestCount() > 0) {
    if (Date.now() - startTime > timeout) {
      log.warn("Timeout waiting for active requests");
      break;
    }
    
    await sleep(100);
  }
}
```

#### 状态恢复

```typescript
// 状态恢复
async function recoverFromCrash(): Promise<void> {
  // 1. 检查崩溃状态
  const crashState = await loadCrashState();
  
  if (!crashState) {
    log.info("No crash state found");
    return;
  }
  
  // 2. 分析崩溃原因
  const cause = analyzeCrash(crashState);
  
  // 3. 恢复会话
  for (const sessionKey of crashState.activeSessions) {
    await restoreSession(sessionKey);
  }
  
  // 4. 恢复消息队列
  await restoreMessageQueue(crashState.queue);
  
  // 5. 清理崩溃状态
  await clearCrashState();
  
  log.info("Recovery complete");
}
```

## 运行模式

### Gateway模式

Gateway模式是OpenClaw的主要运行模式，提供集中式的智能体管理。

#### Gateway启动

```bash
# 启动Gateway
openclaw gateway

# 后台运行
openclaw gateway --daemon

# 指定配置
openclaw gateway --config /path/to/config.json
```

#### Gateway架构

```typescript
// Gateway架构
class Gateway {
  private heartbeatRunner: HeartbeatRunner;
  private cronScheduler: CronScheduler;
  private messageListeners: Map<string, MessageListener>;
  private sessionManager: SessionManager;
  
  async start(): Promise<void> {
    // 1. 启动心跳
    this.heartbeatRunner.start();
    
    // 2. 启动Cron
    this.cronScheduler.start();
    
    // 3. 启动消息监听器
    for (const [channel, listener] of this.messageListeners) {
      await listener.start();
    }
    
    // 4. 启动会话管理
    this.sessionManager.start();
    
    log.info("Gateway started");
  }
  
  async stop(): Promise<void> {
    // 1. 停止心跳
    this.heartbeatRunner.stop();
    
    // 2. 停止Cron
    this.cronScheduler.stop();
    
    // 3. 停止消息监听器
    for (const listener of this.messageListeners.values()) {
      await listener.stop();
    }
    
    // 4. 保存会话
    await this.sessionManager.saveAll();
    
    log.info("Gateway stopped");
  }
}
```

### 单Agent模式

单Agent模式适用于简单的使用场景。

```bash
# 启动单Agent
openclaw agent

# 指定Agent ID
openclaw agent --agent main

# 交互模式
openclaw agent --interactive
```

## 监控和诊断

### 运行状态监控

```typescript
// 运行状态
interface RuntimeStatus {
  uptime: number;
  activeSessions: number;
  totalMessages: number;
  heartbeatCount: number;
  lastHeartbeat: number;
  cronJobs: number;
  errors: number;
}

async function getRuntimeStatus(): Promise<RuntimeStatus> {
  return {
    uptime: process.uptime(),
    activeSessions: getActiveSessionCount(),
    totalMessages: getTotalMessageCount(),
    heartbeatCount: getHeartbeatCount(),
    lastHeartbeat: getLastHeartbeatTime(),
    cronJobs: getCronJobCount(),
    errors: getErrorCount()
  };
}
```

### 健康检查

```typescript
// 健康检查
async function healthCheck(): Promise<HealthStatus> {
  const checks = {
    heartbeat: await checkHeartbeat(),
    messageListeners: await checkMessageListeners(),
    cron: await checkCron(),
    sessions: await checkSessions(),
    database: await checkDatabase()
  };
  
  const healthy = Object.values(checks).every(check => check.healthy);
  
  return {
    healthy,
    checks,
    timestamp: Date.now()
  };
}
```

### 日志和诊断

```typescript
// 日志记录
function logRuntimeEvent(event: RuntimeEvent): void {
  const logEntry = {
    timestamp: Date.now(),
    level: event.level,
    module: event.module,
    message: event.message,
    data: event.data
  };
  
  // 写入日志文件
  appendToLogFile(logEntry);
  
  // 发送到监控系统
  if (monitoringEnabled) {
    sendToMonitoring(logEntry);
  }
}
```

## 最佳实践

### 1. 配置优化

```json5
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "30m",           // 根据需求调整
        "activeHours": {            // 设置活跃时间
          "start": "08:00",
          "end": "24:00",
          "timezone": "Asia/Shanghai"
        },
        "lightContext": true         // 使用轻量级上下文
      }
    }
  },
  "cron": {
    "jobs": [
      {
        "id": "daily-summary",
        "schedule": "0 20 * * *",  // 每天晚上8点
        "prompt": "生成每日总结"
      }
    ]
  }
}
```

### 2. 监控设置

```bash
# 启用详细日志
export DEBUG=openclaw:*

# 监控日志
tail -f /tmp/openclaw/openclaw-gateway.log

# 检查服务状态
systemctl --user status openclaw-gateway
```

### 3. 错误处理

```typescript
// 自定义错误处理
async function customErrorHandler(err: Error): Promise<void> {
  // 1. 分类错误
  const category = classifyError(err);
  
  // 2. 记录详细信息
  await logDetailedError(err, category);
  
  // 3. 采取相应措施
  switch (category) {
    case "transient":
      // 临时错误，重试
      await retryOperation();
      break;
    case "configuration":
      // 配置错误，通知管理员
      await notifyAdmin(err);
      break;
    case "critical":
      // 严重错误，重启
      await restartService();
      break;
  }
}
```

### 4. 性能优化

```typescript
// 性能优化
async function optimizePerformance(): Promise<void> {
  // 1. 清理旧会话
  await cleanupOldSessions();
  
  // 2. 压缩大会话
  await compactLargeSessions();
  
  // 3. 清理缓存
  await clearCache();
  
  // 4. 优化数据库
  await optimizeDatabase();
}
```

## 故障排除

### 问题1: 智能体停止响应

**症状**: 智能体不再响应消息

**解决方案**:

```bash
# 1. 检查服务状态
systemctl --user status openclaw-gateway

# 2. 查看日志
tail -f /tmp/openclaw/openclaw-gateway.log

# 3. 重启服务
systemctl --user restart openclaw-gateway
```

### 问题2: 心跳未触发

**症状**: 心跳没有按预期触发

**解决方案**:

```bash
# 1. 检查配置
openclaw config show | grep heartbeat

# 2. 验证活跃时间
date

# 3. 手动触发心跳
openclaw heartbeat trigger
```

### 问题3: 连接频繁断开

**症状**: 消息通道连接不稳定

**解决方案**:

```json5
{
  "channels": {
    "discord": {
      "reconnect": {
        "maxAttempts": 10,
        "initialDelayMs": 1000,
        "maxDelayMs": 60000,
        "backoffFactor": 2
      }
    }
  }
}
```

### 问题4: 内存使用过高

**症状**: 进程内存持续增长

**解决方案**:

```typescript
// 定期清理
setInterval(async () => {
  // 1. 清理旧会话
  await cleanupOldSessions();
  
  // 2. 压缩会话
  await compactSessions();
  
  // 3. 清理缓存
  await clearCache();
}, 3600000); // 每小时
```

## 总结

OpenClaw通过多种机制确保智能体持续运行：

1. **心跳机制**: 定期触发智能体执行检查任务
2. **自动回复**: 实时响应传入消息
3. **后台进程**: 通过系统服务保持进程运行
4. **连接保持**: 智能重连和健康检查
5. **消息队列**: 处理高负载情况
6. **会话持久化**: 确保状态可恢复
7. **错误处理**: 完善的错误捕获和恢复
8. **Cron任务**: 精确的定时执行

这些机制共同工作，使OpenClaw智能体能够7x24小时稳定运行，持续提供服务。通过合理配置和监控，可以确保智能体在各种情况下都能保持活跃和响应。