# OpenSpec：AI 原生的规范驱动开发框架

## 📋 目录

- [项目概述](#项目概述)
- [核心设计理念](#核心设计理念)
- [核心架构](#核心架构)
- [OPSX 工作流](#opsx-工作流)
- [Schema 驱动系统](#schema-驱动系统)
- [多 AI 工具支持](#多-ai-工具支持)
- [快速开始](#快速开始)
- [实际使用示例](#实际使用示例)
- [技术亮点](#技术亮点)
- [核心模块详解](#核心模块详解)
- [适用场景](#适用场景)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [社区与支持](#社区与支持)

---

## 项目概述

OpenSpec 是一个革命性的 AI 原生规范驱动开发框架，旨在帮助开发团队通过结构化的方式管理软件开发过程中的需求、设计和任务。它不是传统的文档工具，而是一个智能化的开发协作平台，能够与各种 AI 编码工具无缝集成。

### 核心定位

- 📦 **NPM 包名**：`@fission-ai/openspec`
- 🎯 **当前版本**：1.2.0
- 💡 **核心理念**：流动而非僵化、迭代而非瀑布、简单而非复杂、面向棕地项目而非仅绿地项目
- 🌟 **最受喜爱的规范框架**

### 技术栈

- **语言**：TypeScript (ES Module)
- **运行时**：Node.js >= 20.19.0
- **核心依赖**：
  - `commander` - CLI 框架
  - `@inquirer/prompts` - 交互式提示
  - `chalk` - 终端颜色输出
  - `zod` - 运行时数据验证
  - `yaml` - YAML 配置解析
  - `fast-glob` - 高性能文件匹配
  - `ora` - 优雅的终端加载动画

### 为什么选择 OpenSpec？

传统的规范系统存在以下问题：
- ❌ **阶段锁定**：必须按照固定顺序进行，无法灵活调整
- ❌ **重量级流程**：需要大量设置和配置
- ❌ **与 AI 工具脱节**：无法与现代 AI 编码工具集成
- ❌ **仅适合绿地项目**：难以应用于现有系统

OpenSpec 解决了这些问题：
- ✅ **流体式工作流**：按需创建制品，灵活调整顺序
- ✅ **轻量级设置**：几秒钟初始化，立即开始工作
- ✅ **AI 工具原生支持**：支持 20+ 种 AI 编码工具
- ✅ **棕地优先**：专为现有系统设计，支持增量变更

---

## 核心设计理念

OpenSpec 建立在四个核心原则之上：

### 1. 流动而非僵化 (Fluid not Rigid)

**传统方式**：
```
PLANNING ────────► IMPLEMENTING ────────► DONE
    │                    │
    │   "无法回退"       │
    └────────────────────┘
```

**OpenSpec 方式**：
```
proposal ──► specs ──► design ──► tasks ──► implement
    │            │          │          │
    └────────────┴──────────┴──────────┘
              随时可以调整和迭代
```

传统的规范系统将你锁定在阶段中：先规划，然后实施，最后完成。OpenSpec 更加灵活——你可以按照对你工作有意义的任何顺序创建制品。你可以在实施过程中发现设计问题，然后回到设计阶段更新，而不会"破坏流程"。

### 2. 迭代而非瀑布 (Iterative not Waterfall)

需求会变化，理解会加深。开始时看似不错的方法在看到代码库后可能站不住脚。OpenSpec 拥抱这一现实：

- 🔄 **需求演进**：随着项目进展，需求可以自然演进
- 📈 **理解加深**：实现过程中的新发现可以反馈到规范中
- 🔧 **灵活调整**：不需要"重新开始"，只需更新相关制品

### 3. 简单而非复杂 (Easy not Complex)

一些规范框架需要大量设置、僵化格式或重量级流程。OpenSpec 不会妨碍你：

- ⚡ **快速初始化**：几秒钟内完成设置
- 🎯 **最小仪式**：只做必要的事情
- 🔌 **可选自定义**：仅在需要时才进行配置

### 4. 棕地优先 (Brownfield-first)

大多数软件工作不是从零开始构建——而是修改现有系统。OpenSpec 的基于增量的方法使得指定对现有行为的修改变得容易：

- 🏗️ **增量变更**：只描述变化的部分，不需要重写整个系统
- 📊 **Delta 操作**：使用 ADDED/MODIFIED/REMOVED 操作精确描述变更
- 🔍 **影响分析**：清晰识别受影响的代码、API 和依赖

---

## 核心架构

### 双区域架构

OpenSpec 采用独特的双区域架构来组织工作：

```
┌─────────────────────────────────────────────────────────┐
│                    openspec/                             │
│                                                          │
│   ┌──────────────────┐      ┌────────────────────────┐  │
│   │     specs/       │      │       changes/          │  │
│   │                  │      │                         │  │
│   │  系统当前行为     │◄─────│  提议的修改              │  │
│   │  的真实来源       │ merge│  每个变更 = 一个文件夹   │  │
│   │                  │      │  包含制品 + 增量         │  │
│   └──────────────────┘      └────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

#### Specs（规范）- 真实来源

描述系统当前行为的真实来源，组织方式：

```
openspec/specs/
├── auth/
│   └── spec.md           # 认证行为
├── payments/
│   └── spec.md           # 支付处理
├── notifications/
│   └── spec.md           # 通知系统
└── ui/
    └── spec.md           # UI 行为和主题
```

**组织模式**：
- **按功能区域**：`auth/`、`payments/`、`search/`
- **按组件**：`api/`、`frontend/`、`workers/`
- **按界限上下文**：`ordering/`、`fulfillment/`、`inventory/`

#### Changes（变更）- 提议的修改

每个变更独立文件夹管理，直到准备好合并：

```
openspec/changes/
├── add-dark-mode/
│   ├── proposal.md       # 为什么做这个变更
│   ├── specs/            # 需求和场景
│   ├── design.md         # 技术方法
│   └── tasks.md          # 实现清单
└── refactor-auth/
    ├── proposal.md
    ├── specs/
    └── tasks.md
```

**这种分离的优势**：
- ✅ 并行处理多个变更而不会冲突
- ✅ 在影响主规范之前审查变更
- ✅ 归档时增量干净地合并到真实来源

### 制品图系统 (Artifact Graph)

OpenSpec 使用制品图来管理依赖关系：

#### 核心功能

- **依赖跟踪**：每个制品可以声明它依赖的其他制品
- **状态检测**：自动检测哪些制品已完成
- **阻塞检测**：识别因依赖未完成而被阻塞的制品

#### 类型定义

```typescript
// 制品定义
Artifact = {
  id: string,           // 制品 ID
  generates: string,    // 生成的文件路径
  description: string,  // 描述
  template: string,     // 模板文件
  instruction: string,  // AI 指令
  requires: string[]    // 依赖的制品 ID
}

// Schema 定义
SchemaYaml = {
  name: string,
  version: number,
  artifacts: Artifact[],
  apply: ApplyPhase     // 应用阶段配置（可选）
}
```

#### 依赖关系示例

```
proposal (无依赖)
    ↓
specs (依赖 proposal)
    ↓
design (依赖 proposal)
    ↓
tasks (依赖 specs, design)
    ↓
implement (依赖 tasks)
```

### 目录结构详解

```
openspec/
├── config.yaml              # 项目配置（可选）
├── specs/                   # 当前系统规范
│   ├── auth/
│   │   └── spec.md
│   └── payments/
│       └── spec.md
├── changes/                 # 进行中的变更
│   ├── add-dark-mode/
│   │   ├── metadata.yaml    # 变更元数据
│   │   ├── proposal.md
│   │   ├── specs/
│   │   ├── design.md
│   │   └── tasks.md
│   └── refactor-auth/
│       └── ...
└── archive/                 # 已归档的变更
    └── 2025-01-23-add-dark-mode/
        └── ...
```

---

## OPSX 工作流

OPSX 是 OpenSpec 的标准工作流，采用流体式、迭代式方法。

### 核心理念：行动而非阶段

**传统工作流（阶段锁定）**：
```
PLANNING ────────► IMPLEMENTING ────────► DONE
    │                    │
    │   "无法回退"       │
    └────────────────────┘
```

**OPSX 工作流（流体行动）**：
```
proposal ──► specs ──► design ──► tasks ──► implement
    │           │          │          │
    └───────────┴──────────┴──────────┘
         可以随时回到任何步骤
```

**关键原则**：
- **行动而非阶段** - 命令是可以做的事情，而不是被困住的阶段
- **依赖是使能者** - 它们显示什么是可能的，而不是接下来必须做什么

### 两种工作模式

#### 默认快速路径 (Core Profile)

适合快速迭代和简单功能：

```bash
/opsx:propose ──► /opsx:apply ──► /opsx:archive
```

**特点**：
- ⚡ 最快的工作流
- 🎯 适合明确知道要做什么的情况
- 📦 自动创建所有必要的制品

#### 扩展工作流 (Expanded Profile)

适合复杂项目和需要更多控制的场景：

```bash
/opsx:new ──► /opsx:ff ──► /opsx:apply ──► /opsx:verify ──► /opsx:archive
```

**特点**：
- 🔍 更细粒度的控制
- ✅ 验证步骤确保质量
- 📊 适合团队协作

### 核心命令详解

| 命令 | 功能 | 依赖 | 使用场景 |
|------|------|------|----------|
| `/opsx:propose` | 创建提议 | 无 | 开始新功能开发，快速创建所有规划制品 |
| `/opsx:explore` | 探索代码库 | 无 | 了解现有系统，收集上下文信息 |
| `/opsx:new` | 创建新变更 | 无 | 明确知道要做什么，创建空变更目录 |
| `/opsx:continue` | 继续现有变更 | 无 | 恢复之前的工作，继续未完成的变更 |
| `/opsx:ff` | 快速前进 | proposal | 一次性创建所有规划制品（specs, design, tasks） |
| `/opsx:apply` | 实施变更 | specs, design, tasks | 开始编码实现，按任务清单执行 |
| `/opsx:verify` | 验证变更 | apply | 确保实现符合规范，运行测试 |
| `/opsx:sync` | 同步规范 | 无 | 更新系统当前状态，反映最新变更 |
| `/opsx:archive` | 归档变更 | apply | 完成并合并变更，更新主规范 |
| `/opsx:bulk-archive` | 批量归档 | 无 | 一次归档多个已完成的变更 |
| `/opsx:onboard` | 项目引导 | 无 | 为新项目创建初始规范结构 |

### 工作流模式

#### 模式 1：快速功能开发

适合小到中等功能、bug 修复、直接变更：

```text
/opsx:new ──► /opsx:ff ──► /opsx:apply ──► /opsx:verify ──► /opsx:archive
```

**示例对话**：
```text
You: /opsx:new add-logout-button

AI:  Created openspec/changes/add-logout-button/
     Ready to create: proposal

You: /opsx:ff

AI:  Creating all planning artifacts...
     ✓ proposal.md
     ✓ specs/
     ✓ design.md
     ✓ tasks.md
     Ready for implementation!

You: /opsx:apply

AI:  Working through tasks...
     ✓ Added logout button to header
     ✓ Implemented session clearing
     ✓ Added confirmation dialog
     All tasks complete!

You: /opsx:archive

AI:  ✓ Merged specs
     ✓ Archived change
```

#### 模式 2：探索性开发

适合需要先了解代码库的情况：

```text
/opsx:explore ──► /opsx:propose ──► /opsx:apply ──► /opsx:archive
```

#### 模式 3：迭代式开发

适合复杂功能，需要多次调整：

```text
/opsx:new ──► /opsx:continue ──► /opsx:continue ──► ... ──► /opsx:apply ──► /opsx:archive
```

---

## Schema 驱动系统

OpenSpec 使用 YAML 文件定义工作流，实现高度可定制化。

### Schema 文件位置

```
schemas/
└── spec-driven/
    ├── schema.yaml          # Schema 定义
    └── templates/           # 模板文件
        ├── proposal.md
        ├── spec.md
        ├── design.md
        └── tasks.md
```

### Schema 结构详解

```yaml
name: spec-driven
version: 1
description: Default OpenSpec workflow - proposal → specs → design → tasks

artifacts:
  # 制品 1：提议
  - id: proposal
    generates: proposal.md
    description: Initial proposal document outlining the change
    template: proposal.md
    instruction: |
      Create the proposal document that establishes WHY this change is needed.
      
      Sections:
      - **Why**: 1-2 sentences on the problem or opportunity
      - **What Changes**: Bullet list of changes
      - **Capabilities**: New or modified capabilities
      - **Impact**: Affected code, APIs, dependencies
    requires: []

  # 制品 2：规范
  - id: specs
    generates: "specs/**/*.md"
    description: Detailed specifications for the change
    template: spec.md
    instruction: |
      Create specification files that define WHAT the system should do.
      
      Use delta operations:
      - ADDED Requirements: New capabilities
      - MODIFIED Requirements: Changed behavior
      - REMOVED Requirements: Deprecated features
    requires:
      - proposal

  # 制品 3：设计
  - id: design
    generates: design.md
    description: Technical design document with implementation details
    template: design.md
    instruction: |
      Create the design document that explains HOW to implement the change.
      
      Sections:
      - Context: Background and constraints
      - Goals / Non-Goals: What this design achieves
      - Architecture: Technical approach
    requires:
      - proposal

  # 制品 4：任务
  - id: tasks
    generates: tasks.md
    description: Implementation checklist with trackable tasks
    template: tasks.md
    instruction: |
      Create a task breakdown for implementation.
      
      Format:
      - Use checkboxes for trackable items
      - Group related tasks
      - Include acceptance criteria
    requires:
      - specs
      - design

# 应用阶段配置
apply:
  requires:
    - tasks
  tracks: tasks.md
  instruction: |
    Implement the changes according to the task list.
```

### 制品详解

#### 1. proposal.md - 初始提议

**目的**：建立变更的"为什么"

**结构**：
```markdown
# Proposal: Add Dark Mode

## Why
Users have requested dark mode for better visibility in low-light environments
and to reduce eye strain during extended use.

## What Changes
- Add theme context provider
- Create dark/light mode toggle component
- Implement CSS variable-based theming
- Add localStorage persistence

## Capabilities

### New Capabilities
- `theme-management`: System-wide theme control

### Modified Capabilities
- `ui-components`: Update components to support theming

## Impact
- **Affected Code**: All UI components, layout components
- **APIs**: None
- **Dependencies**: No new dependencies
- **Migration**: Existing users will see light mode by default
```

#### 2. specs/**/*.md - 详细规范

**目的**：定义系统"应该做什么"

**Delta 操作**：

##### ADDED Requirements（新增需求）
```markdown
## ADDED Requirements

### Requirement: Theme Management
The system SHALL provide a theme management system that allows users to 
switch between light and dark modes.

#### Scenario: User toggles theme
- GIVEN a user on any page
- WHEN the user clicks the theme toggle
- THEN the theme switches between light and dark mode
- AND the preference is saved to localStorage

#### Scenario: Theme persistence
- GIVEN a user with a saved theme preference
- WHEN the user visits the application
- THEN the saved theme is applied automatically
```

##### MODIFIED Requirements（修改需求）
```markdown
## MODIFIED Requirements

### Requirement: Button Component
The button component SHALL support theme-aware styling.

**Previous behavior**: Buttons used hardcoded colors.
**New behavior**: Buttons use CSS variables for colors.

#### Scenario: Button in dark mode
- GIVEN the application is in dark mode
- WHEN a button is rendered
- THEN the button uses dark theme colors
- AND the button maintains proper contrast
```

##### REMOVED Requirements（移除需求）
```markdown
## REMOVED Requirements

### Requirement: Legacy Theme System
**Reason**: Replaced by new CSS variable-based theming system.
**Migration**: Update custom styles to use CSS variables instead of 
hardcoded colors.
```

#### 3. design.md - 技术设计

**目的**：解释"如何实现"

**结构**：
```markdown
# Design: Dark Mode Implementation

## Context
- Current state: No theming support, hardcoded colors
- Constraints: Must work with existing component library
- Stakeholders: Frontend team, Design team

## Goals / Non-Goals

### Goals
- Implement system-wide theme support
- Ensure smooth transitions between themes
- Maintain accessibility standards

### Non-Goals
- Custom theme creation by users
- More than two themes (light/dark)

## Architecture

### Component Structure
```
src/
├── contexts/
│   └── ThemeContext.tsx
├── components/
│   └── ThemeToggle.tsx
└── styles/
    └── theme.css
```

### Data Flow
```
User Click → ThemeToggle → ThemeContext → CSS Variables → UI Update
                ↓
          localStorage
```

### Technical Decisions
1. **CSS Variables**: Use CSS custom properties for dynamic theming
2. **Context API**: React Context for theme state management
3. **localStorage**: Persist theme preference across sessions
```

#### 4. tasks.md - 实现任务

**目的**：可追踪的实现清单

**格式**：
```markdown
# Tasks: Dark Mode Implementation

## Phase 1: Foundation
- [ ] 1.1 Create ThemeContext provider
- [ ] 1.2 Define CSS variables for light theme
- [ ] 1.3 Define CSS variables for dark theme
- [ ] 1.4 Add theme detection on app load

## Phase 2: UI Components
- [ ] 2.1 Create ThemeToggle component
- [ ] 2.2 Add toggle to header
- [ ] 2.3 Implement smooth transition animation
- [ ] 2.4 Add keyboard accessibility

## Phase 3: Integration
- [ ] 3.1 Update all components to use CSS variables
- [ ] 3.2 Test theme switching
- [ ] 3.3 Test localStorage persistence
- [ ] 3.4 Verify accessibility compliance

## Acceptance Criteria
- ✅ Theme persists across page reloads
- ✅ All components support both themes
- ✅ Smooth transition between themes
- ✅ Accessible via keyboard navigation
```

---

## 多 AI 工具支持

OpenSpec 支持 20+ 种 AI 编码工具，通过适配器模式实现无缝集成。

### 支持的 AI 工具

#### 主流 IDE 集成
- **Claude** (`.claude/skills/`)
- **Cursor** (`.cursor/rules/`)
- **Windsurf** (`.windsurf/rules/`)
- **GitHub Copilot** (`.github/copilot-instructions.md`)

#### AI 编码助手
- **CodeX**
- **Cline**
- **Amazon Q**
- **Gemini**
- **Continue**
- **CodeBuddy**
- **Kiro**
- **KiloCode**
- **Qwen**
- **Qoder**
- **Pi**
- **Auggie**
- **Antigravity**
- **CoStrict**
- **Crush**
- **OpenCode**
- **iFlow**

### 适配器模式

#### 核心接口

```typescript
// 命令内容
interface CommandContent {
  name: string;         // 命令名称
  description: string;  // 描述
  content: string;      // 命令内容
}

// 生成的命令
interface GeneratedCommand {
  filename: string;     // 文件名
  content: string;      // 文件内容
}

// 工具适配器
interface ToolCommandAdapter {
  name: string;         // 适配器名称
  extension: string;    // 文件扩展名
  generateCommand: (content: CommandContent) => GeneratedCommand;
}
```

#### 适配器示例

**Claude 适配器**：
```typescript
const claudeAdapter: ToolCommandAdapter = {
  name: 'claude',
  extension: '.md',
  generateCommand: (content: CommandContent) => ({
    filename: `${content.name}.md`,
    content: `---
name: ${content.name}
description: ${content.description}
---

${content.content}`
  })
};
```

**Cursor 适配器**：
```typescript
const cursorAdapter: ToolCommandAdapter = {
  name: 'cursor',
  extension: '.mdc',
  generateCommand: (content: CommandContent) => ({
    filename: `${content.name}.mdc`,
    content: `---
description: ${content.description}
---

${content.content}`
  })
};
```

### 命令生成流程

```
1. 加载 Schema
   ↓
2. 解析 Artifacts
   ↓
3. 生成 CommandContent
   ↓
4. 选择适配器
   ↓
5. 生成工具特定命令
   ↓
6. 写入文件
```

### 自定义 AI 工具支持

要添加新的 AI 工具支持：

1. **创建适配器**：
```typescript
// src/core/command-generation/adapters/my-tool.ts
export const myToolAdapter: ToolCommandAdapter = {
  name: 'my-tool',
  extension: '.myext',
  generateCommand: (content: CommandContent) => ({
    filename: `${content.name}.myext`,
    content: `# ${content.name}\n\n${content.content}`
  })
};
```

2. **注册适配器**：
```typescript
// src/core/command-generation/adapters/index.ts
export { myToolAdapter } from './my-tool.js';
```

3. **更新工厂**：
```typescript
// src/core/command-generation/adapters/factory.ts
import { myToolAdapter } from './my-tool.js';

export function getAdapter(toolName: string): ToolCommandAdapter | undefined {
  const adapters = {
    'claude': claudeAdapter,
    'cursor': cursorAdapter,
    'my-tool': myToolAdapter,
    // ...
  };
  return adapters[toolName];
}
```

---

## 快速开始

### 安装

```bash
# 使用 npm
npm install -g @fission-ai/openspec@latest

# 使用 pnpm
pnpm install -g @fission-ai/openspec@latest

# 使用 yarn
yarn global add @fission-ai/openspec@latest
```

### 初始化项目

```bash
# 进入项目目录
cd your-project

# 初始化 OpenSpec
openspec init
```

初始化过程会：
1. ✅ 检测并清理旧版本制品
2. ✅ 创建 `openspec/` 目录结构
3. ✅ 为选定的 AI 工具生成技能文件
4. ✅ 创建项目配置文件（可选）
5. ✅ 生成斜杠命令

### 项目配置

创建 `openspec/config.yaml`：

```yaml
# Schema 配置
schema: spec-driven

# 项目上下文（注入到所有制品）
context: |
  Tech stack: TypeScript, React, Node.js
  API conventions: RESTful, JSON responses
  Testing: Vitest for unit tests, Playwright for e2e
  Style: ESLint with Prettier, strict TypeScript
  Database: PostgreSQL with Prisma ORM
  Deployment: Docker containers on AWS ECS

# 规则配置（针对特定制品的规则）
rules:
  proposal:
    - Include rollback plan
    - Identify affected teams
    - Estimate effort in story points
  specs:
    - Use Given/When/Then format for scenarios
    - Include performance requirements
    - Specify error handling
  design:
    - Include sequence diagrams for complex flows
    - Document API contracts
    - Consider scalability implications
  tasks:
    - Break down into 2-4 hour chunks
    - Include testing tasks
    - Mark dependencies between tasks
```

### 配置字段说明

#### schema
指定使用的工作流 schema，默认为 `spec-driven`。

#### context
项目上下文信息，会被注入到所有制品的 AI 指令中，帮助 AI 更好地理解项目。

#### rules
针对特定制品的规则，会在生成对应制品时附加到 AI 指令中。

### 选择工作流模式

```bash
# 查看当前配置
openspec config

# 切换到扩展工作流
openspec config profile

# 更新配置
openspec update
```

---

## 实际使用示例

### 示例 1：添加暗黑模式

```text
You: /opsx:propose add-dark-mode

AI:  Created openspec/changes/add-dark-mode/
     ✓ proposal.md — why we're doing this, what's changing
     ✓ specs/       — requirements and scenarios
     ✓ design.md    — technical approach
     ✓ tasks.md     — implementation checklist
     Ready for implementation!

You: /opsx:apply

AI:  Implementing tasks...
     ✓ 1.1 Add theme context provider
     ✓ 1.2 Create toggle component
     ✓ 2.1 Add CSS variables
     ✓ 2.2 Wire up localStorage
     All tasks complete!

You: /opsx:archive

AI:  Archived to openspec/changes/archive/2025-01-23-add-dark-mode/
     Specs updated. Ready for the next feature.
```

### 示例 2：重构认证系统

```text
You: /opsx:new refactor-auth

AI:  Created openspec/changes/refactor-auth/
     Ready to create: proposal

You: /opsx:continue

AI:  What would you like to work on?
     Available artifacts: proposal, specs, design, tasks

You: Create the proposal

AI:  Creating proposal.md...
     ✓ Added motivation for refactoring
     ✓ Identified affected components
     ✓ Listed breaking changes
     Proposal complete!

You: /opsx:ff

AI:  Creating remaining artifacts...
     ✓ specs/auth/spec.md
     ✓ design.md
     ✓ tasks.md
     All planning artifacts ready!

You: /opsx:apply

AI:  Starting implementation...
     [Working through tasks...]

You: /opsx:verify

AI:  Running verification...
     ✓ All tests passing
     ✓ Specs validated
     ✓ No breaking changes detected
     Verification complete!

You: /opsx:archive

AI:  Archiving change...
     ✓ Merged specs into openspec/specs/auth/
     ✓ Moved to archive/2025-01-24-refactor-auth/
     Change archived successfully!
```

### 示例 3：探索性开发

```text
You: /opsx:explore

AI:  Exploring codebase...
     Found:
     - 15 React components
     - 3 API endpoints
     - 2 database models
     - Current auth flow: JWT-based
     
     Suggested areas for improvement:
     - Add rate limiting to API
     - Implement caching layer
     - Refactor large components

You: /opsx:propose add-rate-limiting

AI:  Based on exploration, creating proposal...
     ✓ proposal.md
     ✓ specs/api/spec.md
     ✓ tasks.md
     Ready for implementation!
```

---

## 技术亮点

### 1. 高度可扩展性

#### Schema 驱动
- 📝 通过 YAML 文件定义工作流，无需修改代码
- 🔄 支持多个 Schema，针对不同项目类型
- 🎨 完全自定义制品序列和依赖关系

#### 模板系统
- 📄 可自定义指令和模板
- 🌐 支持多语言模板
- 🔧 模板变量替换

#### 适配器模式
- 🔌 轻松支持新的 AI 工具
- 🎯 工具特定的格式化
- 📦 模块化设计

### 2. 完善的验证机制

#### Zod Schema 验证
```typescript
// 运行时类型验证
const ArtifactSchema = z.object({
  id: z.string().min(1),
  generates: z.string().min(1),
  template: z.string().min(1),
  requires: z.array(z.string()).default([]),
});
```

#### 依赖检查
- ✅ 确保制品依赖关系正确
- 🚫 检测循环依赖
- 📊 可视化依赖图

#### 格式验证
- 📝 Markdown 格式验证
- 🏷️ 标题层级检查
- 📋 场景格式验证（Given/When/Then）

### 3. 优秀的开发体验

#### 交互式 CLI
- 💬 使用 Inquirer 提供友好的交互体验
- 🎨 彩色输出和格式化
- ⌨️ 键盘导航支持

#### 进度反馈
- ⏳ 使用 Ora 提供加载动画
- ✅ 实时任务进度
- 📊 完成状态可视化

#### Shell 补全
- 🐚 支持 Bash、Zsh、Fish、PowerShell
- 📝 命令和参数自动补全
- 🎯 上下文感知建议

### 4. 智能迁移系统

#### 自动迁移
- 🔍 检测旧版本制品
- 📦 自动转换到新格式
- 📋 迁移日志和报告

#### 版本兼容
- 🔄 向后兼容旧版本
- 📈 平滑升级路径
- 🛡️ 数据完整性保证

### 5. Profile 系统

#### Core Profile
- ⚡ 快速工作流
- 🎯 最小命令集
- 📦 适合快速迭代

#### Expanded Profile
- 🔍 完整工作流
- ✅ 验证步骤
- 👥 团队协作功能

---

## 核心模块详解

### Artifact Graph（制品图）

**位置**：`src/core/artifact-graph/`

**核心功能**：
- 管理制品之间的依赖关系
- 跟踪制品完成状态
- 阻塞检测（哪些制品因依赖未完成而被阻塞）

**核心类**：
```typescript
class ArtifactGraph {
  // 加载 Schema
  loadSchema(schemaPath: string): SchemaYaml;
  
  // 检测已完成的制品
  detectCompleted(changeDir: string): CompletedSet;
  
  // 获取被阻塞的制品
  getBlockedArtifacts(completed: CompletedSet): BlockedArtifacts;
  
  // 获取下一个可创建的制品
  getNextAvailable(completed: CompletedSet): Artifact[];
}
```

**使用示例**：
```typescript
const graph = new ArtifactGraph();
const schema = graph.loadSchema('schemas/spec-driven/schema.yaml');
const completed = graph.detectCompleted('openspec/changes/add-dark-mode');
const blocked = graph.getBlockedArtifacts(completed);

console.log('Completed:', completed);
// Output: Set { 'proposal' }

console.log('Blocked:', blocked);
// Output: { tasks: ['specs', 'design'] }
```

### Command Generation（命令生成）

**位置**：`src/core/command-generation/`

**核心功能**：为不同的 AI 编码工具生成对应的命令格式

**核心类**：
```typescript
class CommandAdapterRegistry {
  // 注册适配器
  register(name: string, adapter: ToolCommandAdapter): void;
  
  // 获取适配器
  get(name: string): ToolCommandAdapter | undefined;
  
  // 列出所有适配器
  list(): string[];
}

// 生成命令
function generateCommands(
  contents: CommandContent[],
  adapter: ToolCommandAdapter
): GeneratedCommand[];
```

**使用示例**：
```typescript
const registry = new CommandAdapterRegistry();
registry.register('claude', claudeAdapter);
registry.register('cursor', cursorAdapter);

const adapter = registry.get('claude');
const commands = generateCommands(commandContents, adapter);

commands.forEach(cmd => {
  fs.writeFileSync(`.claude/skills/${cmd.filename}`, cmd.content);
});
```

### Parsers（解析器）

**位置**：`src/core/parsers/`

**核心解析器**：

#### Markdown Parser
```typescript
class MarkdownParser {
  // 解析 Markdown 文件
  parse(content: string): MarkdownDocument;
  
  // 提取标题
  extractHeadings(): Heading[];
  
  // 提取代码块
  extractCodeBlocks(): CodeBlock[];
}
```

#### Change Parser
```typescript
class ChangeParser {
  // 解析变更目录
  parseChangeDir(dir: string): Change;
  
  // 解析元数据
  parseMetadata(file: string): ChangeMetadata;
  
  // 验证变更完整性
  validate(change: Change): ValidationResult;
}
```

#### Requirement Blocks Parser
```typescript
class RequirementBlocksParser {
  // 解析需求块
  parseRequirements(content: string): Requirement[];
  
  // 解析场景
  parseScenarios(requirement: Requirement): Scenario[];
  
  // 提取 Delta 操作
  extractDeltaOperations(content: string): DeltaOperation[];
}
```

### Validation（验证）

**位置**：`src/core/validation/`

**核心功能**：
- Schema 验证
- 制品格式验证
- 依赖关系验证

**验证器**：
```typescript
class Validator {
  // 验证 Schema
  validateSchema(schema: unknown): SchemaYaml;
  
  // 验证制品
  validateArtifact(artifact: unknown): Artifact;
  
  // 验证变更
  validateChange(change: Change): ValidationResult;
  
  // 验证依赖关系
  validateDependencies(artifacts: Artifact[]): DependencyValidation;
}
```

### Templates & Workflows（模板与工作流）

**位置**：`src/core/templates/`

**核心功能**：
- 工作流模板管理
- 技能模板生成
- 指令模板加载

**模板类型**：
```typescript
// 工作流模板
interface WorkflowTemplate {
  name: string;
  description: string;
  steps: WorkflowStep[];
}

// 技能模板
interface SkillTemplate {
  name: string;
  description: string;
  content: string;
}

// 指令模板
interface InstructionTemplate {
  artifactId: string;
  instruction: string;
  variables: Record<string, string>;
}
```

---

## 适用场景

### ✅ 适合使用 OpenSpec 的场景

#### 1. 团队协作开发
- **场景**：多人协作的大型项目
- **优势**：
  - 统一的规范格式
  - 清晰的变更追踪
  - 易于代码审查
  - 知识传承

#### 2. 复杂需求管理
- **场景**：需求变更频繁，需要追踪历史
- **优势**：
  - 增量变更记录
  - 需求演进追踪
  - 影响范围分析
  - 回滚支持

#### 3. AI 辅助开发
- **场景**：使用 AI 编码工具的开发者
- **优势**：
  - 20+ AI 工具支持
  - 结构化上下文
  - 智能指令生成
  - 自动化工作流

#### 4. 棕地项目
- **场景**：现有系统的维护和升级
- **优势**：
  - 增量变更支持
  - 现有规范导入
  - 影响分析
  - 迁移路径规划

#### 5. 文档驱动开发
- **场景**：重视文档和规范的项目
- **优势**：
  - 活文档（Living Documentation）
  - 代码与文档同步
  - 自动化文档生成
  - 版本化文档

### ❌ 不太适合的场景

#### 1. 小型个人项目
- **原因**：可能过于重量级
- **建议**：使用简单的 TODO 列表或 Issue 跟踪

#### 2. 快速原型开发
- **原因**：需要快速迭代，不需要详细文档
- **建议**：先完成原型，再引入 OpenSpec

#### 3. 纯前端/UI 项目
- **原因**：可能不需要复杂的需求管理
- **建议**：使用设计系统和组件文档

#### 4. 一次性脚本
- **原因**：不需要长期维护
- **建议**：简单的注释和 README 即可

---

## 最佳实践

### 1. 组织规范

#### 按领域组织
```
openspec/specs/
├── authentication/      # 认证领域
│   ├── login/
│   ├── logout/
│   └── session/
├── payments/           # 支付领域
│   ├── checkout/
│   ├── refund/
│   └── subscription/
└── notifications/      # 通知领域
    ├── email/
    ├── push/
    └── sms/
```

#### 组织原则
- 🎯 **单一职责**：每个规范文件关注一个能力
- 📊 **合理粒度**：不要太粗（难以维护）或太细（碎片化）
- 🔗 **清晰边界**：规范之间有明确的界限
- 📈 **可扩展**：便于添加新的需求

### 2. 编写需求

#### 使用规范性语言
```markdown
✅ 好的写法：
The system SHALL issue a JWT token upon successful login.

❌ 不好的写法：
The system should issue a token when user logs in.
```

#### 每个需求至少有一个场景
```markdown
### Requirement: User Authentication
The system SHALL issue a JWT token upon successful login.

#### Scenario: Valid credentials
- GIVEN a user with valid credentials
- WHEN the user submits login form
- THEN a JWT token is returned
- AND the user is redirected to dashboard

#### Scenario: Invalid credentials
- GIVEN invalid credentials
- WHEN the user submits login form
- THEN an error message is displayed
- AND the login form is shown again
```

#### 场景使用 Given/When/Then 格式
```markdown
✅ 好的写法：
- GIVEN a user with valid credentials
- WHEN the user submits login form
- THEN a JWT token is returned

❌ 不好的写法：
- User has valid credentials
- User submits form
- Token is returned
```

#### 保持需求可测试
每个场景应该可以直接转换为测试用例：
```typescript
// 场景：Valid credentials
test('should return JWT token for valid credentials', async () => {
  // GIVEN
  const user = await createUser({ email: 'test@example.com', password: 'password' });
  
  // WHEN
  const response = await request(app)
    .post('/login')
    .send({ email: 'test@example.com', password: 'password' });
  
  // THEN
  expect(response.status).toBe(200);
  expect(response.body.token).toBeDefined();
});
```

### 3. 管理变更

#### 每个变更一个文件夹
```
openspec/changes/
├── add-dark-mode/           # ✅ 好的命名
├── refactor-auth-system/    # ✅ 好的命名
├── fix-login-bug/           # ✅ 好的命名
└── misc-updates/            # ❌ 不好的命名（太模糊）
```

#### 使用描述性名称
- ✅ `add-dark-mode` - 清晰描述功能
- ✅ `refactor-auth-system` - 明确重构范围
- ✅ `fix-login-timeout` - 具体问题描述
- ❌ `update-1` - 无意义编号
- ❌ `changes` - 太通用
- ❌ `bugfix` - 不够具体

#### 完成后及时归档
```bash
# 完成变更后立即归档
/opsx:archive

# 不要让完成的变更堆积
# ❌ openspec/changes/ 中有 10+ 已完成的变更
# ✅ openspec/changes/ 中只有进行中的变更
```

#### 定期同步规范
```bash
# 定期运行同步命令
/opsx:sync

# 确保规范反映系统当前状态
# 特别是手动修改代码后
```

### 4. 配置项目

#### 提供项目上下文
```yaml
context: |
  Tech stack: TypeScript, React, Node.js, PostgreSQL
  Architecture: Microservices with event-driven communication
  Testing: Vitest (unit), Playwright (e2e), k6 (load)
  CI/CD: GitHub Actions with automated deployments
  Monitoring: DataDog for APM and logging
```

#### 设置团队特定规则
```yaml
rules:
  proposal:
    - Include rollback plan
    - Identify affected teams
    - Estimate effort in story points
    - Link to related tickets
  specs:
    - Use Given/When/Then format
    - Include performance requirements
    - Specify error handling
    - Document edge cases
  design:
    - Include sequence diagrams
    - Document API contracts
    - Consider scalability
    - Address security concerns
```

#### 包含技术栈和约定
```yaml
context: |
  Code Style:
    - ESLint with Airbnb config
    - Prettier for formatting
    - Strict TypeScript
    - Prefer functional components
  
  Naming Conventions:
    - Components: PascalCase
    - Functions: camelCase
    - Constants: SCREAMING_SNAKE_CASE
    - Files: kebab-case
```

### 5. 与 AI 工具协作

#### 提供清晰的上下文
```text
✅ 好的提示：
/opsx:propose add-pagination-to-user-list

Current user list shows all users at once, causing performance 
issues when there are 1000+ users. Need to implement server-side 
pagination with 20 items per page.

❌ 不好的提示：
/opsx:propose fix-user-list
```

#### 逐步完善制品
```text
# 不要期望一次完成所有工作
You: /opsx:new add-feature

AI:  Created change directory...

You: Review and update the proposal

AI:  [Shows proposal for review]

You: Add more details to the performance requirements

AI:  [Updates proposal]

You: /opsx:continue

AI:  Creating specs...
```

#### 验证 AI 输出
```text
You: /opsx:apply

AI:  [Implementing...]

You: Review the implementation

AI:  [Shows code changes]

You: The implementation doesn't match the spec for error handling

AI:  [Updates implementation]

You: /opsx:verify

AI:  ✓ All specs validated
```

---

## 常见问题

### Q1: OpenSpec 与传统文档工具有什么区别？

**A**: OpenSpec 不是传统的文档工具，而是一个 AI 原生的开发协作平台：

| 特性 | 传统文档工具 | OpenSpec |
|------|-------------|----------|
| 文档位置 | 独立的文档系统 | 代码仓库中的活文档 |
| 更新方式 | 手动更新 | 与代码同步更新 |
| AI 集成 | 无或有限 | 原生支持 20+ AI 工具 |
| 工作流 | 线性、僵化 | 流体、迭代 |
| 变更追踪 | 版本控制 | 增量变更 + 归档 |

### Q2: 如何在现有项目中引入 OpenSpec？

**A**: 分步引入：

1. **初始化**：
```bash
cd existing-project
openspec init
```

2. **导入现有规范**（如果有）：
```bash
# 手动创建 openspec/specs/ 目录
# 将现有文档转换为 OpenSpec 格式
```

3. **从小变更开始**：
```text
/opsx:new small-feature
/opsx:apply
/opsx:archive
```

4. **逐步扩展**：
- 为核心模块创建规范
- 建立团队工作流程
- 自定义配置

### Q3: OpenSpec 会增加开发负担吗？

**A**: 短期可能增加少量工作，但长期收益巨大：

**短期成本**：
- 学习曲线：1-2 天
- 编写规范：每个变更额外 10-20 分钟

**长期收益**：
- 减少沟通成本：清晰的规范减少误解
- 提高代码质量：规范驱动减少 bug
- 加速新人上手：活文档是最好的教程
- AI 辅助效率：结构化上下文提高 AI 准确性

### Q4: 如何处理大型团队协作？

**A**: OpenSpec 支持团队协作的最佳实践：

1. **分支策略**：
```bash
# 每个变更一个分支
git checkout -b feature/add-dark-mode

# 变更目录在分支中
openspec/changes/add-dark-mode/
```

2. **代码审查**：
```text
# PR 中包含完整的变更制品
- proposal.md - 理解变更意图
- specs/ - 验证需求完整性
- design.md - 评估技术方案
- tasks.md - 检查实现计划
```

3. **冲突解决**：
```bash
# 规范文件冲突
# 使用标准 Git 合并工具

# 变更目录冲突
# 通常不会冲突（每个变更独立目录）
```

4. **团队配置**：
```yaml
# 共享的 openspec/config.yaml
# 提交到代码仓库
# 所有团队成员使用相同配置
```

### Q5: 如何自定义工作流？

**A**: 创建自定义 Schema：

1. **创建 Schema 文件**：
```yaml
# schemas/custom-workflow/schema.yaml
name: custom-workflow
version: 1
description: Custom workflow for my team

artifacts:
  - id: idea
    generates: idea.md
    template: idea.md
    instruction: |
      Describe the initial idea...
    requires: []
  
  - id: prototype
    generates: prototype.md
    template: prototype.md
    instruction: |
      Document the prototype...
    requires:
      - idea
  
  - id: spec
    generates: spec.md
    template: spec.md
    instruction: |
      Create detailed specification...
    requires:
      - prototype
```

2. **创建模板文件**：
```markdown
<!-- schemas/custom-workflow/templates/idea.md -->
# Idea: {{changeName}}

## Problem
[What problem does this solve?]

## Solution
[What is the proposed solution?]

## Success Criteria
[How do we measure success?]
```

3. **更新项目配置**：
```yaml
# openspec/config.yaml
schema: custom-workflow
```

### Q6: OpenSpec 支持多语言吗？

**A**: 是的，OpenSpec 支持多语言：

1. **模板多语言**：
```
schemas/
└── spec-driven/
    └── templates/
        ├── en/
        │   ├── proposal.md
        │   └── spec.md
        └── zh/
            ├── proposal.md
            └── spec.md
```

2. **配置语言**：
```yaml
# openspec/config.yaml
language: zh  # 使用中文模板
```

3. **自定义指令**：
```yaml
# 在 Schema 中使用中文指令
artifacts:
  - id: proposal
    instruction: |
      创建提议文档，说明为什么需要这个变更。
      
      包含以下部分：
      - **为什么**：1-2 句话说明问题或机会
      - **变更内容**：变更列表
      - **能力**：新增或修改的能力
      - **影响**：受影响的代码、API、依赖
```

---

## 社区与支持

### 官方资源

- **GitHub 仓库**：https://github.com/Fission-AI/OpenSpec
- **NPM 包**：https://www.npmjs.com/package/@fission-ai/openspec
- **Discord 社区**：https://discord.gg/YctCnvvshC
- **Twitter**：关注 [@0xTab](https://x.com/0xTab) 获取更新

### 团队支持

使用 OpenSpec 的团队可以申请访问 Slack 频道：
- **邮箱**：teams@openspec.dev

### 贡献指南

欢迎贡献代码、报告问题或提出建议：

1. **Fork 仓库**
2. **创建特性分支**：`git checkout -b feature/amazing-feature`
3. **提交更改**：`git commit -m 'Add amazing feature'`
4. **推送分支**：`git push origin feature/amazing-feature`
5. **创建 Pull Request**

### 行为准则

请阅读并遵守我们的行为准则，确保社区友好和包容。

---

## 许可证

OpenSpec 采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 总结

OpenSpec 是一个设计精良的规范驱动开发框架，它通过以下特点重新定义了软件开发流程：

✅ **架构清晰** - 双区域架构分离关注点  
✅ **扩展性强** - Schema 驱动，支持自定义工作流  
✅ **工具友好** - 支持 20+ 种 AI 编码工具  
✅ **迭代友好** - 流体式工作流，支持随时调整  
✅ **验证完善** - 多层次验证确保数据一致性  
✅ **文档齐全** - 完善的文档和示例  

它特别适合需要规范化开发流程、管理复杂需求变更的团队使用。通过将规范管理与 AI 工具深度集成，OpenSpec 为现代软件开发提供了一个强大而灵活的解决方案。

无论你是个人开发者还是大型团队，OpenSpec 都能帮助你更好地组织开发工作，提高代码质量，并确保需求与实现的一致性。

---

**开始使用 OpenSpec，让规范驱动你的开发流程！** 🚀
