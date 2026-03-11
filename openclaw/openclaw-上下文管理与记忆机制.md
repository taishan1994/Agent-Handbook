# OpenClaw上下文管理与记忆机制

## 概述

OpenClaw作为一款智能体框架，其核心能力之一就是高效的上下文管理和记忆机制。这两者共同构成了智能体的"大脑"，使其能够在有限的token预算内保持连贯的对话和长期的知识积累。

## 上下文管理

### 什么是上下文

在OpenClaw中，"上下文"指的是在一次运行中发送给模型的所有内容。它受模型的上下文窗口（token限制）约束，是智能体当前"看到"和"思考"的内容范围。

### 上下文的组成

OpenClaw的上下文由以下几个核心部分组成：

#### 1. 系统提示词

系统提示词由OpenClaw自动构建，每次运行时重建，包括：

- **工具列表和描述**：智能体可用的工具及其功能说明
- **Skills列表**：仅包含元数据（名称+描述+位置），具体的指令按需加载
- **工作区位置**：智能体的工作空间路径
- **时间信息**：UTC时间和用户本地时间
- **运行时元数据**：主机、操作系统、模型、思考模式等信息
- **项目上下文**：注入的工作区引导文件

#### 2. 注入的工作区文件

默认情况下，OpenClaw会注入一组固定的工作区文件（如果存在）：

- `AGENTS.md`：智能体配置信息
- `SOUL.md`：智能体的"灵魂"或个性定义
- `TOOLS.md`：工具使用指南
- `IDENTITY.md`：身份信息
- `USER.md`：用户相关信息
- `HEARTBEAT.md`：心跳信息
- `BOOTSTRAP.md`：首次运行的引导信息

大文件会按照`agents.defaults.bootstrapMaxChars`（默认20000字符）进行截断。

#### 3. 对话历史

包括用户消息和助手在当前会话中的所有消息，构成了对话的上下文连续性。

#### 4. 工具调用和结果

命令输出、文件读取、图片/音频等工具调用的结果也计入上下文。

### 上下文检查工具

OpenClaw提供了几个斜杠命令来检查和管理上下文：

- `/status`：快速查看上下文窗口的使用情况和会话设置
- `/context list`：查看注入的文件及其大小
- `/context detail`：详细的上下文分解，包括每个文件、工具schema、Skills条目的大小
- `/usage tokens`：查看每次回复的token使用量
- `/compact`：将较旧的历史总结为紧凑条目以释放窗口空间

### 上下文压缩和修剪

当上下文接近token限制时，OpenClaw会自动进行压缩：

- **压缩**：将旧消息总结为紧凑条目，保持最近消息不变
- **修剪**：从内存中的提示词删除旧的工具结果，但不重写记录

## 记忆机制

### 记忆的存储方式

OpenClaw采用了一种独特而简洁的记忆存储方式：**纯Markdown文件**。这些文件位于智能体的工作空间中（默认`~/.openclaw/workspace`），是唯一的事实来源。

### 记忆文件结构

OpenClaw使用两层记忆结构：

#### 1. 每日日志（`memory/YYYY-MM-DD.md`）

- 用于记录日常笔记和运行上下文
- 采用追加模式写入
- 在会话开始时读取今天和昨天的内容
- 适合记录临时性、过程性的信息

#### 2. 长期记忆（`MEMORY.md`）

- 精心整理的持久性事实
- 仅在主要的私人会话中加载（不在群组上下文中加载）
- 适合存储决策、偏好和重要事实

### 何时写入记忆

OpenClaw提供了明确的记忆写入指导：

- **决策、偏好和持久性事实** → 写入`MEMORY.md`
- **日常笔记和运行上下文** → 写入`memory/YYYY-MM-DD.md`
- **明确的"记住这个"指令** → 必须写下来，不能只保存在内存中

### 自动记忆刷新

OpenClaw实现了一个智能的记忆刷新机制：

当会话接近自动压缩时，系统会触发一个**静默的智能体回合**，提醒模型在上下文被压缩之前写入持久记忆。这个机制由`agents.defaults.compaction.memoryFlush`配置控制：

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

特点：
- **软阈值触发**：当token估计超过`contextWindow - reserveTokensFloor - softThresholdTokens`时触发
- **默认静默**：提示包含`NO_REPLY`，用户不会看到这个回合
- **每个压缩周期刷新一次**：在`sessions.json`中跟踪
- **工作空间必须可写**：只读沙箱会跳过刷新

## 向量记忆搜索

### 搜索能力

OpenClaw可以在记忆文件上构建向量索引，支持语义搜索：

- **默认启用**：自动监视记忆文件的更改
- **语义搜索**：即使措辞不同也能找到相关笔记
- **混合搜索**：结合向量相似度和BM25关键词相关性

### 搜索工具

OpenClaw提供了两个主要的记忆搜索工具：

#### 1. `memory_search`

- 从`MEMORY.md`和`memory/**/*.md`进行语义搜索
- 返回片段文本（约700字符）、文件路径、行范围、分数等信息
- 支持混合搜索（向量+关键词）

#### 2. `memory_get`

- 读取特定的记忆Markdown文件
- 支持从起始行开始读取N行
- 路径限制在`MEMORY.md`/`memory/`范围内

### 索引机制

- **文件类型**：仅索引Markdown文件
- **索引存储**：每个智能体的SQLite数据库位于`~/.openclaw/memory/<agentId>.sqlite`
- **新鲜度**：监视器标记索引为脏（去抖动1.5秒），同步异步运行
- **自动重建**：当嵌入提供商/模型/参数变化时自动重新索引

### 混合搜索

OpenClaw结合了两种检索信号：

1. **向量相似度**：擅长语义匹配，如"Mac Studio gateway host" vs "运行gateway的机器"
2. **BM25关键词相关性**：擅长精确匹配，如ID、代码符号、错误字符串

配置示例：

```json5
agents: {
  defaults: {
    memorySearch: {
      query: {
        hybrid: {
          enabled: true,
          vectorWeight: 0.7,
          textWeight: 0.3,
          candidateMultiplier: 4
        }
      }
    }
  }
}
```

## 嵌入提供商支持

OpenClaw支持多种嵌入提供商：

### 远程嵌入

- **OpenAI**：`text-embedding-3-small`等模型
- **Gemini**：`gemini-embedding-001`
- **Voyage**：Voyage AI的嵌入模型
- **Mistral**：Mistral的嵌入API
- **Ollama**：本地Ollama服务

### 本地嵌入

- 使用`node-llama-cpp`运行本地模型
- 默认模型：`hf:ggml-org/embeddinggemma-300M-GGUF/embeddinggemma-300M-Q8_0.gguf`
- 支持自动下载和缓存
- 完全离线工作

### 批量索引

OpenAI和Gemini支持批量嵌入，可以显著提高大型索引的速度并降低成本：

```json5
agents: {
  defaults: {
    memorySearch: {
      provider: "openai",
      remote: {
        batch: { enabled: true, concurrency: 2 }
      }
    }
  }
}
```

## 高级特性

### 嵌入缓存

OpenClaw可以在SQLite中缓存块嵌入，避免重新嵌入未更改的文本：

```json5
agents: {
  defaults: {
    memorySearch: {
      cache: {
        enabled: true,
        maxEntries: 50000
      }
    }
  }
}
```

### SQLite向量加速

当`sqlite-vec`扩展可用时，OpenClaw将嵌入存储在SQLite虚拟表中，在数据库内执行向量距离查询，保持搜索快速。

### 会话记忆搜索（实验性）

可以选择性地索引会话记录并通过`memory_search`呈现：

```json5
agents: {
  defaults: {
    memorySearch: {
      experimental: { sessionMemory: true },
      sources: ["memory", "sessions"]
    }
  }
}
```

### 额外记忆路径

可以索引默认工作区布局之外的Markdown文件：

```json5
agents: {
  defaults: {
    memorySearch: {
      extraPaths: ["../team-docs", "/srv/shared-notes/overview.md"]
    }
  }
}
```

## 上下文与记忆的关系

上下文和记忆虽然相关，但有不同的作用：

- **上下文**：模型当前窗口内的内容，包括系统提示词、对话历史、工具结果等
- **记忆**：存储在磁盘上的持久化信息，可以跨会话访问

OpenClaw通过以下方式协调两者：

1. **记忆注入**：在会话开始时，将相关的记忆文件注入到上下文中
2. **记忆搜索**：在运行时，通过`memory_search`工具从记忆中检索相关信息
3. **记忆刷新**：在上下文压缩前，自动提醒模型将重要信息写入记忆

## 最佳实践

### 上下文管理

1. **监控上下文使用**：定期使用`/context`和`/status`检查上下文使用情况
2. **优化工具使用**：避免不必要的工具调用，减少工具结果占用的token
3. **合理配置压缩**：根据模型和需求调整压缩阈值和策略
4. **管理工作区文件**：保持引导文件简洁，避免注入过多内容

### 记忆管理

1. **明确记忆写入**：当需要持久化信息时，明确要求模型写入记忆
2. **分类存储**：长期事实存入`MEMORY.md`，日常笔记存入每日日志
3. **定期整理**：定期回顾和整理记忆文件，保持其结构清晰
4. **利用搜索**：使用`memory_search`快速检索相关信息，避免重复劳动

## 技术架构

### 记忆管理器

OpenClaw的核心是`MemoryIndexManager`类，它负责：

- **索引管理**：创建和维护向量索引
- **搜索执行**：执行向量搜索、关键词搜索和混合搜索
- **同步协调**：协调文件监视、索引更新和后台同步
- **嵌入处理**：管理嵌入提供商、缓存和批量处理

### 上下文引擎

上下文引擎负责：

- **上下文组装**：构建发送给模型的完整上下文
- **压缩执行**：在token限制接近时执行压缩
- **历史管理**：管理对话历史的持久化和检索

## 总结

OpenClaw的上下文管理和记忆机制体现了其设计的核心理念：**在有限的资源约束下，实现智能的长期记忆和高效的上下文利用**。

通过Markdown文件作为记忆存储、向量搜索作为检索机制、自动压缩作为上下文管理策略，OpenClaw为智能体提供了一个强大而灵活的记忆系统。这套机制使得智能体能够在保持对话连贯性的同时，积累和利用长期知识，从而提供更智能、更个性化的服务。

通过合理配置和使用这些机制，可以显著提升OpenClaw的智能性、可靠性和效率。理解这套机制对于深入使用和定制OpenClaw至关重要。