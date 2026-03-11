# OpenClaw使用MCP指南

## 概述

OpenClaw完全支持MCP（Model Context Protocol），这是一种标准化的工具提供者接口，允许智能体与外部服务和工具进行交互。通过MCP，OpenClaw可以访问各种第三方服务，如数据库、API、文件系统等，大大扩展了智能体的能力范围。

## MCP简介

MCP（Model Context Protocol）是一个开放协议，定义了AI模型与工具提供者之间的通信标准。它提供了一种统一的方式来：

- 发现和描述可用的工具
- 调用工具并传递参数
- 接收工具执行结果
- 管理工具生命周期

MCP支持多种传输方式，包括stdio、HTTP等，使工具提供者可以灵活地部署和集成。

## OpenClaw中的MCP支持

### ACPX插件集成

OpenClaw通过ACPX（Agent Client Protocol eXtension）插件提供MCP支持。ACPX是一个强大的运行时后端，支持：

- ACP协议实现
- MCP服务器管理
- 会话生命周期管理
- 权限控制

### MCP配置架构

OpenClaw的MCP配置采用分层架构：

```
全局配置
  ↓
插件配置（acpx）
  ↓
MCP服务器定义
  ↓
会话注入
```

## MCP服务器配置

### 基本配置结构

在OpenClaw配置文件中，MCP服务器通过`acpx`插件的`mcpServers`字段定义：

```json5
{
  "plugins": {
    "acpx": {
      "mcpServers": {
        "server-name": {
          "command": "server-command",
          "args": ["arg1", "arg2"],
          "env": {
            "ENV_VAR": "value"
          }
        }
      }
    }
  }
}
```

### 配置字段说明

#### command（必需）

MCP服务器的启动命令：

```json5
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/directory"]
    }
  }
}
```

#### args（可选）

传递给命令的参数数组：

```json5
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github",
        "--personal-access-token",
        "${GITHUB_TOKEN}"
      ]
    }
  }
}
```

#### env（可选）

环境变量对象：

```json5
{
  "mcpServers": {
    "database": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_USER": "admin",
        "DB_PASSWORD": "${DB_PASSWORD}"
      }
    }
  }
}
```

## 常用MCP服务器示例

### 文件系统服务器

```json5
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  }
}
```

### GitHub服务器

```json5
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github",
        "--personal-access-token",
        "${GITHUB_TOKEN}"
      ]
    }
  }
}
```

### SQLite服务器

```json5
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "--db-path",
        "/path/to/database.db"
      ]
    }
  }
}
```

### PostgreSQL服务器

```json5
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": [
        "mcp-postgres",
        "--connection-string",
        "postgresql://user:password@localhost:5432/dbname"
      ]
    }
  }
}
```

### Puppeteer浏览器服务器

```json5
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-puppeteer"
      ]
    }
  }
}
```

### Fetch服务器

```json5
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-fetch"
      ]
    }
  }
}
```

### 自定义MCP服务器

```json5
{
  "mcpServers": {
    "custom-api": {
      "command": "python",
      "args": ["custom_mcp_server.py"],
      "env": {
        "API_KEY": "${CUSTOM_API_KEY}",
        "API_ENDPOINT": "https://api.example.com"
      }
    }
  }
}
```

## MCP会话管理

### MCP代理机制

OpenClaw使用MCP代理机制将配置的MCP服务器注入到ACP会话中：

```javascript
// MCP代理工作流程
1. 接收ACP会话请求（session/new, session/load, session/fork）
2. 检查配置的MCP服务器
3. 将MCP服务器配置注入到会话参数中
4. 转发修改后的请求到目标ACP运行时
5. 返回响应给客户端
```

### 会话启动时的MCP注入

当创建新的ACP会话时，OpenClaw自动注入配置的MCP服务器：

```json5
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "session/new",
  "params": {
    "cwd": "/workspace",
    "mcpServers": [
      {
        "name": "filesystem",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
        "env": []
      }
    ]
  }
}
```

### 会话加载时的MCP注入

加载现有会话时也会注入MCP服务器配置：

```json5
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/load",
  "params": {
    "sessionId": "session-id",
    "mcpServers": [
      // 配置的MCP服务器
    ]
  }
}
```

## MCP工具调用

### 工具发现

OpenClaw通过MCP协议自动发现可用工具：

```typescript
// MCP工具发现流程
1. 连接到MCP服务器
2. 调用tools/list方法
3. 接收工具列表和定义
4. 将工具转换为OpenClaw工具格式
5. 注册到智能体工具集中
```

### 工具定义格式

MCP工具定义包含以下信息：

```json5
{
  "name": "read_file",
  "description": "Read the contents of a file",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": {
        "type": "string",
        "description": "Path to the file to read"
      }
    },
    "required": ["path"]
  }
}
```

### 工具调用流程

```typescript
// MCP工具调用流程
1. 智能体决定调用工具
2. OpenClaw将调用转换为MCP请求
3. 发送到对应的MCP服务器
4. MCP服务器执行工具
5. 返回结果
6. OpenClaw将结果转换为标准格式
7. 返回给智能体
```

## MCP权限管理

### 权限模式

OpenClaw支持多种MCP权限模式：

#### approve-all（批准所有）

```json5
{
  "plugins": {
    "acpx": {
      "permissionMode": "approve-all"
    }
  }
}
```

自动批准所有MCP工具调用。

#### approve-reads（批准读取）

```json5
{
  "plugins": {
    "acpx": {
      "permissionMode": "approve-reads"
    }
  }
}
```

自动批准读取操作，其他操作需要批准。

#### deny-all（拒绝所有）

```json5
{
  "plugins": {
    "acpx": {
      "permissionMode": "deny-all"
    }
  }
}
```

拒绝所有MCP工具调用。

### 非交互式权限策略

当无法进行交互式批准时：

```json5
{
  "plugins": {
    "acpx": {
      "nonInteractivePermissions": "deny"
    }
  }
}
```

选项：
- `deny`: 拒绝调用
- `fail`: 返回错误

## MCP配置验证

### 配置检查

OpenClaw在启动时验证MCP配置：

```typescript
// 验证规则
1. mcpServers必须是对象
2. 每个服务器必须有command字段
3. args必须是字符串数组
4. env必须是字符串到字符串的对象
5. 未知配置键会被拒绝
```

### 错误处理

配置错误示例：

```json5
{
  "mcpServers": {
    "invalid": {
      // 缺少command字段
      "args": ["arg1"]
    }
  }
}
```

错误信息：
```
mcpServers.invalid must have a command string, optional args array, and optional env object
```

## MCP使用场景

### 场景1：代码仓库分析

```json5
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/repo"]
    },
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github",
        "--personal-access-token",
        "${GITHUB_TOKEN}"
      ]
    }
  }
}
```

智能体可以：
- 读取代码文件
- 分析代码结构
- 获取GitHub issues
- 创建pull requests

### 场景2：数据库查询

```json5
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": [
        "mcp-postgres",
        "--connection-string",
        "${DATABASE_URL}"
      ]
    }
  }
}
```

智能体可以：
- 执行SQL查询
- 分析数据
- 生成报告
- 数据可视化

### 场景3：Web自动化

```json5
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

智能体可以：
- 浏览网页
- 提取数据
- 表单填写
- 网页截图

### 场景4：API集成

```json5
{
  "mcpServers": {
    "custom-api": {
      "command": "python",
      "args": ["api_server.py"],
      "env": {
        "API_KEY": "${API_KEY}",
        "API_BASE": "https://api.example.com"
      }
    }
  }
}
```

智能体可以：
- 调用REST API
- 处理API响应
- 数据转换
- 错误处理

## MCP调试

### 日志配置

启用MCP调试日志：

```bash
export DEBUG=mcp:*
openclaw agent
```

### 连接测试

测试MCP服务器连接：

```bash
# 使用mcporter CLI测试
mcporter list
mcporter test filesystem
```

### 工具列表

查看可用工具：

```bash
# 通过OpenClaw CLI
openclaw tools list

# 通过acpx
acpx tools list
```

### 会话检查

检查MCP会话状态：

```bash
# 查看活动会话
openclaw sessions list

# 查看会话详情
openclaw sessions get <session-id>
```

## MCP性能优化

### 连接池

MCP服务器连接可以重用：

```json5
{
  "plugins": {
    "acpx": {
      "queueOwnerTtlSeconds": 0.1
    }
  }
}
```

### 超时设置

配置MCP操作超时：

```json5
{
  "plugins": {
    "acpx": {
      "timeoutSeconds": 30
    }
  }
}
```

### 缓存策略

MCP代理缓存命令：

```typescript
// 缓存键格式
<cwd>::<agent>

// 缓存失效
- 配置更改
- 工作目录更改
- 代理命令更改
```

## MCP安全考虑

### 环境变量保护

敏感信息使用环境变量：

```json5
{
  "mcpServers": {
    "secure": {
      "command": "python",
      "args": ["secure_server.py"],
      "env": {
        "API_KEY": "${API_KEY}",
        "SECRET": "${SECRET}"
      }
    }
  }
}
```

### 权限限制

使用严格的权限模式：

```json5
{
  "plugins": {
    "acpx": {
      "permissionMode": "approve-reads",
      "nonInteractivePermissions": "deny"
    }
  }
}
```

### 网络隔离

限制MCP服务器网络访问：

```json5
{
  "mcpServers": {
    "local-only": {
      "command": "python",
      "args": ["local_server.py"],
      "env": {
        "ALLOWED_HOSTS": "localhost,127.0.0.1"
      }
    }
  }
}
```

## MCP与OpenClaw工具集成

### 工具转换

MCP工具自动转换为OpenClaw工具格式：

```typescript
// MCP工具定义
{
  "name": "read_file",
  "description": "Read file contents",
  "inputSchema": {
    "type": "object",
    "properties": {
      "path": { "type": "string" }
    }
  }
}

// 转换为OpenClaw工具
{
  name: "read_file",
  description: "Read file contents",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" }
    }
  },
  execute: async (params) => {
    // 通过MCP协议调用
  }
}
```

### 工具策略

MCP工具遵循OpenClaw工具策略：

```json5
{
  "tools": {
    "allow": ["read_file", "write_file"],
    "deny": ["delete_file"]
  }
}
```

### 工具循环检测

MCP工具调用受循环检测保护：

```json5
{
  "tools": {
    "loopDetection": {
      "enabled": true,
      "historySize": 50
    }
  }
}
```

## MCP最佳实践

### 1. 服务器命名

使用描述性的服务器名称：

```json5
{
  "mcpServers": {
    "prod-database": { /* ... */ },
    "staging-database": { /* ... */ },
    "dev-database": { /* ... */ }
  }
}
```

### 2. 环境变量管理

集中管理环境变量：

```bash
# .env file
GITHUB_TOKEN=ghp_xxx
DATABASE_URL=postgresql://...
API_KEY=sk_xxx
```

```json5
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### 3. 版本锁定

锁定MCP服务器版本：

```json5
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem@0.6.0",
        "/workspace"
      ]
    }
  }
}
```

### 4. 错误处理

实现健壮的错误处理：

```python
# custom_mcp_server.py
import mcp
from mcp.server import Server

server = Server("custom-server")

@server.tool()
async def risky_operation(param: str) -> str:
    try:
        # 执行操作
        return result
    except Exception as e:
        # 返回友好的错误信息
        return f"Error: {str(e)}"
```

### 5. 文档记录

记录MCP服务器用途：

```json5
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "_comment": "GitHub API integration for repository management"
    }
  }
}
```

## 故障排除

### 问题1：MCP服务器无法启动

症状：
- 工具调用失败
- 连接超时

解决方案：
```bash
# 手动测试服务器
npx @modelcontextprotocol/server-filesystem /path

# 检查命令路径
which npx

# 验证权限
ls -la /path/to/directory
```

### 问题2：工具未被发现

症状：
- 工具列表为空
- 工具调用失败

解决方案：
```bash
# 检查MCP服务器日志
openclaw logs

# 验证工具列表
acpx tools list

# 检查配置
openclaw config show
```

### 问题3：权限被拒绝

症状：
- 工具调用被阻止
- 权限错误

解决方案：
```json5
{
  "plugins": {
    "acpx": {
      "permissionMode": "approve-reads"
    }
  }
}
```

### 问题4：性能问题

症状：
- 响应缓慢
- 超时错误

解决方案：
```json5
{
  "plugins": {
    "acpx": {
      "timeoutSeconds": 60,
      "queueOwnerTtlSeconds": 0.1
    }
  }
}
```

## 高级用法

### 动态MCP服务器

根据环境动态配置MCP服务器：

```typescript
// config.ts
export function getMcpServers(env: string) {
  const base = {
    filesystem: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    }
  };

  if (env === "production") {
    return {
      ...base,
      database: {
        command: "uvx",
        args: ["mcp-postgres", "--connection-string", process.env.DATABASE_URL]
      }
    };
  }

  return base;
}
```

### MCP服务器链

组合多个MCP服务器：

```json5
{
  "mcpServers": {
    "filesystem": { /* ... */ },
    "github": { /* ... */ },
    "database": { /* ... */ },
    "browser": { /* ... */ }
  }
}
```

智能体可以：
- 读取代码文件（filesystem）
- 获取GitHub issues（github）
- 查询数据库（database）
- 浏览网页（browser）

### 自定义MCP服务器

创建自定义MCP服务器：

```python
# my_mcp_server.py
import mcp
from mcp.server import Server

server = Server("my-custom-server")

@server.tool()
async def custom_tool(param: str) -> str:
    """Custom tool description"""
    # 实现自定义逻辑
    return f"Result: {param}"

async def main():
    async with mcp.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

配置：

```json5
{
  "mcpServers": {
    "my-custom": {
      "command": "python",
      "args": ["my_mcp_server.py"],
      "env": {
        "CUSTOM_VAR": "value"
      }
    }
  }
}
```

## 总结

OpenClaw的MCP支持为智能体提供了强大的外部工具集成能力。通过MCP，OpenClaw可以：

1. **访问外部服务**: 与数据库、API、文件系统等外部服务交互
2. **扩展工具集**: 通过MCP服务器轻松添加新工具
3. **标准化接口**: 使用统一的协议管理工具
4. **灵活配置**: 支持多种配置方式和环境
5. **安全控制**: 提供完善的权限管理和安全机制

MCP使OpenClaw智能体能够突破本地限制，访问更广阔的世界，实现更复杂的任务。通过合理配置和使用MCP，可以显著提升OpenClaw的能力和应用范围。