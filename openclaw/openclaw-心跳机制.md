# OpenClaw心跳机制

## 概述

OpenClaw的心跳机制是一种智能的周期性任务调度系统，它使智能体能够在主会话中定期运行检查任务，主动发现并提醒用户需要关注的事项。心跳机制的设计理念是"主动感知"而非"被动响应"，让智能体成为真正的助手而非仅仅是一个问答工具。

## 心跳的核心概念

### 什么是心跳

心跳是OpenClaw在智能体主会话中运行的周期性智能体轮次。与传统的定时任务不同，心跳具有以下特点：

- **上下文感知**：运行在主会话中，拥有完整的对话历史和上下文
- **智能决策**：可以根据当前状态判断什么是紧急的，什么可以等待
- **批量处理**：一次心跳可以同时检查多个事项（收件箱、日历、通知等）
- **自然抑制**：如果没有需要关注的事项，智能体回复`HEARTBEAT_OK`，不会打扰用户

### 默认行为

OpenClaw的心跳默认配置为：

- **间隔**：30分钟（当使用Anthropic OAuth/setup-token时默认为1小时）
- **目标**：`last`（发送到最后使用的外部渠道）
- **提示**：读取HEARTBEAT.md文件并遵循其指示

## 心跳配置

### 基本配置

心跳配置位于`agents.defaults.heartbeat`或单个智能体的`heartbeat`块中：

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",           // 心跳间隔
        target: "last",         // 消息发送目标
        model: "anthropic/claude-opus-4-5",  // 可选的模型覆盖
        includeReasoning: false, // 是否发送推理内容
        prompt: "Read HEARTBEAT.md if it exists...",  // 自定义提示
        ackMaxChars: 300,       // HEARTBEAT_OK后允许的最大字符数
        lightContext: false,    // 是否只注入HEARTBEAT.md
        activeHours: {          // 活动时段限制
          start: "08:00",
          end: "22:00",
          timezone: "America/New_York"
        }
      }
    }
  }
}
```

### 配置字段详解

#### `every` - 心跳间隔

- 格式：时长字符串（默认单位为分钟）
- 示例：`"30m"`、`"1h"`、`"2h"`
- 特殊值：`"0m"`表示禁用心跳

#### `target` - 消息发送目标

- `"last"`（默认）：发送到最后使用的外部渠道
- `"none"`：运行心跳但不发送到外部
- 显式渠道：`"whatsapp"`、`"telegram"`、`"discord"`等

#### `to` - 收件人覆盖

- 渠道特定的收件人ID
- 示例：WhatsApp的E.164号码（`"+15551234567"`）
- Telegram的聊天ID

#### `prompt` - 心跳提示

- 默认提示：`"Read HEARTBEAT.md if it exists (workspace context). Follow it strictly. Do not infer or repeat old tasks from prior chats. If nothing needs attention, reply HEARTBEAT_OK."`
- 可以完全自定义，不与默认提示合并

#### `model` - 模型覆盖

- 为心跳运行指定不同的模型
- 格式：`"provider/model"`，如`"anthropic/claude-opus-4-5"`
- 可用于成本优化（使用更便宜的模型）或质量提升（使用更强的模型）

#### `includeReasoning` - 推理内容发送

- 默认：`false`
- 启用后会发送单独的`Reasoning:`消息
- 适用于需要透明度的场景，但在群聊中建议关闭

#### `lightContext` - 轻量级上下文

- 默认：`false`
- 启用后只注入`HEARTBEAT.md`，不注入其他引导文件
- 适用于心跳只需要HEARTBEAT.md的场景

#### `ackMaxChars` - 确认消息长度限制

- 默认：300字符
- 当回复包含`HEARTBEAT_OK`时，剩余内容超过此长度会被发送
- 用于控制"无事发生"时的详细程度

#### `activeHours` - 活动时段

```json5
{
  "activeHours": {
    "start": "08:00",
    "end": "22:00",
    "timezone": "America/New_York"
  }
}
```

- `start`：开始时间（HH:MM格式）
- `end`：结束时间（HH:MM格式，支持`24:00`）
- `timezone`：时区（可选，默认使用用户时区）
- 在活动时段外，心跳会被跳过

### 单智能体心跳

如果任何`agents.list[]`条目包含`heartbeat`块，**只有这些智能体**运行心跳：

```json5
{
  agents: {
    defaults: {
      heartbeat: {
        every: "30m",
        target: "last"
      }
    },
    list: [
      { id: "main", default: true },  // 不运行心跳
      {
        id: "ops",
        heartbeat: {  // 运行心跳
          every: "1h",
          target: "whatsapp",
          to: "+15551234567"
        }
      }
    ]
  }
}
```

## HEARTBEAT.md检查清单

### 文件作用

`HEARTBEAT.md`是智能体工作区中的一个可选文件，作为心跳的检查清单。当此文件存在时，默认提示会告诉智能体读取并严格遵循它。

### 文件位置

- 路径：`~/.openclaw/workspace/HEARTBEAT.md`
- 作为工作区引导文件的一部分注入到上下文中

### 内容示例

```md
# Heartbeat checklist

- Quick scan: anything urgent in inboxes?
- Check calendar for events in next 2 hours
- If a background task finished, summarize results
- If idle for 8+ hours, send a brief check-in
- If a task is blocked, write down what is missing
```

### 最佳实践

1. **保持简洁**：文件应该小巧，避免提示膨胀
2. **明确具体**：使用清晰、可执行的指令
3. **避免重复**：不要让智能体重复之前聊天中的任务
4. **定期更新**：根据实际需求调整检查清单

### 空文件优化

如果`HEARTBEAT.md`存在但实际上是空的（只有空行和markdown标题），OpenClaw会跳过心跳运行以节省API调用。这是一个重要的优化机制。

### 智能体更新HEARTBEAT.md

智能体可以更新`HEARTBEAT.md`文件，如果用户要求它这样做：

- "更新`HEARTBEAT.md`添加每日日历检查"
- "重写`HEARTBEAT.md`，使其更短并专注于收件箱跟进"

也可以在心跳提示中包含明确的指令：
```json5
{
  "prompt": "Read HEARTBEAT.md if it exists. If the checklist becomes stale, update HEARTBEAT.md with a better one. If nothing needs attention, reply HEARTBEAT_OK."
}
```

**安全提示**：不要在`HEARTBEAT.md`中放置密钥（API密钥、电话号码、私有令牌），因为它会成为提示上下文的一部分。

## 响应约定

### HEARTBEAT_OK标记

`HEARTBEAT_OK`是心跳机制的核心约定：

- **含义**：表示没有需要关注的事项
- **位置**：回复的开头或结尾
- **处理**：标记会被移除，剩余内容≤`ackMaxChars`时回复被丢弃

### 响应类型

1. **无事发生**：
   ```
   HEARTBEAT_OK
   ```
   或
   ```
   Everything looks good. HEARTBEAT_OK
   ```
   → 被抑制，不发送给用户

2. **无事发生但带说明**：
   ```
   Checked inboxes and calendar. No urgent items. HEARTBEAT_OK
   ```
   → 如果≤300字符，被抑制；否则发送

3. **有事项需要关注**：
   ```
   You have 3 urgent emails:
   - Client meeting at 2pm
   - Project deadline tomorrow
   - Invoice overdue
   ```
   → 发送给用户

### 标记位置规则

- **开头或结尾**：特殊处理，作为确认标记
- **中间**：不特殊处理，作为普通文本
- **心跳外**：意外的`HEARTBEAT_OK`会被移除并记录日志

## 可见性控制

### 三层控制机制

OpenClaw提供了三层可见性控制：

1. **全局默认值**：`channels.defaults.heartbeat`
2. **渠道级别**：`channels.<channel>.heartbeat`
3. **账户级别**：`channels.<channel>.accounts.<id>.heartbeat`

### 控制标志

#### `showOk` - 显示确认消息

- 默认：`false`（静默确认）
- 启用：发送`HEARTBEAT_OK`确认消息

#### `showAlerts` - 显示警报消息

- 默认：`true`（显示警报）
- 禁用：抑制非OK回复的发送

#### `useIndicator` - 使用指示器事件

- 默认：`true`（发出指示器事件）
- 禁用：不发送UI状态指示器

### 配置示例

```yaml
channels:
  defaults:
    heartbeat:
      showOk: false      # 隐藏HEARTBEAT_OK（默认）
      showAlerts: true   # 显示警报消息（默认）
      useIndicator: true # 发出指示器事件（默认）

  telegram:
    heartbeat:
      showOk: true       # 在Telegram上显示OK确认

  slack:
    accounts:
      ops:
        heartbeat:
          showAlerts: false  # 为ops账户抑制警报
```

### 常见模式

| 目标 | 配置 |
|------|------|
| 默认行为（静默OK，警报开启） | （无需配置） |
| 完全静默（无消息，无指示器） | `channels.defaults.heartbeat: { showOk: false, showAlerts: false, useIndicator: false }` |
| 仅指示器（无消息） | `channels.defaults.heartbeat: { showOk: false, showAlerts: false, useIndicator: true }` |
| 仅在一个渠道显示OK | `channels.telegram.heartbeat: { showOk: true }` |

### 完全禁用心跳

如果所有三个标志都为`false`，OpenClaw会完全跳过心跳运行（不调用模型）：

```yaml
channels:
  defaults:
    heartbeat:
      showOk: false
      showAlerts: false
      useIndicator: false
```

## 活动时段控制

### 时段配置

活动时段允许你限制心跳只在特定时间运行：

```json5
{
  "activeHours": {
    "start": "09:00",
    "end": "22:00",
    "timezone": "America/New_York"
  }
}
```

### 时区解析

时区字段支持以下值：

- 省略或`"user"`：使用`agents.defaults.userTimezone`，否则回退到主机时区
- `"local"`：始终使用主机系统时区
- IANA标识符：如`"America/New_York"`、`"Asia/Shanghai"`
- 无效值：回退到`"user"`行为

### 时间格式

- 格式：`HH:MM`
- 小时：`00-23`
- 分钟：`00-59`
- 特殊值：`24:00`（仅用于结束时间）

### 跨午夜处理

如果结束时间小于开始时间，表示跨午夜：

```json5
{
  "activeHours": {
    "start": "22:00",
    "end": "06:00"
  }
}
```

这表示心跳在晚上10点到早上6点之间运行。

### 边界情况

- `start`和`end`相等：视为零宽度窗口，始终在窗口外
- 无效时间格式：忽略活动时段限制

## 发送行为

### 会话上下文

心跳默认在智能体主会话中运行（`agent:<id>:<mainKey>`），或当`session.scope = "global"`时在`global`中运行。

可以通过`session`字段覆盖为特定渠道会话：

```json5
{
  "session": "discord:channel:123456789"
}
```

### 目标解析

- `session`只影响运行上下文
- 发送由`target`和`to`控制
- `target: "last"`使用该会话的最后一个外部渠道

### 队列处理

- 如果主队列繁忙，心跳会被跳过并稍后重试
- 心跳不会阻塞正常消息处理

### 会话活跃性

- 仅心跳回复不会保持会话活跃
- 最后的`updatedAt`会被恢复，因此空闲过期正常工作

### 目标解析失败

如果`target`解析为无外部目标，运行仍会发生但不会发送出站消息。这允许心跳进行内部处理而不打扰用户。

## 手动唤醒

### 立即触发

可以通过系统事件立即触发心跳：

```bash
openclaw system event --text "Check for urgent follow-ups" --mode now
```

### 唤醒模式

- `--mode now`：立即运行
- `--mode next-heartbeat`：等待下一个计划的时钟周期

### 多智能体处理

如果多个智能体配置了`heartbeat`，手动唤醒会立即运行每个智能体的心跳。

### 自定义唤醒参数

```bash
openclaw system event \
  --text "Custom wake reason" \
  --agent-id "ops" \
  --session-key "discord:channel:123" \
  --mode now
```

## 推理内容发送

### 启用推理

默认情况下，心跳只发送最终的"答案"负载。启用推理后，会发送单独的`Reasoning:`消息：

```json5
{
  "includeReasoning": true
}
```

### 推理消息格式

推理消息与`/reasoning on`格式相同：

```
Reasoning: I checked the inbox and found 3 urgent emails. The calendar shows a meeting at 2pm. No other items need attention.
```

### 使用场景

- **透明度**：了解智能体为什么决定联系你
- **调试**：诊断心跳决策过程
- **多会话管理**：跟踪智能体在不同会话中的推理

### 注意事项

- 可能泄露比你想要的更多内部细节
- 在群聊中建议保持关闭
- 会增加token使用量

## 心跳与Cron的对比

### 核心区别

| 特性 | 心跳 | Cron |
|------|------|------|
| 上下文 | 主会话（完整上下文） | 隔离会话（无上下文）或主会话 |
| 定时 | 固定间隔（如30分钟） | 精确cron表达式 |
| 决策 | 智能决策，可抑制 | 确定性执行 |
| 成本 | 批量处理多项检查 | 每个任务独立运行 |
| 适用场景 | 监控、检查 | 精确调度、独立任务 |

### 何时使用心跳

- **多个周期性检查**：一次心跳批量处理收件箱、日历、通知等
- **上下文感知决策**：需要根据对话历史判断优先级
- **对话连续性**：需要记住最近对话并自然跟进
- **低开销监控**：替代多个小型轮询任务

### 何时使用Cron

- **精确定时**：需要"每天上午9:00"而非"大约9点"
- **独立任务**：不需要对话上下文
- **不同模型**：需要更强大或更便宜的模型
- **一次性提醒**：使用`--at`实现"20分钟后提醒我"
- **嘈杂任务**：会污染主会话历史的任务

### 组合使用

最高效的配置是两者结合：

1. **心跳**处理常规监控（每30分钟）
2. **Cron**处理精确调度（每日报告、每周回顾）

## 技术实现

### 心跳调度器

OpenClaw使用`HeartbeatRunner`类管理心跳调度：

- **定时器管理**：基于`setTimeout`的定时调度
- **队列协调**：与主命令队列协调，避免冲突
- **状态跟踪**：跟踪每个智能体的最后运行时间和下次到期时间
- **配置热更新**：支持运行时配置更新

### 唤醒机制

心跳唤醒使用优先级队列：

- **优先级**：重试 > 间隔 > 默认 > 动作
- **合并**：短时间内的多个唤醒请求会被合并
- **重试**：失败的唤醒会自动重试

### 活动时段检查

活动时段检查使用`Intl.DateTimeFormat`API：

- 支持IANA时区标识符
- 正确处理跨午夜时段
- 回退到用户时区或主机时区

### 可见性解析

可见性设置遵循优先级链：

1. 账户级别（最具体）
2. 渠道级别
3. 渠道默认值
4. 全局默认值（最通用）

### 事件系统

心跳事件通过事件系统分发：

- **事件类型**：`sent`、`ok-empty`、`ok-token`、`skipped`、`failed`
- **指示器类型**：`ok`、`alert`、`error`
- **监听器**：UI和其他组件可以监听心跳事件

## 成本优化

### Token使用

心跳运行完整的智能体轮次，因此会消耗token。优化策略：

1. **保持HEARTBEAT.md小巧**：减少提示长度
2. **使用更便宜的模型**：为心跳配置专用模型
3. **合理设置间隔**：避免过于频繁的检查
4. **使用target: "none"**：仅内部处理，不发送消息

### API调用优化

- **空文件跳过**：空的HEARTBEAT.md会跳过API调用
- **活动时段**：在非活动时段完全跳过
- **队列协调**：避免在队列繁忙时重复尝试

### 成本对比

| 机制 | 成本特征 |
|------|----------|
| 心跳 | 每N分钟一次轮次；随HEARTBEAT.md大小扩展 |
| Cron（主会话） | 将事件添加到下一次心跳（无隔离轮次） |
| Cron（隔离式） | 每个任务一次完整智能体轮次；可使用更便宜的模型 |

## 最佳实践

### 配置建议

1. **间隔设置**：
   - 开发/测试：`"1h"`或更长
   - 生产环境：`"30m"`到`"1h"`
   - 高频监控：`"15m"`（注意成本）

2. **目标设置**：
   - 个人助手：`"last"`
   - 运维监控：特定渠道
   - 内部处理：`"none"`

3. **活动时段**：
   - 工作时间：`"09:00"-"18:00"`
   - 延长服务：`"08:00"-"22:00"`
   - 24/7服务：不设置

### HEARTBEAT.md编写

1. **保持简洁**：5-10个检查项
2. **明确具体**：使用可执行的指令
3. **避免重复**：不重复之前聊天的任务
4. **定期审查**：根据实际需求调整

### 监控和调试

1. **使用心跳事件**：监听心跳事件了解运行状态
2. **检查日志**：查看心跳运行日志
3. **手动测试**：使用`openclaw system event`手动触发
4. **调整配置**：根据实际使用情况优化

## 故障排除

### 心跳未运行

1. 检查`heartbeat.every`是否为`"0m"`（禁用）
2. 检查活动时段配置
3. 检查智能体是否配置了心跳
4. 查看日志了解具体原因

### 消息未发送

1. 检查`target`配置
2. 检查可见性设置（`showAlerts`）
3. 检查回复是否包含`HEARTBEAT_OK`且≤`ackMaxChars`
4. 检查渠道连接状态

### 成本过高

1. 减少心跳间隔
2. 缩小`HEARTBEAT.md`
3. 使用更便宜的模型
4. 设置`target: "none"`进行内部处理

### 时段问题

1. 检查时区配置
2. 验证时间格式
3. 检查跨午夜配置
4. 使用日志验证时段判断

## 总结

OpenClaw的心跳机制是一个强大而灵活的周期性任务调度系统。它通过以下特性为智能体提供了主动感知能力：

- **上下文感知**：在主会话中运行，拥有完整的对话历史
- **智能决策**：可以根据当前状态判断优先级
- **批量处理**：一次心跳可以检查多个事项
- **自然抑制**：无事发生时不会打扰用户
- **灵活配置**：支持间隔、目标、时段等多维度配置
- **成本优化**：通过多种机制控制token使用

通过合理配置和使用心跳机制，可以显著提升OpenClaw的智能性和实用性，使其从一个被动的问答工具转变为一个主动的智能助手。心跳机制与记忆机制、上下文管理共同构成了OpenClaw的核心能力，为构建真正的智能体应用提供了坚实的基础。