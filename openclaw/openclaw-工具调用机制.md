# OpenClaw工具调用机制

## 概述

OpenClaw的工具调用机制是其智能体能力的核心，它允许模型通过定义良好的接口与外部系统交互，执行文件操作、网络请求、命令执行等各种任务。工具调用机制设计精巧，提供了强大的功能、灵活的配置和完善的错误处理。

## 工具定义

### 工具基本结构

OpenClaw中的工具遵循`AgentTool`接口定义：

```typescript
interface AgentTool<TParams = unknown, TResult = unknown> {
  name: string;
  label?: string;
  description?: string;
  parameters?: Record<string, unknown>;
  execute: (
    toolCallId: string,
    params: TParams,
    signal?: AbortSignal,
    onUpdate?: AgentToolUpdateCallback<TResult>
  ) => Promise<TResult>;
  ownerOnly?: boolean;
}
```

### 工具字段说明

- **name**: 工具的唯一标识符，用于模型调用
- **label**: 工具的可读标签（默认为name）
- **description**: 工具功能的描述，帮助模型理解何时使用
- **parameters**: 工具参数的JSON Schema定义
- **execute**: 工具的执行函数，接收参数并返回结果
- **ownerOnly**: 标记为仅所有者可用的工具

### 工具参数Schema

工具参数使用JSON Schema定义，确保模型传递的参数符合预期：

```typescript
{
  name: "read",
  parameters: {
    type: "object",
    properties: {
      path: {
        type: "string",
        description: "File path to read"
      }
    },
    required: ["path"]
  }
}
```

## 工具调用流程

### 1. 工具注册和发现

OpenClaw通过插件系统发现和注册工具：

- **核心工具**: 内置的文件操作、命令执行等工具
- **插件工具**: 通过插件系统加载的扩展工具
- **渠道工具**: 特定消息渠道提供的工具（如Discord、Slack等）

工具注册时会进行以下处理：
- 名称规范化（转换为小写）
- Schema清理和适配
- 权限检查包装
- 循环检测包装

### 2. 工具策略应用

在工具可用给模型之前，会应用多层策略：

#### 全局策略

```json5
{
  "tools": {
    "allow": ["read", "write", "exec"],
    "deny": ["cron", "gateway"]
  }
}
```

#### 智能体策略

```json5
{
  "agents": {
    "list": [
      {
        "id": "ops",
        "tools": {
          "allow": ["read", "exec"],
          "deny": ["write"]
        }
      }
    ]
  }
}
```

#### 渠道策略

```json5
{
  "channels": {
    "discord": {
      "tools": {
        "allow": ["read", "message"]
      }
    }
  }
}
```

#### 群组策略

```json5
{
  "channels": {
    "discord": {
      "guilds": {
        "123456789": {
          "tools": {
            "allow": ["read"]
          }
        }
      }
    }
  }
}
```

#### 所有者限制

某些工具标记为`ownerOnly`，只有配置的所有者才能使用：

```typescript
{
  name: "whatsapp_login",
  ownerOnly: true,
  execute: async () => { /* ... */ }
}
```

### 3. 工具Schema转换

OpenClaw将工具定义转换为模型特定的格式：

#### Anthropic格式

```json
{
  "name": "read",
  "description": "Read file contents",
  "input_schema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string"
      }
    },
    "required": ["path"]
  }
}
```

#### OpenAI格式

```json
{
  "type": "function",
  "function": {
    "name": "read",
    "description": "Read file contents",
    "parameters": {
      "type": "object",
      "properties": {
        "path": {
          "type": "string"
        }
      },
      "required": ["path"]
    }
  }
}
```

#### Gemini格式

```json
{
  "name": "read",
  "description": "Read file contents",
  "parameters": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string"
      }
    },
    "required": ["path"]
  }
}
```

### 4. 工具调用执行

当模型决定调用工具时，OpenClaw执行以下步骤：

#### 步骤1: 前置钩子检查

```typescript
async function runBeforeToolCallHook(args: {
  toolName: string;
  params: unknown;
  toolCallId?: string;
  ctx?: HookContext;
}): Promise<HookOutcome>
```

前置钩子执行：
- **循环检测**: 检查是否陷入无限循环
- **参数调整**: 根据策略调整参数
- **权限验证**: 验证调用者权限
- **自定义钩子**: 执行用户定义的before_tool_call钩子

如果钩子返回`blocked: true`，工具调用被阻止并返回错误。

#### 步骤2: 参数规范化

```typescript
function normalizeToolParams(
  toolName: string,
  params: unknown
): Record<string, unknown>
```

参数规范化包括：
- 类型转换（字符串转数字等）
- 默认值填充
- 必需参数验证
- 参数名称规范化（camelCase ↔ snake_case）

#### 步骤3: 工具执行

```typescript
const result = await tool.execute(
  toolCallId,
  normalizedParams,
  abortSignal,
  onUpdateCallback
);
```

执行时支持：
- **中止信号**: 允许取消长时间运行的工具
- **进度更新**: 通过`onUpdate`回调报告进度
- **错误处理**: 捕获并标准化错误

#### 步骤4: 结果规范化

```typescript
function normalizeToolExecutionResult(params: {
  toolName: string;
  result: unknown;
}): AgentToolResult<unknown>
```

结果规范化确保：
- 标准的`content[]`格式
- 错误信息的统一处理
- 元数据的正确包含

#### 步骤5: 后置钩子执行

```typescript
async function runAfterToolCallHook(args: {
  toolName: string;
  params: unknown;
  result: unknown;
  error?: Error;
}): Promise<void>
```

后置钩子用于：
- 结果记录和审计
- 自定义处理逻辑
- 统计和监控

## 工具循环检测

### 检测机制

OpenClaw实现了多层次的工具循环检测：

#### 1. 精确重复检测

```typescript
function detectExactRepeats(
  history: ToolCallHistory[],
  toolName: string,
  params: unknown
): LoopDetectionResult
```

检测相同的工具调用重复出现：

```javascript
// 检测到循环
read({path: "config.json"})  // 第1次
read({path: "config.json"})  // 第2次
read({path: "config.json"})  // 第3次 - 警告
read({path: "config.json"})  // 第4次 - 阻止
```

#### 2. 配对工具检测

```typescript
function detectPairedTools(
  history: ToolCallHistory[],
  toolName: string,
  params: unknown
): LoopDetectionResult
```

检测两个工具之间的循环：

```javascript
// 检测到循环
read({path: "data.json"})
write({path: "data.json", content: "..."})
read({path: "data.json"})  // 警告
write({path: "data.json", content: "..."})  // 阻止
```

#### 3. 无进展检测

```typescript
function detectNoProgress(
  history: ToolCallHistory[],
  toolName: string,
  params: unknown
): LoopDetectionResult
```

检测工具调用没有产生进展：

```javascript
// 检测到无进展
exec({command: "npm install"})
exec({command: "npm install"})  // 无进展
exec({command: "npm install"})  // 阻止
```

#### 4. 全局熔断器

```typescript
function checkGlobalCircuitBreaker(
  history: ToolCallHistory[]
): boolean
```

全局熔断器防止过多的工具调用：

```javascript
// 超过全局限制
read({path: "file1.txt"})
read({path: "file2.txt"})
// ... 更多读取
read({path: "file100.txt"})  // 熔断器触发
```

### 配置选项

```json5
{
  "tools": {
    "loopDetection": {
      "enabled": true,
      "historySize": 50,
      "detectors": {
        "exactRepeats": {
          "enabled": true,
          "warningThreshold": 3,
          "criticalThreshold": 4
        },
        "pairedTools": {
          "enabled": true,
          "warningThreshold": 3,
          "criticalThreshold": 4
        },
        "noProgress": {
          "enabled": true,
          "warningThreshold": 5,
          "criticalThreshold": 6
        },
        "globalCircuitBreaker": {
          "enabled": true,
          "threshold": 100
        }
      }
    }
  }
}
```

### 响应级别

循环检测支持两个响应级别：

- **warning**: 记录警告但允许执行
- **critical**: 阻止执行并返回错误

## 工具策略系统

### 策略层次

OpenClaw的工具策略系统支持多层配置：

```
全局策略
  ↓
智能体策略
  ↓
渠道策略
  ↓
群组策略
  ↓
所有者限制
```

### 策略解析

```typescript
function resolveEffectiveToolPolicy(params: {
  config: OpenClawConfig;
  sessionKey: string;
  agentId: string;
  modelProvider?: string;
  modelId?: string;
}): EffectiveToolPolicy
```

策略解析考虑：
- 配置文件中的显式设置
- 会话上下文（主会话vs子会话）
- 消息渠道类型
- 模型提供商和ID
- 用户权限

### 工具组

OpenClaw支持工具组概念，简化策略配置：

```json5
{
  "tools": {
    "allow": [
      "read",
      "write",
      "group:file-ops",
      "group:plugins"
    ]
  }
}
```

预定义的工具组：
- `group:file-ops`: 文件操作工具
- `group:exec`: 命令执行工具
- `group:network`: 网络工具
- `group:plugins`: 所有插件工具

### 插件工具组

```json5
{
  "tools": {
    "allow": [
      "lobster",
      "diffs",
      "group:plugins"
    ]
  }
}
```

插件工具组会展开为所有可用的插件工具。

## 工具结果处理

### 标准结果格式

OpenClaw期望工具返回标准格式：

```typescript
interface AgentToolResult<T = unknown> {
  content: Array<{
    type: "text" | "image" | "audio" | "video";
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
  details?: T;
}
```

### 文本结果

```typescript
{
  content: [
    {
      type: "text",
      text: "File contents here..."
    }
  ]
}
```

### 多媒体结果

```typescript
{
  content: [
    {
      type: "image",
      data: "base64_encoded_image_data",
      mimeType: "image/png"
    }
  ]
}
```

### 混合结果

```typescript
{
  content: [
    {
      type: "text",
      text: "Analysis complete"
    },
    {
      type: "image",
      data: "base64_chart_data",
      mimeType: "image/svg+xml"
    }
  ]
}
```

### 错误结果

```typescript
{
  content: [
    {
      type: "text",
      text: "Error: file not found"
    }
  ],
  details: {
    status: "error",
    tool: "read",
    error: "ENOENT: file not found"
  }
}
```

## 工具钩子系统

### 钩子类型

OpenClaw支持多种工具钩子：

#### before_tool_call

在工具执行前调用：

```typescript
async function beforeToolCall(
  context: {
    toolName: string;
    params: Record<string, unknown>;
    toolCallId: string;
    runId?: string;
    agentId?: string;
    sessionKey?: string;
  }
): Promise<{
  block?: boolean;
  reason?: string;
  params?: Record<string, unknown>;
}>
```

用途：
- 参数验证和修改
- 权限检查
- 审计日志
- 自定义逻辑

#### after_tool_call

在工具执行后调用：

```typescript
async function afterToolCall(
  context: {
    toolName: string;
    params: Record<string, unknown>;
    result: unknown;
    error?: Error;
    toolCallId: string;
  }
): Promise<void>
```

用途：
- 结果记录
- 错误处理
- 统计收集
- 触发后续操作

### 钩子注册

```typescript
import { registerHook } from '@openclaw/hooks';

registerHook('before_tool_call', async (context) => {
  console.log(`Tool ${context.toolName} called with:`, context.params);
  return { block: false };
});

registerHook('after_tool_call', async (context) => {
  console.log(`Tool ${context.toolName} completed:`, context.result);
});
```

## 内置工具

### 文件操作工具

#### read

```typescript
{
  name: "read",
  description: "Read file contents",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" },
      limit: { type: "number" }
    },
    required: ["path"]
  }
}
```

#### write

```typescript
{
  name: "write",
  description: "Write content to file",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" },
      content: { type: "string" }
    },
    required: ["path", "content"]
  }
}
```

#### edit

```typescript
{
  name: "edit",
  description: "Edit file with search/replace",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" },
      search: { type: "string" },
      replace: { type: "string" }
    },
    required: ["path", "search", "replace"]
  }
}
```

### 命令执行工具

#### exec

```typescript
{
  name: "exec",
  description: "Execute shell command",
  parameters: {
    type: "object",
    properties: {
      command: { type: "string" },
      background: { type: "boolean" }
    },
    required: ["command"]
  }
}
```

#### process

```typescript
{
  name: "process",
  description: "Manage background processes",
  parameters: {
    type: "object",
    properties: {
      action: {
        type: "string",
        enum: ["list", "poll", "kill"]
      },
      sessionId: { type: "string" }
    },
    required: ["action"]
  }
}
```

### 网络工具

#### web_search

```typescript
{
  name: "web_search",
  description: "Search the web",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string" },
      numResults: { type: "number" }
    },
    required: ["query"]
  }
}
```

#### web_fetch

```typescript
{
  name: "web_fetch",
  description: "Fetch web content",
  parameters: {
    type: "object",
    properties: {
      url: { type: "string" },
      method: { type: "string" }
    },
    required: ["url"]
  }
}
```

### 记忆工具

#### memory_search

```typescript
{
  name: "memory_search",
  description: "Search memory files",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string" },
      maxResults: { type: "number" }
    },
    required: ["query"]
  }
}
```

#### memory_get

```typescript
{
  name: "memory_get",
  description: "Get memory file content",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" },
      from: { type: "number" },
      lines: { type: "number" }
    },
    required: ["path"]
  }
}
```

## 工具沙箱

### 沙箱模式

OpenClaw支持多种沙箱模式：

#### none（无沙箱）

```json5
{
  "agents": {
    "defaults": {
      "sandbox": {
        "enabled": false
      }
    }
  }
}
```

工具直接在主机文件系统上运行。

#### ro（只读）

```json5
{
  "agents": {
    "defaults": {
      "sandbox": {
        "enabled": true,
        "mode": "ro"
      }
    }
  }
}
```

工具在只读沙箱中运行，文件系统是工作区的副本。

#### copy（复制）

```json5
{
  "agents": {
    "defaults": {
      "sandbox": {
        "enabled": true,
        "mode": "copy"
      }
    }
  }
}
```

工具在独立沙箱中运行，文件系统是工作区的副本，写入被丢弃。

#### none（无文件系统）

```json5
{
  "agents": {
    "defaults": {
      "sandbox": {
        "enabled": true,
        "mode": "none"
      }
    }
  }
}
```

工具在没有文件系统访问的沙箱中运行。

### 沙箱限制

沙箱模式下的限制：
- 文件访问受限
- 网络访问可能受限
- 命令执行受限
- 工作区根目录保护

## 工具调用HTTP API

### 直接工具调用

OpenClaw提供HTTP端点直接调用工具：

```
POST /tools/invoke
Authorization: Bearer <token>
Content-Type: application/json

{
  "tool": "read",
  "action": "json",
  "args": {
    "path": "/path/to/file.txt"
  },
  "sessionKey": "main",
  "dryRun": false
}
```

### 请求参数

- **tool**: 工具名称（必需）
- **action**: 工具动作（可选）
- **args**: 工具参数（可选）
- **sessionKey**: 会话键（可选）
- **dryRun**: 是否为试运行（可选）

### 响应格式

```json
{
  "ok": true,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "File contents..."
      }
    ]
  }
}
```

### 错误响应

```json
{
  "ok": false,
  "error": "Tool not allowed",
  "status": 403
}
```

## 工具调用最佳实践

### 工具设计

1. **清晰的描述**: 提供详细的工具描述，帮助模型理解何时使用
2. **明确的参数**: 使用JSON Schema明确定义参数类型和约束
3. **错误处理**: 返回标准化的错误信息
4. **进度报告**: 对长时间运行的操作使用`onUpdate`回调

### 策略配置

1. **最小权限原则**: 只允许必要的工具
2. **分层配置**: 在不同层次配置策略
3. **定期审查**: 定期审查和更新工具策略
4. **监控使用**: 监控工具使用情况

### 循环检测

1. **启用检测**: 保持循环检测启用
2. **调整阈值**: 根据实际使用调整阈值
3. **监控警告**: 关注循环检测警告
4. **优化工具**: 避免设计容易产生循环的工具

### 性能优化

1. **缓存结果**: 对重复操作使用缓存
2. **批量操作**: 合并多个操作为单个工具调用
3. **异步执行**: 对长时间运行的操作使用后台执行
4. **限制输出**: 控制工具返回的数据量

## 故障排除

### 工具未找到

1. 检查工具名称拼写
2. 验证工具策略配置
3. 确认插件已正确加载
4. 检查模型提供商兼容性

### 工具被阻止

1. 检查工具策略（allow/deny）
2. 验证用户权限（ownerOnly）
3. 检查循环检测状态
4. 查看钩子日志

### 工具执行失败

1. 验证参数格式
2. 检查沙箱配置
3. 查看错误日志
4. 测试工具独立执行

### 循环检测误报

1. 调整检测阈值
2. 检查工具设计
3. 配置例外规则
4. 监控实际使用模式

## 总结

OpenClaw的工具调用机制是一个强大而灵活的系统，它通过以下特性为智能体提供了丰富的外部交互能力：

- **标准化接口**: 统一的工具定义和调用接口
- **多层策略**: 灵活的权限控制和访问管理
- **循环检测**: 智能的无限循环防护
- **钩子系统**: 可扩展的前后置处理机制
- **沙箱支持**: 安全的执行环境
- **错误处理**: 完善的错误处理和恢复
- **性能优化**: 多种优化机制确保高效执行

通过合理配置和使用这些机制，可以显著提升OpenClaw的安全性、可靠性和效率。工具调用机制是OpenClaw智能体能力的核心，理解这套机制对于深入使用和定制OpenClaw至关重要。