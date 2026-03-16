# 1. 什么是 Skill？
*   **核心定义**：Skill 是一个**上下文压缩包**。它不是简单的 Prompt，而是一套包含元数据（YAML）、核心指令（Markdown）、辅助脚本（Scripts）和参考文档（References）的完整文件系统。**简单来讲，skill就是一个文件夹。**
*   **工作机制**：
    *   当用户发起对话时，Claude 会扫描所有已安装的 Skill。
    *   通过比对用户输入与 Skill 的 `description`，动态决定是否将该 Skill 的内容注入当前对话的 Context Window。
*   **与普通 Prompt 的区别**：
    *   *Prompt*：一次性，需每次复制粘贴。
    *   *Skill*：持久化，自动触发，支持多文件引用，可跨会话记忆。

# 2. 核心设计原则
*   **渐进式披露 (Progressive Disclosure) 详解**：
    *   **Level 1 (YAML)** ：这是“钩子”。如果 YAML 中的 `description` 没匹配到用户意图，后续几 KB 的内容根本不会加载。**关键点**：用最少 Token 换取最高命中率。
    *   **Level 2 (SKILL.md)** ：这是“大脑”。只有触发后才加载。必须结构清晰，逻辑严密。
    *   **Level 3 (外部文件)** ：这是“图书馆”。当任务需要大量背景知识（如品牌规范、API 文档）时，在 `SKILL.md` 中写“请参考 `references/brand-guide.md`”，Claude 会在需要时主动读取。
*   **可组合性实战**：
你可以同时激活 `react-expert` 和 `accessibility-audit` 两个 Skill。前者负责写代码，后者负责检查无障碍标准。它们互不干扰，协同工作。

# 3. 进阶概念：Skill + MCP
*   **场景模拟**：
    *   *没有 Skill*：你连接了 Slack MCP。你对 Claude 说“查一下昨天的消息”，它可能不知道查哪个频道、怎么格式化、要不要总结。
    *   *有了 Skill*：你加载了 `slack-daily-standup` Skill。你说“开始站会”，Skill 立即指示 Claude：1. 调用 MCP 获取 `#general` 昨天 9am-6pm 的消息；2. 按“完成/阻碍/计划”格式总结；3. 输出 Markdown 表格。
*   **结论**：MCP 提供**能力 (Capability)**，Skill 提供**策略 (Strategy)**。

---

# 4. skill设计技巧
**目标**：从零开始构建一个符合规范、高可用性的 Skill 文件夹。

## 4.1. 用例定义工作坊
*   **步骤 1：痛点挖掘**
    *   列出你每周重复做 3 次以上的任务。
    *   *例子*：每次新建 React 项目都要配置 ESLint, Prettier, Tailwind。
*   **步骤 2：成功标准定义**
    *   *输入*：“帮我建个新后台项目”。
    *   *理想输出*：自动生成文件结构，安装依赖，配置好所有 lint 规则，并运行 `npm run dev`。
*   **步骤 3：边界界定**
明确 Skill **不做什么**（例如：不负责部署到服务器，只负责本地初始化）。

## 4.2. 技术规范与文件结构
*   **文件夹命名严格规范**：
    *   ✅ `react-project-starter`
    *   ❌ `React Project Starter` (有空格/大写)
    *   ❌ `react_project_starter` (有下划线)
    *   ❌ `claude-react-helper` (包含禁止词 "claude")
*   **文件树示例**：
    ```text
    my-skill-folder/
    ├── SKILL.md                # 必填：主入口
    ├── scripts/                # 可选：自动化脚本
    │   └── validate-config.py
    ├── references/             # 可选：长文档
    │   ├── api-docs.md
    │   └── style-guide.pdf
    └── assets/                 # 可选：图片/模板
        └── logo-template.svg
    ```
    *注意：根目录下不要放 `README.md`，上传时会报错。README 应放在 GitHub 仓库层级，而非 Skill 文件夹内。*

## 4.3 YAML Frontmatter 编写（核心中的核心）
*   **语法结构**：
    ```yaml
    ---
    name: react-project-starter
    description: >
      帮助用户快速初始化 React + TypeScript + Tailwind 项目。
      当用户提到 "新建 React 项目", "setup react", "init frontend", 
      或者 "创建一个带有 Tailwind 的新应用" 时使用此技能。
      不适用于修改现有项目或调试错误。
    ---
    ```
*   **编写技巧**：
    *   **关键词覆盖**：列出用户可能用的同义词（setup, init, create, new）。
    *   **否定约束**：明确指出“不适用于...”以减少误触。
    *   **自然语言**：Description 是写给 AI 看的，要像自然对话描述场景，而不是写代码注释。
*   **安全红线**：
    *   绝对不要在 YAML 中使用 `<` 或 `>` (除了 YAML 的多行符号 `>`)，避免被误解析为 HTML 标签。
    *   Name 必须全小写，连字符分隔。

## 4.4. 指令编写最佳实践 (SKILL.md 内部)
*   **推荐结构模板**：
    1.  **Role Definition**: "你是一个资深的前端架构师..."
    2.  **Trigger Confirmation**: "当用户请求初始化项目时，首先确认技术栈偏好..."
    3.  **Step-by-Step Workflow**:
        *   Step 1: 检查环境 (Node 版本)。
        *   Step 2: 执行命令 (`npx create-react-app...`)。
        *   Step 3: 配置文件替换 (从 `assets` 读取模板)。
    4.  **Output Format**: "最终输出一个文件树结构和下一步指导。"
    5.  **References Usage**: "详细的设计规范请参阅 `references/style-guide.md`。"
    6.  **Error Handling**: "如果 `npm install` 失败，尝试清理缓存后重试。"
*   **Token 优化技巧**：
对于超过 2000 字的背景资料，**务必**放入 `references/` 文件夹，并在主文件中用一句话引用。不要让主文件变得臃肿。

---

# 5. 测试与迭代
**目标**：建立科学的测试流程，量化 Skill 的表现。

## 5.1. 测试策略实施
*   **手动测试清单**：
    *   **正例测试**：使用 5 种不同的说法触发 Skill（如："建个项目"、"Setup new app"、"我想做个 React 网站"）。
    *   **反例测试**：询问无关话题（如"今天天气如何"、"解释量子力学"），确保 Skill **不**加载。
    *   **边缘测试**：模糊指令（如"帮我弄个前端"），看 Skill 是否能通过追问澄清需求。
*   **Claude Code 自动化测试**：
编写一个简单的 Shell 脚本，循环发送预设 Prompt 给 CLI 版本的 Claude，检查输出是否包含预期的关键字（如 "Initializing project..."）。

## 5.2. 三大测试维度详解
1.  **触发率 (Trigger Rate)**：
    *   *指标*：10 次相关请求中，有几次自动加载了 Skill？
    *   *优化*：如果低于 80%，检查 `description` 是否漏掉了常用口语表达。
2.  **准确率 (Accuracy)**：
    *   *指标*：生成的代码/内容是否直接可用？是否需要人工大幅修改？
    *   *优化*：如果经常出错，检查 `SKILL.md` 中的步骤是否缺失，或是否需要引入 `scripts/` 进行硬性校验。
3.  **效率提升 (Efficiency)**：
    *   *指标*：对比有无 Skill 时的对话轮数。
    *   *目标*：将原本需要 5 轮对话的任务压缩到 1-2 轮。

## 5.3. 迭代优化信号与行动
*   **信号 A：用户说“你没听懂我的意思”**
    *   *行动*：在 `SKILL.md` 开头增加“澄清问题”的步骤，强制 AI 先确认需求再执行。
*   **信号 B：Skill 在奇怪的时候跳出来**
    *   *行动*：在 YAML `description` 中加入更强的否定句，如 "Never use this for debugging existing code."
*   **信号 C：执行到一半卡住**
    *   *行动*：检查是否引用了不存在的文件路径，或者脚本权限问题。

---

# 6. 分发与共享
**目标**：让你的 Skill 被更多人使用，建立影响力。

## 6.1. 分发渠道全流程
*   **个人/小团队 (ZIP 法)** ：
    1.  在终端进入 Skill 文件夹上级目录。
    2.  运行 `zip -r my-skill.zip my-skill-folder`。
    3.  打开 Claude.ai -> Settings -> Skills -> Upload -> 选择 ZIP。
*   **企业级 (Admin Console)** ：
    *   管理员登录 Anthropic 控制台，批量上传 ZIP 包，设置默认对全员可见。
    *   优势：版本统一管理，员工无需手动安装。
*   **开发者 (API)**：
使用 `POST /v1/skills` 接口，将 Skill 作为 JSON 对象或文件流推送，集成到自己的 SaaS 产品中。

## 6.2. 推广与文档化 (GitHub 策略)
*   **仓库结构**：
    ```text
    my-skill-repo/
    ├── README.md          # 这里是给人看的：安装教程、功能演示、截图
    ├── skills/            # 存放实际的 Skill 文件夹
    │   └── react-starter/
    │       ├── SKILL.md
    │       └── ...
    └── examples/          # 使用案例截图或录屏
    ```
*   **文案技巧**：
    *   *标题*：不要写 "React Starter Skill"，要写 "30 秒启动生产级 React 项目 (零配置)"。
    *   *GIF 演示*：录制一个从输入命令到项目跑起来的 15 秒 GIF，胜过千言万语。
*   **MCP 生态联动**：
    *   如果你开发了一个 MCP Server，务必在它的文档首页放上对应的 Skill 下载链接。这是“工具 + 用法”的完美闭环。

---

# 7. 高级模式
**目标**：解决疑难杂症，构建企业级复杂工作流。

1.  **顺序工作流编排 (Chain of Thought Enforcement)**
    *   *场景*：合规审查。
    *   *实现*：在 `SKILL.md` 中强制要求：Step 1 提取实体 -> Step 2 对照法规库 -> Step 3 生成风险报告。禁止跳过步骤。
2.  **多 MCP 协同 (Orchestration)**
    *   *场景*：全栈部署。
    *   *实现*：Skill 指挥 Claude 依次调用：GitHub MCP (建库) -> Vercel MCP (部署) -> Slack MCP (通知团队)。Skill 负责传递上一步的输出作为下一步的输入。
3.  **迭代优化循环 (Self-Correction)**
    *   *场景*：生成单元测试。
    *   *实现*：指令中包含："生成测试代码 -> 运行测试 -> 如果失败，分析错误日志 -> 修正代码 -> 再次运行"。
4.  **上下文感知路由 (Context Routing)**
    *   *场景*：智能文件存储。
    *   *实现*：Skill 判断：如果是小文件 (<1MB)，存本地；如果是大文件或需协作，自动调用 Google Drive MCP 上传并返回链接。
5.  **领域专家嵌入 (Domain Expertise)**
    *   *场景*：医疗/法律助手。
    *   *实现*：在 `references/` 中放入最新的法律法规 PDF。Skill 指令要求："所有回答必须严格依据 `references/law-2024.pdf`，并标注页码。"

# 8. 常见故障排查手册
| 问题现象 | 可能原因 | 解决方案 |
| :--- | :--- | :--- |
| **上传失败** | 文件夹名有大写/空格 | 重命名为全小写 kebab-case (如 `my-skill`) |
| **上传失败** | 缺少 `SKILL.md` 或拼写错误 | 确保文件名完全匹配 `SKILL.md` (大小写敏感) |
| **上传失败** | YAML 格式错误 | 检查 `---` 是否成对，缩进是否正确 |
| **不触发** | Description 太短或太抽象 | 增加具体的用户口语短语 ("帮我...", "我想...") |
| **误触发** | Description 太宽泛 | 增加 "Only use when..." 和 "Do not use for..." 限制 |
| **指令不执行** | 指令太长被截断 | 将长文档移至 `references/`，主文件只做索引 |
| **MCP 报错** | 权限不足或未配置 | 单独测试 MCP 连接，检查环境变量/API Key |
| **逻辑混乱** | 步骤描述模糊 | 使用编号列表 (1. 2. 3.)，明确每一步的输入输出 |

---