# OpenClaw技能加载与使用机制

OpenClaw的技能系统是其核心功能之一，允许通过可扩展的技能文件增强智能体的能力。本文将详细介绍OpenClaw如何加载、管理和使用技能。

## 技能概述

技能是OpenClaw中的可扩展功能单元，每个技能都是一个独立的模块，包含特定的功能和工具。技能可以：

- 提供专门的工具和命令
- 定义使用场景和触发条件
- 包含依赖检查和安装说明
- 提供丰富的文档和使用示例

## 技能加载位置

OpenClaw从多个位置加载技能，按优先级顺序如下：

1. **用户自定义技能**：`~/.openclaw/skills/`
2. **项目本地技能**：`<project>/.openclaw/skills/`
3. **内置技能**：OpenClaw安装目录中的`skills/`文件夹

这种分层加载机制允许用户覆盖内置技能，同时为不同项目提供定制化的技能集。

## 技能文件结构

每个技能必须包含一个`SKILL.md`文件，该文件使用YAML frontmatter定义技能元数据：

```yaml
---
name: weather
description: "通过wttr.in或Open-Meteo获取当前天气和预报"
homepage: https://wttr.in/:help
metadata:
  {
    "openclaw":
      {
        "emoji": "🌤️",
        "requires": { "bins": ["curl"] },
      },
  }
---

# 天气技能

获取当前天气状况和预报。

## 使用时机

✅ **使用此技能时：**

- "今天天气怎么样？"
- "明天会下雨吗？"
- "[城市]的温度"
- "本周天气预报"
```

## 技能元数据解析

OpenClaw通过`frontmatter.ts`模块解析技能元数据：

### 核心元数据字段

- **name**: 技能唯一标识符
- **description**: 技能功能描述，用于智能体理解技能用途
- **homepage**: 技能文档主页URL
- **metadata**: 扩展元数据，包含OpenClaw特定配置

### OpenClaw特定元数据

```typescript
interface OpenClawMetadata {
  emoji?: string;              // 技能图标
  requires?: {
    bins?: string[];           // 需要的二进制工具
    env?: string[];            // 需要的环境变量
  };
  install?: InstallInstruction[]; // 安装说明
  os?: string[];               // 支持的操作系统
  always?: boolean;            // 是否始终加载
  primaryEnv?: string;         // 主要环境变量名
}
```

### 安装指令

技能可以定义多种安装方式：

```yaml
metadata:
  {
    "openclaw":
      {
        "install":
          [
            {
              "id": "brew",
              "kind": "brew",
              "formula": "gh",
              "bins": ["gh"],
              "label": "安装GitHub CLI (brew)",
            },
            {
              "id": "apt",
              "kind": "apt",
              "package": "gh",
              "bins": ["gh"],
              "label": "安装GitHub CLI (apt)",
            },
          ],
      },
  }
```

支持的安装类型包括：
- `brew`: Homebrew安装
- `apt`: APT包管理器
- `npm`: NPM包安装
- `pip`: Python包安装

## 技能过滤机制

OpenClaw使用多层次的过滤机制来确定哪些技能应该被加载：

### 1. 配置过滤

```typescript
function shouldIncludeSkill(params: {
  entry: SkillEntry;
  config?: OpenClawConfig;
  eligibility?: SkillEligibilityContext;
}): boolean {
  const { entry, config, eligibility } = params;
  const skillKey = resolveSkillKey(entry.skill, entry);
  const skillConfig = resolveSkillConfig(config, skillKey);
  const allowBundled = normalizeAllowlist(config?.skills?.allowBundled);

  // 检查技能是否被显式禁用
  if (skillConfig?.enabled === false) {
    return false;
  }

  // 检查内置技能是否允许
  if (!isBundledSkillAllowed(entry, allowBundled)) {
    return false;
  }

  // 运行时资格检查
  return evaluateRuntimeEligibility({...});
}
```

### 2. 技能列表过滤

用户可以通过配置指定要加载的技能列表：

```typescript
function filterSkillEntries(
  entries: SkillEntry[],
  config?: OpenClawConfig,
  skillFilter?: string[],
  eligibility?: SkillEligibilityContext,
): SkillEntry[] {
  let filtered = entries.filter((entry) => 
    shouldIncludeSkill({ entry, config, eligibility })
  );

  // 如果提供了skillFilter，只包含过滤器中的技能
  if (skillFilter !== undefined) {
    const normalized = normalizeSkillFilter(skillFilter) ?? [];
    filtered = normalized.length > 0
      ? filtered.filter((entry) => normalized.includes(entry.skill.name))
      : [];
  }

  return filtered;
}
```

### 3. 运行时资格检查

```typescript
function evaluateRuntimeEligibility(params: EligibilityParams): boolean {
  const { os, remotePlatforms, always, requires, hasBin, hasRemoteBin, 
          hasAnyRemoteBin, hasEnv } = params;

  // 始终加载的技能
  if (always) {
    return true;
  }

  // 操作系统检查
  if (os && os.length > 0) {
    const currentOS = process.platform;
    if (!os.includes(currentOS)) {
      return false;
    }
  }

  // 二进制依赖检查
  if (requires?.bins) {
    const allBinsAvailable = requires.bins.every(bin => 
      hasBin(bin) || hasAnyRemoteBin?.(bin)
    );
    if (!allBinsAvailable) {
      return false;
    }
  }

  // 环境变量检查
  if (requires?.env) {
    const allEnvAvailable = requires.env.every(env => hasEnv(env));
    if (!allEnvAvailable) {
      return false;
    }
  }

  return true;
}
```

## 技能发现与加载

OpenClaw通过`workspace.ts`模块实现技能的发现和加载：

### 技能入口定义

```typescript
interface SkillEntry {
  skill: Skill;
  metadata?: OpenClawMetadata;
  source: 'builtin' | 'user' | 'project';
  path: string;
}
```

### 技能加载流程

1. **扫描技能目录**：从所有配置的技能目录中扫描`SKILL.md`文件
2. **解析技能元数据**：使用frontmatter解析器提取技能信息
3. **验证技能完整性**：检查必需字段和元数据格式
4. **应用过滤规则**：根据配置和运行时环境过滤技能
5. **构建技能索引**：创建技能名称到技能入口的映射

### 技能优先级处理

当多个位置存在同名技能时，OpenClaw按以下优先级选择：

1. 项目本地技能（最高优先级）
2. 用户自定义技能
3. 内置技能（最低优先级）

## 技能使用机制

### 技能触发

OpenClaw通过以下方式触发技能使用：

1. **自然语言匹配**：智能体根据用户输入和技能描述进行语义匹配
2. **工具调用**：技能提供的工具被智能体调用时自动激活
3. **显式引用**：用户可以明确指定使用某个技能

### 技能工具集成

技能可以定义多个工具，这些工具会被集成到OpenClaw的工具系统中：

```typescript
// 技能工具定义示例
const weatherTools = [
  {
    name: 'get_current_weather',
    description: '获取指定位置的当前天气',
    parameters: {
      type: 'object',
      properties: {
        location: {
          type: 'string',
          description: '城市名称或位置'
        }
      },
      required: ['location']
    }
  }
];
```

### 技能上下文

技能在执行时可以访问：

- 用户输入和对话历史
- 技能特定的配置和参数
- 系统环境和可用工具
- 其他技能提供的功能

## 技能配置管理

### 全局技能配置

```typescript
interface SkillsConfig {
  allowBundled?: string[] | 'all' | 'none';  // 允许的内置技能
  skillFilter?: string[];                    // 技能过滤列表
  [skillName: string]?: SkillConfig;         // 单个技能配置
}

interface SkillConfig {
  enabled?: boolean;                          // 是否启用
  apiKey?: string;                            // API密钥
  env?: Record<string, string>;              // 环境变量
}
```

### 技能配置示例

```yaml
# openclaw.config.yaml
skills:
  allowBundled: ['weather', 'github', 'file']
  weather:
    enabled: true
    apiKey: ${WEATHER_API_KEY}
  github:
    enabled: true
```

## 技能依赖管理

### 二进制依赖检查

OpenClaw会检查技能所需的二进制工具是否可用：

```typescript
function hasBinary(bin: string): boolean {
  try {
    require('child_process').execSync(`which ${bin}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}
```

### 环境变量检查

```typescript
function hasEnv(envName: string): boolean {
  return Boolean(process.env[envName]);
}
```

### 安装提示

当技能依赖缺失时，OpenClaw会提供安装建议：

```
⚠️  技能 'github' 需要以下依赖：
  - 二进制工具: gh

安装方法：
  brew: brew install gh
  apt:  sudo apt install gh
```

## 技能最佳实践

### 1. 清晰的技能描述

提供详细且准确的技能描述，帮助智能体理解何时使用技能：

```yaml
description: "GitHub操作：创建issue、管理PR、查看CI运行、代码审查、API查询。使用场景：用户需要与GitHub仓库交互、管理代码审查、自动化工作流时。"
```

### 2. 合理的依赖声明

只声明必要的依赖，避免过度限制技能使用：

```yaml
metadata:
  {
    "openclaw":
      {
        "requires": { "bins": ["gh"] },  // 只声明必需的工具
      },
  }
```

### 3. 完善的使用文档

在`SKILL.md`中提供详细的使用示例和最佳实践：

```markdown
## 使用示例

### 创建Issue
```
用户：帮我创建一个bug报告
智能体：[使用github技能创建issue]
```

### 查看PR状态
```
用户：检查PR #123的状态
智能体：[使用github技能查看PR信息]
```

## 技能生态系统

OpenClaw内置了丰富的技能库，包括：

- **文件操作**：文件读写、目录管理
- **网络工具**：HTTP请求、API调用
- **开发工具**：Git操作、代码分析
- **数据处理**：JSON解析、文本处理
- **系统管理**：进程管理、系统信息

用户可以通过创建自定义技能来扩展这些功能，构建适合自己工作流的技能生态系统。

## 总结

OpenClaw的技能系统通过灵活的加载机制、智能的过滤规则和完善的依赖管理，为用户提供了强大而可扩展的功能增强能力。通过合理配置和使用技能，可以显著提升智能体的工作效率和适用范围。