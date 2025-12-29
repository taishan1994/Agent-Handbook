# Agent-Handbook
Agent学习笔记。

- pocketflow-handbook：使用Pocketflow的官方仓库及示例，构建基础的学习课程。基本上如果对pocketflow比较了解了，后续再去学习langchain或者langgraph等其它的框架就会更简单。
- pocketflow-adp：基于google的书籍《agentic-design-patterns》，使用pocketflow实现书中不同章节的代码。
- pocketflow-leetcode：构建一个可以自动写leetcode和测试i的智能体。
- anthropic-article：学习anthropic发布的有关智能体的文章。
- pocketflow-law-tag-agent：一个基础的RAG框架，后续优化方法可以基于这个框架进行尝试。

# 配套文章

- [一份全面的Agent学习资料，看完了我不信你还不会](https://mp.weixin.qq.com/s/acJA87ciZqxXh07y5cf8Bg)
- [从零开始构建一个会写leetcode的Agent](https://mp.weixin.qq.com/s/CONB6qRcgYD_RhXzMS_eqw)
- [终于弄懂了提示词，提示工程和上下文工程](https://mp.weixin.qq.com/s/iAR5EuMqYpMU-BRK3nNjqQ)
- [25种LLM部署框架你知道多少？](https://mp.weixin.qq.com/s/XEOFUt7wXZm7ZtDcVDls2A)
- [Agent评测之使用opencompass评测大模型的基础能力](https://mp.weixin.qq.com/s/I3s3Fei0wA-TsRnpSogDtQ)
- [Agent评测之使用大海捞针评估大模型的上下文长度](https://mp.weixin.qq.com/s/QSQDkLI0xECZeE0yHJiQjQ)
- [基于大语言模型的智能体优化综述](https://mp.weixin.qq.com/s/FZl2l47TQ98U53MLZA4z6Q)
- [基于大语言模型的智能体评估综述](https://mp.weixin.qq.com/s/YalQ1xrfpMRKPZUeFrvnag)
- [【search-o1】大模型的推理](https://mp.weixin.qq.com/s/ISE2k87aiBi4i67wXH1how)
- [【search-o1】利用RAG进行检索问答](https://mp.weixin.qq.com/s/Eucfjn99wDpcmFmACgywUQ)
- [【search-o1】利用Agent结合搜索引擎进行问答](https://mp.weixin.qq.com/s/MHc3BdigVvd-oW3Szm2zrQ?poc_token=HJWiz2ijBMxKCEMq2xkCyo8jRJap4chTd0k5vHct)
- [【search-o1】使用search-o1方法进行智能检索问答](https://mp.weixin.qq.com/s/Um6NKMtypvF2cq7-D_Ya1A)
- [mini-langchain-chatglm：五分钟实现基于知识的问答](https://mp.weixin.qq.com/s/8qUv2XIzeK36RO9QEUJA3A)

# Agent框架对比
**主流 AI Agent 框架优缺点对比（截至 2025 年 11 月）**

| 框架 | 优点 | 缺点 |
|------|------|------|
| **OpenAI Agents SDK** | - 轻量级、设计简洁<br>- 原语清晰（Agent 与 Handoff）<br>- 支持全面的跟踪功能<br>- 适合快速构建生产级多智能体系统<br>- 拥有活跃社区（GitHub 1.1万星） | - 对非 OpenAI 模型（如开源或竞品）支持有限<br>- 生态目前不如 LangChain 等成熟 |
| **AutoGen（Microsoft Research）** | - 开创了多智能体“群聊”模式<br>- 支持高度灵活的协作模式<br>- 适合研究与原型开发 | - 缺乏原生记忆支持<br>- 扩展性弱<br>- 企业级部署需额外集成<br>- 更适合小规模研究项目，不适合大规模生产 |
| **Microsoft Agent Framework (MAF)** | - 融合 AutoGen 与 Semantic Kernel 的长处<br>- 提供图式工作流、强类型接口<br>- 支持企业级功能（安全、可观测性）<br>- 支持 .NET 与 Python | - 相对较新，社区生态尚在建设中<br>- 学习曲线略陡 |
| **CrewAI** | - 完全从零构建、轻量快速<br>- 强调“角色-目标-任务”驱动的协作<br>- 可独立于 LangChain<br>- 适合构建结构化团队式智能体 | - 生态较新，工具链和可视化支持较少<br>- 不适合需要复杂流程编排的场景 |
| **Google ADK（Agent Development Kit）** | - 提供开发者 UI、CLI、调试工具链完整<br>- 支持 Google Agent Protocol<br>- 便于集成 Google 生态（如 Search、Gemini） | - 内置工具限制多（如每个 Agent 只能绑定一个内置工具）<br>- 深度绑定 Gemini，跨模型迁移困难 |
| **MetaGPT** | - 模拟软件公司工作流<br>- 擅长从单行需求生成完整项目代码<br>- 适合工程类多智能体协作 | - 依赖 asyncio<br>- 缺乏可视化构建器<br>- 对非技术用户不友好 |
| **Haystack Agents（deepset）** | - 围绕 RAG 构建<br>- 模块化强<br>- 适合企业级 NLP 应用（如智能搜索、文档处理） | - 通用智能体编排能力较弱<br>- 不如 AutoGen / CrewAI 等专为多智能体设计的框架灵活 |
| **Claude Agent SDK（Anthropic）** | - 专为 Claude 模型优化<br>- 支持 MCP 工具协议<br>- 适合构建生产级编码智能体 | - 仅支持 Claude 系列模型<br>- 目前仅提供 Python 版本<br>- 长上下文需手动压缩 |
| **Crawl4AI / Crawl4AI** | - 专为 LLM 优化的网页抓取框架<br>- 异步高性能<br>- 输出结构化 Markdown<br>- 适合构建 Web 数据摄入管道 | - 并非通用智能体框架<br>- 是特定于数据采集的工具，需与其他框架配合使用 |
| **LlamaIndex（Agents & LlamaAgents）** | - 在 RAG 场景下表现卓越<br>- 数据连接器丰富<br>- 文档和社区活跃 | - 聚焦数据检索而非通用智能体协作<br>- 扩展性和通用编排能力有限 |
| **Semantic Kernel – Agent Orchestration（Microsoft）** | - 多语言支持（.NET / Python / Java）<br>- 模型无关<br>- 适合企业级工作流编排<br>- 支持 Group Chat 等高级模式 | - 抽象层级高，初学者门槛略高<br>- 需结合其他组件构建完整智能体系统 |
| **PydanticAI** | - 强类型安全<br>- 与 Pydantic 深度集成<br>- 调试能力强（支持 Logfire）<br>- 适合构建可靠生产应用 | - 较新，生态和工具链尚不成熟<br>- 社区规模较小 |
| **Griptape** | - 模块化设计<br>- 支持记忆、工具、多智能体协作<br>- 适合构建 LLM 工作流与智能体应用 | - 文档和示例相对较少<br>- 社区活跃度不如头部框架 |
| **Flowise Agents** | - 低代码可视化编排<br>- 适合快速构建 LLM 工作流和简单智能体系统 | - 动态多智能体能力有限<br>- 不适合复杂协作场景<br>- 企业集成能力较弱 |
| **LangChain** | - 快速原型开发能力强<br>- 支持海量工具与模型集成（包括本地/私有模型）<br>- 成熟的 RAG 与 Agent 支持<br>- 拥有最广泛的社区与教程资源 | - 抽象层级高，学习曲线陡峭<br>- 调优与性能优化较复杂<br>- 在大型项目中带来治理和调试负担 |
| **LangGraph** | - 提供状态化、可持久记忆的多智能体工作流<br>- 基于图结构，支持循环、分支、暂停/恢复等高级控制流<br>- 与 LangChain 深度集成，适合构建复杂代理系统<br>- 支持节点级超时、重试等生产级特性 | - 需要熟悉图式编程范式<br>- 对简单任务而言可能过度设计<br>- 部分高级功能需依赖 LangSmith 等商业组件 |
| **DeepAgents** | - 基于 LangChain/LangGraph 构建的高级代理框架<br>- 内置规划、待办事项（TODOs）、文件系统支持<br>- 支持子代理（subagents）与中间件，实现职责隔离<br>- 支持真实 Web 搜索与上下文卸载 | - 相对新，生态和文档仍在完善<br>- 强依赖 LangChain 技术栈，学习成本叠加<br>- 更适合“深度推理”场景，不适合轻量级任务 |
| **PocketFlow** | - 极简设计（约 100 行核心代码）<br>- 无依赖、无厂商锁定<br>- 基于图结构，支持多智能体、RAG、任务分解等<br>- 非常适合教学、原型验证与 AI 编码代理辅助开发 | - 功能高度精简，缺少企业级特性（如可观测性、安全控制）<br>- 社区规模小，扩展能力有限<br>- 需自行实现高级功能（如记忆、评估） |
| **smolagents（Hugging Face）** | - 轻量级（核心代码约 1000 行）<br>- 首类支持“代码即动作”的 Code Agent<br>- 与 Hugging Face 生态无缝集成（模型、数据集、Space）<br>- 开发体验简洁，适合快速部署 | - 功能聚焦特定范式（代码生成型代理）<br>- 缺乏复杂的多智能体协调机制<br>- 企业级部署能力尚未成熟 |
| **HelloAgents** | - 专为教学与学习设计，代码透明、结构清晰<br>- 基于 OpenAI 原生 API 从零构建，深入讲解 Agent 核心原理<br>- 包含完整教程（《从零开始构建智能体》），适合入门者 | - 非生产级框架，功能有限<br>- 仅支持 OpenAI 模型，扩展性弱<br>- 社区主要用于教育，不适合工业部署 |

> **具体使用**：  
> - **企业级复杂系统**推荐：Microsoft Agent Framework、LangGraph、DeepAgents、Semantic Kernel。  
> - **研究与快速原型**推荐：AutoGen、CrewAI、LangChain、smolagents。  
> - **极简/教学用途**推荐：PocketFlow、HelloAgents。  
> - **特定能力突出**：Crawl4AI（数据抓取）、Claude SDK（编码代理）、Haystack（RAG 智能体）。  
> 实际选型应结合模型生态、团队技能栈、部署环境与可维护性综合评估。