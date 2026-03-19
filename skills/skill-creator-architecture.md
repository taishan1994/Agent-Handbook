# Skill-Creator：构建智能体技能的元技能系统深度解析

## 摘要

Skill-Creator 是一个用于创建、修改、改进和评估智能体技能（Skills）的元技能系统。它提供了一套完整的工具链，从技能的初始设计到自动化测试、迭代优化和性能基准测试，形成了一个闭环的技能开发工作流。本文将深入解析 Skill-Creator 的整体架构、核心组件、数据流和工作流程，帮助读者理解如何构建高质量的智能体技能。

---

## 1. 系统概述

Skill-Creator 的核心使命是**让技能开发变得系统化、可量化和可迭代**。它不仅仅是一个技能编写工具，而是一个完整的技能生命周期管理系统，涵盖了从需求捕获、技能编写、测试评估、性能分析到持续优化的全流程。

### 1.1 核心设计理念

1. **渐进式披露（Progressive Disclosure）**：技能内容按需加载的层次组织，避免不必要的上下文消耗
   - Level 1：YAML frontmatter（name + description）- 始终在上下文中
   - Level 2：SKILL.md 主体内容（<500行理想）
   - Level 3：捆绑资源（scripts/references/assets）- 按需加载

2. **数据驱动决策**：所有改进决策都基于量化的评估数据，而非主观判断

3. **盲评机制**：通过盲比较消除偏见，确保技能质量评估的客观性

4. **迭代优化**：支持训练/测试集分离，防止过拟合，确保技能的泛化能力

### 1.2 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Skill-Creator 元技能                    │
├─────────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  │
│  │   SKILL.md    │  │  Scripts/    │  │
│  │  (核心定义)  │  │  (工具链)    │  │
│  └──────────────┘  └──────────────┘  │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  Agents/      │  │  References/  │  │
│  │  (智能体)    │  │  (文档)      │  │
│  └──────────────┘  └──────────────┘  │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  │
│  │  Eval-Viewer/ │  │  Assets/     │  │
│  │  (可视化)    │  │  (资源)      │  │
│  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 核心组件详解

### 2.1 SKILL.md - 技能定义文件

SKILL.md 是技能的核心定义文件，采用 YAML frontmatter + Markdown 结构：

```yaml
---
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance.
---

# Skill Creator

技能的主体内容...
```

**关键字段**：
- `name`：技能标识符（小写、连字符分隔）
- `description`：触发描述（决定技能何时被加载）
- `compatibility`：可选的依赖和工具要求

**内容组织原则**：
- 使用命令式指令（"做X，然后做Y"）
- 解释"为什么"而非强制"必须"
- 包含具体示例和输出格式模板
- 保持简洁（理想<500行，超出则分层引用）

### 2.2 三大核心智能体

Skill-Creator 包含三个专门的智能体，每个负责不同的评估任务：

#### 2.2.1 Grader Agent - 评分智能体

**职责**：评估期望（expectations）与执行结果和输出文件

**工作流程**：
1. 读取执行脚本（transcript）
2. 检查输出文件
3. 对每个期望进行评估：
   - 搜索证据
   - 确定通过/失败
   - 引用具体证据
4. 提取和验证隐式声明（claims）
5. 读取用户笔记和执行指标
6. 批评期望本身（识别无意义或遗漏的期望）

**输出格式**（grading.json）：
```json
{
  "expectations": [
    {
      "text": "The output includes name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {...},
    "total_tool_calls": 15,
    "total_steps": 6
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0
  },
  "claims": [...],
  "user_notes_summary": {...},
  "eval_feedback": {
    "suggestions": [...],
    "overall": "Assessments check presence but not correctness."
  }
}
```

**评分标准**：
- **PASS**：有明确证据且反映真实任务完成
- **FAIL**：无证据、证据矛盾或证据肤浅
- **不确定时**：举证责任在期望方

#### 2.2.2 Comparator Agent - 盲比较智能体

**职责**：在不了解哪个技能产生哪个输出的情况下，比较两个输出并判定胜者

**工作流程**：
1. 读取两个输出（A和B）
2. 理解任务要求
3. 生成评估标准（内容+结构两个维度）
4. 对每个输出进行评分（1-5分制）
5. 检查期望（如果提供）
6. 确定胜者（主要：总分；次要：期望通过率）

**输出格式**（comparison.json）：
```json
{
  "winner": "A",
  "reasoning": "Output A provides a complete solution...",
  "rubric": {
    "A": {
      "content": {...},
      "structure": {...},
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {...}
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": [...],
      "weaknesses": [...]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80
    }
  }
}
```

**盲评原则**：
- 纯粹基于输出质量和任务完成度
- 不尝试推断哪个技能产生哪个输出
- 避免对特定技能或风格的偏见

#### 2.2.3 Analyzer Agent - 分析智能体

**职责**：分析基准测试结果和盲比较结果，提取可操作的洞察

**两种分析模式**：

**基准测试分析**：
1. 读取所有运行结果
2. 分析每个期望的模式（总是通过/失败/高变异）
3. 分析跨评估模式（某些类型更难/更容易）
4. 分析指标模式（时间、token、工具调用）
5. 生成基于数据的观察笔记

**盲比较分析**：
1. 读取比较结果和两个技能
2. 读取两个技能的SKILL.md
3. 读取两个执行脚本
4. 识别结构差异（指令清晰度、脚本使用、示例覆盖）
5. 比较执行模式（遵循指令程度、工具使用差异）
6. 识别胜者优势和败者弱点
7. 生成改进建议（按优先级：高/中/低）

**输出格式**（analysis.json）：
```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner",
    "loser_skill": "path/to/loser",
    "comparator_reasoning": "..."
  },
  "winner_strengths": [
    "Clear step-by-step instructions...",
    "Included validation script..."
  ],
  "loser_weaknesses": [
    "Vague instruction...",
    "No script for validation..."
  ],
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace vague instruction with explicit steps",
      "expected_impact": "Would eliminate ambiguity"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "...",
    "loser_execution_pattern": "..."
  }
}
```

### 2.3 工具脚本链

Skill-Creator 提供了一套完整的工具脚本，支持技能开发的各个阶段：

#### 2.3.1 核心工具脚本

**run_eval.py - 评估执行器**

功能：运行触发评估，测试技能描述是否导致Claude加载技能

核心机制：
- 为每个查询创建临时命令文件
- 使用 `claude -p` 运行查询
- 通过流事件（`stream_event`）早期检测技能触发
- 支持并行执行多个查询
- 计算触发率、精确率、召回率、准确率

关键代码逻辑：
```python
# 早期检测机制
if event.get("type") == "content_block_start":
    if cb.get("type") == "tool_use":
        if tool_name in ("Skill", "Read"):
            pending_tool_name = tool_name
elif se_type == "content_block_delta" and pending_tool_name:
    if delta.get("type") == "input_json_delta":
        accumulated_json += delta.get("partial_json", "")
        if clean_name in accumulated_json:
            return True  # 技能被触发
```

**run_loop.py - 迭代优化循环**

功能：结合评估和改进，自动迭代直到全部通过或达到最大迭代次数

核心特性：
- 支持训练/测试集分离（防止过拟合）
- 分层采样（按should_trigger分层）
- 实时报告生成（HTML自动刷新）
- 历史跟踪（每次迭代的描述和分数）
- 自动选择最佳版本（基于测试集分数）

工作流程：
```
for iteration in range(1, max_iterations + 1):
    1. 在训练集上评估当前描述
    2. 分离训练和测试结果
    3. 基于训练结果改进描述
    4. 更新当前描述
    5. 生成实时报告
```

**package_skill.py - 技能打包器**

功能：将技能文件夹打包成可分发的 .skill 文件

打包规则：
- 排除构建产物（`__pycache__`, `node_modules`）
- 排除临时文件（`.DS_Store`, `*.pyc`）
- 保留所有技能内容（SKILL.md, scripts/, references/, assets/）
- 创建ZIP格式的.skill文件

**improve_description.py - 描述优化器**

功能：基于评估结果自动改进技能描述

优化策略：
- 分析训练结果中的失败案例
- 泛化改进（避免过度拟合特定示例）
- 保持提示精简（移除无用的部分）
- 解释"为什么"而非强制"必须"
- 识别跨测试用例的重复工作

#### 2.3.2 辅助工具脚本

**quick_validate.py - 快速验证器**

功能：快速验证技能文件夹结构

检查项：
- SKILL.md 存在且格式正确
- YAML frontmatter 完整（name + description）
- 文件夹命名规范（小写、连字符、无空格）
- 必需文件存在

**aggregate_benchmark.py - 基准聚合器**

功能：聚合多次运行的结果，计算统计量

聚合指标：
- 通过率（mean ± stddev）
- 执行时间（mean ± stddev）
- Token使用量（mean ± stddev）
- 工具调用次数
- 配置间差异（delta）

**generate_report.py - 报告生成器**

功能：生成HTML格式的评估报告

报告特性：
- 双标签页（Outputs + Benchmark）
- 交互式查看（上一个/下一个导航）
- 实时反馈收集（自动保存为feedback.json）
- 历史对比（iteration 2+ 显示上一次迭代）
- 支持静态输出（无显示环境）

**utils.py - 工具函数**

功能：共享的实用函数

主要函数：
- `parse_skill_md()`：解析SKILL.md文件，提取name、description和完整内容
- 处理YAML多行指示符（`>`, `|`, `>-`, `|-`）

### 2.4 可视化组件

**eval-viewer/** - 评估结果查看器**

**viewer.html**：交互式Web界面

功能：
- **Outputs标签页**：
  - 显示每个测试用例的提示、输出、上一次输出
  - 显示正式评分（折叠）
  - 反馈文本框（自动保存）
  - 上一次反馈（迭代2+）

- **Benchmark标签页**：
  - 统计摘要（通过率、时间、token）
  - 每个测试的详细分解
  - 配置对比（with_skill vs without_skill vs old_skill）
  - 分析师观察笔记

**generate_review.py - 查看器生成器**

功能：
- 读取benchmark.json和相关数据
- 生成HTML报告
- 支持实时模式（auto_refresh）
- 支持静态模式（--static）

### 2.5 数据流与JSON模式

Skill-Creator 使用标准化的JSON格式在各个组件间传递数据：

#### 2.5.1 evals.json - 测试用例定义

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's task prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

#### 2.5.2 grading.json - 评分结果

包含期望评估、执行指标、时序数据、隐式声明和用户笔记

#### 2.5.3 benchmark.json - 基准测试聚合

包含元数据、所有运行结果、统计摘要、配置对比和观察笔记

#### 2.5.4 comparison.json - 盲比较结果

包含胜者判定、评分标准、输出质量评估和期望结果

#### 2.5.5 analysis.json - 分析结果

包含比较摘要、胜者优势、败者弱点、改进建议和执行模式洞察

#### 2.5.6 feedback.json - 用户反馈

```json
{
  "reviews": [
    {
      "run_id": "eval-0-with_skill",
      "feedback": "the chart is missing axis labels",
      "timestamp": "..."
    }
  ],
  "status": "complete"
}
```

---

## 3. 完整工作流程

### 3.1 阶段一：创建技能

#### 步骤1：捕获意图
- 从对话历史中提取工作流（如果存在）
- 理解用户想要技能做什么
- 确定触发条件（何时使用）
- 确定预期输出格式
- 决定是否需要测试用例

#### 步骤2：访谈和研究
- 主动询问边缘情况
- 确认输入/输出格式
- 查看示例文件
- 确定成功标准
- 检查可用的MCP工具
- 并行研究（通过子智能体或内联）

#### 步骤3：编写SKILL.md
- 填充YAML frontmatter
- 编写主体内容（使用命令式、解释"为什么"）
- 组织结构（工作流程、示例、最佳实践）
- 保持简洁（<500行）
- 包含具体示例和输出格式模板

#### 步骤4：编写测试用例
- 创建2-3个真实测试提示
- 保存到`evals/evals.json`
- 包含提示、预期输出和可选输入文件
- 暂不编写断言（稍后起草）

### 3.2 阶段二：运行和评估

#### 步骤1：启动所有运行（并行）
```
for each test case:
    # With-skill run
    启动子智能体，使用技能
    保存到: <workspace>/iteration-N/eval-ID/with_skill/outputs/

    # Baseline run
    启动子智能体，不使用技能（或使用旧版本）
    保存到: <workspace>/iteration-N/eval-ID/without_skill/outputs/
```

**关键点**：
- 在同一轮中启动所有运行（节省时间）
- 捕获时序数据（`timing.json`）
- 为每个运行创建`eval_metadata.json`

#### 步骤2：起草断言（运行进行时）
- 基于测试用例起草可验证的断言
- 解释给用户
- 更新`eval_metadata.json`和`evals/evals.json`
- 断言应客观可验证且有描述性名称

#### 步骤3：捕获时序数据
- 从任务通知中提取`total_tokens`和`duration_ms`
- 立即保存到`timing.json`
- 这是唯一机会捕获此数据

#### 步骤4：评分、聚合和启动查看器

**评分**：
- 启动评分智能体（grader.md）
- 评估每个断言
- 保存到`grading.json`

**聚合**：
- 运行聚合脚本
- 生成`benchmark.json`和`benchmark.md`
- 计算统计量（mean ± stddev, delta）

**分析**：
- 运行分析智能体（analyzer.md）
- 识别聚合统计可能隐藏的模式
- 生成观察笔记

**启动查看器**：
```bash
nohup python eval-viewer/generate_review.py \
  <workspace>/iteration-N \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-N/benchmark.json \
  > /dev/null 2>&1 &
```

#### 步骤5：读取反馈
- 用户在查看器中完成评估
- 点击"Submit All Reviews"
- 下载`feedback.json`
- 读取反馈并聚焦于有具体投诉的测试用例

### 3.3 阶段三：改进技能

#### 改进思维框架

1. **从反馈中泛化**：
   - 避免过度拟合特定示例
   - 尝试不同隐喻或模式
   - 关注根本问题而非表面症状

2. **保持提示精简**：
   - 移除不拉动其重量的部分
   - 阅读脚本而不仅是最终输出
   - 消除无生产力的步骤

3. **解释"为什么"**：
   - LLM有良好的心智理论
   - 解释推理而非强制"必须"
   - 避免大写"ALWAYS/NEVER"

4. **识别跨测试用例的重复工作**：
   - 查看所有测试用例的脚本
   - 如果多个测试用例都编写相同的辅助脚本
   - 将其打包到`scripts/`中

#### 迭代循环

```
for iteration in range(1, max_iterations + 1):
    1. 应用改进到技能
    2. 重新运行所有测试用例（新iteration-N+1/）
    3. 评估结果（评分、聚合、分析）
    4. 用户在查看器中审查
    5. 读取反馈
    6. 如果全部通过或达到最大迭代，退出
```

### 3.4 阶段四：优化描述（可选）

#### improve_description.py 的工作流程

1. **读取历史**：
   - 加载所有历史迭代
   - 对测试集结果进行盲化（移除test_分数）

2. **分析失败案例**：
   - 识别总是失败的期望
   - 识别有时失败的期望
   - 识别高变异的期望

3. **生成改进建议**：
   - 基于失败模式生成具体建议
   - 按优先级排序（高/中/低）
   - 解释预期影响

4. **重写描述**：
   - 应用改进
   - 保持简洁和清晰
   - 增强触发条件

---

## 4. 关键设计模式

### 4.1 盲评机制

**目的**：消除评估中的偏见

**实现**：
- Comparator Agent不知道A和B哪个技能产生
- 纯粹基于输出质量判定
- 避免对特定技能名称或风格的偏好

**好处**：
- 确保评估客观性
- 防止"品牌忠诚度"偏差
- 聚焦于任务完成度

### 4.2 训练/测试分离

**目的**：防止过拟合

**实现**：
- `split_eval_set()`函数按`should_trigger`分层采样
- 训练集用于改进描述
- 测试集用于选择最佳版本

**好处**：
- 确保技能泛化到未见过的查询
- 避免针对特定测试用例过度优化
- 提供真实的性能指标

### 4.3 渐进式披露

**目的**：优化上下文窗口使用

**实现**：
- Level 1：YAML frontmatter（~100词）- 始终在上下文
- Level 2：SKILL.md（<500行）- 触发时加载
- Level 3：捆绑资源（scripts/references）- 按需加载

**好处**：
- 减少token消耗
- 提高响应速度
- 支持大型参考文档

### 4.4 并行执行

**目的**：提高效率

**实现**：
- 使用`ProcessPoolExecutor`并行运行查询
- 同时启动with-skill和baseline运行
- 所有运行大约同时完成

**好处**：
- 节省总评估时间
- 加速迭代循环
- 提高资源利用率

### 4.5 实时反馈

**目的**：改善用户体验

**实现**：
- HTML报告自动刷新（`auto_refresh=True`）
- 反馈自动保存（`feedback.json`）
- 历史对比（显示上一次迭代）

**好处**：
- 用户可以实时查看进度
- 无需手动复制反馈
- 方便迭代间对比

---

## 5. 最佳实践

### 5.1 技能编写

1. **描述要"pushy"**：
   - 不要等待用户明确请求
   - 包含相关触发关键词
   - 例如："用于仪表板、数据可视化、内部指标"

2. **使用命令式指令**：
   - "做X，然后做Y"
   - 而非"必须做X"

3. **解释"为什么"**：
   - LLM有良好的心智理论
   - 给出推理让模型理解

4. **保持简洁**：
   - SKILL.md理想<500行
   - 超出则分层引用

5. **包含具体示例**：
   - 展示输入/输出格式
   - 提供实际用例

### 5.2 测试用例设计

1. **覆盖关键场景**：
   - 正常情况
   - 边缘情况
   - 错误处理

2. **可验证的期望**：
   - 客观可检查
   - 有明确证据
   - 避免主观判断

3. **多样化触发条件**：
   - 包含应该触发和不应该触发的查询
   - 测试技能的边界

### 5.3 评估流程

1. **始终并行运行**：
   - 同时启动with-skill和baseline
   - 节省时间

2. **立即捕获时序数据**：
   - 从任务通知中提取
   - 保存到`timing.json`

3. **运行时起草断言**：
   - 不等待所有运行完成
   - 利用时间生产力

4. **使用查看器进行人工审查**：
   - 提供交互式界面
   - 收集结构化反馈

### 5.4 改进策略

1. **泛化而非过度拟合**：
   - 识别根本问题
   - 避免针对特定示例的修补

2. **识别可复用模式**：
   - 查看所有测试用例的脚本
   - 打包重复逻辑到`scripts/`

3. **保持提示精简**：
   - 移除无生产力的步骤
   - 阅读执行脚本

---

## 6. 实际应用示例

### 6.1 创建新技能

```bash
# 1. 创建技能目录
mkdir skills/my-new-skill
cd skills/my-new-skill

# 2. 编写SKILL.md
cat > SKILL.md << 'EOF'
---
name: my-new-skill
description: Automatically generate React components with TypeScript and Tailwind CSS. Use this skill whenever user mentions React, components, UI development, or wants to create frontend interfaces.
---

# My New Skill

## When to Use This Skill

Use this skill when you need to create React components with TypeScript and Tailwind CSS styling.

## Workflow

1. Understand the component requirements
2. Generate TypeScript code with proper types
3. Apply Tailwind CSS classes
4. Ensure responsive design
5. Add accessibility attributes

## Example

Input: Create a button component
Output:
```tsx
import React from 'react';

interface ButtonProps {
  label: string;
  onClick: () => void;
  variant?: 'primary' | 'secondary';
}

export const Button: React.FC<ButtonProps> = ({
  label,
  onClick,
  variant = 'primary'
}) => {
  const baseClasses = 'px-4 py-2 rounded font-medium';
  const variantClasses = variant === 'primary'
    ? 'bg-blue-500 hover:bg-blue-600 text-white'
    : 'bg-gray-200 hover:bg-gray-300 text-gray-800';

  return (
    <button
      onClick={onClick}
      className={`${baseClasses} ${variantClasses}`}
    >
      {label}
    </button>
  );
};
```

## Best Practices

- Use TypeScript interfaces for props
- Follow Tailwind naming conventions
- Ensure keyboard accessibility
- Add proper error handling
EOF

# 3. 创建测试用例
mkdir evals
cat > evals/evals.json << 'EOF'
{
  "skill_name": "my-new-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "Create a primary button component with a click handler",
      "expected_output": "A TypeScript React component with Tailwind CSS classes",
      "files": []
    },
    {
      "id": 2,
      "prompt": "Create a secondary button component",
      "expected_output": "A TypeScript React component with gray styling",
      "files": []
    }
  ]
}
EOF

# 4. 运行评估
cd ../skill-creator
python -m scripts.run_eval \
  --eval-set ../my-new-skill/evals/evals.json \
  --skill-path ../my-new-skill \
  --num-workers 10 \
  --runs-per-query 3
```

### 6.2 迭代改进

```bash
# 1. 启动迭代循环
python -m scripts.run_loop \
  --eval-set ../my-new-skill/evals/evals.json \
  --skill-path ../my-new-skill \
  --max-iterations 5 \
  --holdout 0.4 \
  --model claude-sonnet-4-20250514

# 2. 查看实时报告
# 浏览器会自动打开 report.html
# 审查结果并提供反馈

# 3. 循环会自动：
# - 基于训练结果改进描述
# - 重新运行测试
# - 生成新报告
# - 直到全部通过或达到最大迭代
```

### 6.3 打包分发

```bash
# 1. 打包技能
python -m scripts.package_skill ../my-new-skill ./dist

# 2. 验证.skill文件
python -m scripts.quick_validate ./dist/my-new-skill.skill

# 3. 分发给用户
# 用户可以安装 .skill 文件到他们的 Claude Code
```

---

## 7. 高级特性

### 7.1 实时报告

使用`--report auto`参数启用实时HTML报告：

```bash
python -m scripts.run_loop \
  --report auto \
  --eval-set evals/evals.json \
  --skill-path my-skill
```

报告特性：
- 自动刷新（每5秒）
- 显示当前迭代和历史
- 实时更新最佳分数
- 支持下载反馈

### 7.2 静态报告

对于无显示环境，使用`--static`参数：

```bash
python -m scripts.run_loop \
  --report static \
  --eval-set evals/evals.json \
  --skill-path my-skill
```

反馈收集：
- 用户点击"Submit All Reviews"
- 下载`feedback.json`
- 手动复制到工作空间

### 7.3 自定义工作区

使用`--results-dir`参数指定输出位置：

```bash
python -m scripts.run_loop \
  --results-dir ./my-results \
  --eval-set evals/evals.json \
  --skill-path my-skill
```

输出结构：
```
my-results/
├── results.json          # 完整的JSON输出
├── report.html          # 最终HTML报告
├── logs/               # 详细日志
└── iteration-1/        # 每次迭代
    ├── eval-0/
    │   ├── with_skill/
    │   │   ├── outputs/
    │   │   ├── grading.json
    │   │   ├── metrics.json
    │   │   └── timing.json
    │   └── without_skill/
    │       └── outputs/
    └── benchmark.json
```

---

## 8. 故障排查

### 8.1 技能不触发

**症状**：技能描述匹配但Claude不加载

**可能原因**：
- 描述不够"pushy"
- 缺少相关关键词
- 描述过于抽象

**解决方案**：
- 增强描述中的触发关键词
- 添加具体使用场景
- 使用"whenever user mentions X"模式

### 8.2 评估失败

**症状**：所有测试用例失败

**可能原因**：
- 测试用例不切实际
- 期望过于严格
- 技能指令不清晰

**解决方案**：
- 审查测试用例是否合理
- 放宽期望标准
- 改进技能指令

### 8.3 高变异

**症状**：某些测试用例结果差异很大

**可能原因**：
- 测试用例模糊
- 技能指令有歧义
- 模型随机性

**解决方案**：
- 重写测试用例使其更具体
- 增加运行次数（`--runs-per-query`）
- 使用更稳定的模型

### 8.4 查看器无法启动

**症状**：`webbrowser.open()`失败

**可能原因**：
- 无显示环境
- 缺少webbrowser工具
- 端口被占用

**解决方案**：
- 使用`--static`模式生成静态HTML
- 手动在浏览器中打开
- 检查环境变量

---

## 9. 总结

Skill-Creator 是一个设计精良、功能完整的技能开发元系统。它通过以下核心原则实现了技能开发的系统化：

1. **数据驱动**：所有决策基于量化评估数据
2. **客观评估**：盲评机制消除偏见
3. **迭代优化**：训练/测试分离防止过拟合
4. **并行高效**：并行执行节省时间
5. **用户友好**：实时报告和交互式查看器
6. **可扩展性**：模块化设计支持自定义扩展

通过使用 Skill-Creator，开发者可以：
- 快速创建新技能
- 系统化测试和评估
- 数据驱动的持续改进
- 打包和分发技能
- 构建高质量的智能体技能生态系统

这个系统不仅是一个工具集，更是一种**技能工程的方法论**，为构建可靠、可维护、高性能的智能体技能提供了完整的框架和最佳实践。
