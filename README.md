# Agent-Handbook
Agent学习笔记。

- pocketflow-handbook：使用Pocketflow的官方仓库及示例，构建基础的学习课程。基本上如果对pocketflow比较了解了，后续再去学习langchain或者langgraph等其它的框架就会更简单。

- pocketflow-adp：基于google的书籍《agentic-design-patterns》，使用pocketflow实现书中不同章节的代码。
  - [Chapter 1: 提示词链](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter1_提示词链) - 学习如何将复杂任务分解为多个顺序执行的子任务，每个子任务通过专门的提示词处理，前一个任务的输出作为后一个任务的输入。实现技术规格提取、JSON转换和格式验证等功能。
  - [Chapter 2: 路由](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter2_路由) - 掌握路由模式，使Agent能够根据输入内容动态决定执行路径。包含基于LLM、嵌入相似度和混合路由三种策略，实现预订处理、信息查询等功能。
  - [Chapter 3: 并行化](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter3_并行化) - 学习如何通过并发执行独立任务来提高效率。使用AsyncParallelBatchNode实现并行处理，适用于多个LLM调用或外部API请求的场景。
  - [Chapter 4: 反思](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter4_反思) - 实现反思模式，让AI系统能够自我评估和改进其输出。通过生成、评估和优化的迭代过程逐步提升最终结果质量。
  - [Chapter 5: 工具调用](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter5_工具调用) - 学习工具使用模式，允许Agent调用外部工具来获取信息或执行操作。包含信息搜索、股票价格查询、财务分析等实际应用场景。
  - [Chapter 6: 规划](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter6_规划) - 实现规划模式，将复杂任务分解为多个步骤并按顺序执行。包含规划节点、执行节点和响应生成节点，支持动态规划和工具集成。
  - [Chapter 7: 多智能体协作](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter7_多智能体协作) - 学习多智能体协作模式，通过设计多个专门智能体的协作集合解决复杂、多领域任务。包含顺序协作、并行协作、层级协作和协作决策四种模式。
  - [Chapter 8: 记忆管理](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter8_记忆管理) - 实现Agent的记忆管理功能，包括短期记忆（上下文记忆）和长期记忆（持久记忆）。使用SessionService和MemoryService管理会话和记忆存储。
  - [Chapter 9: 学习和适应](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter9_学习和适应) - 学习多种学习和适应模式，包括强化学习、监督学习、自我进化和自适应智能体。使用PocketFlow框架实现模块化的学习节点。
  - [Chapter 10: MCP](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter10_mcp) - 实现模型上下文协议(MCP)，允许AI模型与外部工具和服务进行交互。包含文件系统交互、Web搜索和文件内容分析功能。
  - [Chapter 11: 目标设定和监控](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter11_目标设定和监控) - 实现目标设定和监控模式，通过迭代式代码生成、评估和改进来满足用户定义的目标。包含目标设定、代码生成、代码评估和代码改进节点。
  - [Chapter 12: 异常处理和恢复](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter12_异常处理和恢复) - 学习异常处理和恢复模式，构建能够优雅处理错误并从失败中恢复的智能系统。包含主要处理器、回退处理器和响应代理三个组件。
  - [Chapter 13: 人机协同](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter13_人机协同) - 实现人机协同模式，将人类智能与人工智能相结合。系统在处理复杂任务时自动决策，并在需要时寻求人类干预。
  - [Chapter 14: RAG](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter14_rag) - 实现检索增强生成(RAG)系统，结合文档检索和LLM生成能力。支持基于Web搜索和向量相似度的文档检索，包含基础RAG和智能RAG两种流程。
  - [Chapter 15: Agent间通信](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter15_agent_communication) - 学习Agent间通信(A2A)协议，使多个Agent能够相互发现、通信和协作。包含AgentCard、A2A通信节点、Agent注册表等核心组件。
  - [Chapter 16: 资源感知优化](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter16_资源感知优化) - 实现资源感知优化系统，根据任务复杂性和资源约束动态选择合适的模型和策略。包含任务分类、资源监控和优化建议功能。
  - [Chapter 17: 推理技术](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter17_推理技术) - 学习多种高级推理技术，包括思维链(CoT)、自我纠正、ReAct、辩论链(CoD)和Deep Research。每种技术都有其适用的场景和优势。
  - [Chapter 18: 防护栏安全模式](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter18_防护栏安全模式) - 实现AI Agent的防护栏和安全模式，确保AI系统安全、可靠且符合道德规范地运行。包含输入验证、输出过滤、工具调用防护栏和错误处理等功能。
  - [Chapter 19: 评估与监控](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter19_评估与监控) - 评估与监控模块（代码存在但README文件缺失）
  - [Chapter 20: 优先级排序](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter20_优先级排序) - 实现任务优先级排序系统，根据任务的重要性和紧急性自动分配优先级，并将任务分配给合适的工作人员。支持自然语言命令和多种查询方式。
  - [Chapter 21: 探索和发现](https://github.com/taishan1994/Agent-Handbook/tree/main/pocketflow-adp/adp/chapter21_探索和发现) - 探索和发现模式，通过Agent实验室进行实验和研究，生成优化建议、模型架构、数据解决方案和文献综述。

- pocketflow-leetcode：构建一个可以自动写leetcode和测试i的智能体。

  - [构建一个自动编写leecode的智能体](https://github.com/taishan1994/Agent-Handbook/blob/main/pocketflow-leetcode/README.MD)

- anthropic-article：学习anthropic发布的有关智能体的文章。

- pocketflow-law-tag-agent：一个基础的RAG框架，后续优化方法可以基于这个框架进行尝试。

  - [构建一个能够进行检索增强生成的法律问答智能体](https://github.com/taishan1994/Agent-Handbook/blob/main/pocketflow-law-rag/README.MD)

- mini-agents：对Minimax的Mini-Agents进行拆解，包括工具的使用、mcp的使用、skills的使用以及构建一个可以执行工具、mcp和skills的agent。

  - [构建一个LLM客户端](https://github.com/taishan1994/Agent-Handbook/blob/main/mini-agents/examples/test_llm_client.py)
  - [构建一个可以使用工具的LLM客户端](https://github.com/taishan1994/Agent-Handbook/blob/main/mini-agents/examples/test_llm_client_with_tool.py)
  - [构建一个可以使用mcp工具的LLM客户端](https://github.com/taishan1994/Agent-Handbook/blob/main/mini-agents/examples/test_llm_client_with_mcp_tools.py)
  - [构建一个可以使用skills工具的LLM客户端](https://github.com/taishan1994/Agent-Handbook/blob/main/mini-agents/examples/test_llm_skill_code_execution.py)

- langchain_v1+：主要是对langchain1.+的学习。

  - [如何自定义中间件](https://github.com/taishan1994/Agent-Handbook/blob/main/langchain_v1%2B/examples/%E5%A6%82%E4%BD%95%E8%87%AA%E5%AE%9A%E4%B9%89%E4%B8%AD%E9%97%B4%E4%BB%B6.md)
  - [使用langchain1.x+vllm+Qwen3-30B-A3B结合MCP构建一个自动搜索回答的智能体](https://github.com/taishan1994/Agent-Handbook/blob/main/langchain_v1%2B/examples/deepagents_with_mcp.md)
  - [使用langchain1.x+Qwen3-30B-A3B构建一个自动写SQL的智能体](https://github.com/taishan1994/Agent-Handbook/tree/main/langchain_v1%2B/examples/codes/text2sql_agent/) 

- openclaw：针对openclaw的架构拆解
  - [总体架构分析](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-总体架构分析.md) - 深入分析OpenClaw的整体架构设计，包括Gateway网关层、Channels渠道层、Plugins插件层、Browser浏览器层、Media媒体层等核心模块的详细说明。
  - [安全管理机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-安全管理机制.md) - 全面介绍OpenClaw的安全管理机制，包括安全审计工具、认证机制、访问控制、沙箱隔离、工具策略、环境变量安全等多层次安全防护体系。
  - [智能体交互机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-智能体交互机制.md) - 详细讲解OpenClaw的智能体交互系统，包括子智能体生成、智能体间消息传递、通告机制、嵌套协作模式和线程绑定会话等功能。
  - [技能加载与使用机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-技能加载与使用机制.md) - 介绍OpenClaw的技能系统，包括技能文件结构、元数据解析、技能发现与加载、技能使用机制和配置管理等核心功能。
  - [智能体持续运行机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-智能体持续运行机制.md) - 阐述OpenClaw确保智能体持续运行的各种机制，包括心跳检测、自动回复、后台进程、消息监听、定时任务、连接保持和重连等。
  - [使用MCP指南](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-使用MCP指南.md) - 完整的MCP（Model Context Protocol）使用指南，涵盖MCP服务器配置、会话管理、工具调用、权限管理、调试和性能优化等内容。
  - [心跳机制详解](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-心跳机制.md) - 深入解析OpenClaw的心跳机制，包括心跳配置、HEARTBEAT.md检查清单、响应约定、可见性控制、活动时段控制和成本优化等核心功能。
  - [反思和规划机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-反思和规划机制.md) - 介绍OpenClaw的多层次反思和规划机制，包括Thinking/Reasoning推理系统、Heartbeat定期检查、Memory记忆管理、Compaction上下文压缩和Cron定时任务等组件。
  - [系统提示词加载机制](https://github.com/taishan1994/Agent-Handbook/blob/main/openclaw/openclaw-系统提示词加载.md) - 详细说明OpenClaw的System Prompt加载机制，包括提示模式、加载流程、Bootstrap文件机制、插件扩展、技能加载和记忆召回等核心内容。

- skills：skills基础学习与前沿研究
  - [技能基础介绍和使用](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/skills基本介绍和使用.md) - 全面介绍Skills系统的核心概念、设计原则、文件结构、编写技巧和最佳实践，帮助理解如何构建和使用可复用的Agent技能。
  - [SoK：Agentic Skills——超越工具调用，重新定义LLM智能体的能力范式](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/agentic_skills.md) - 首次以智能体技能为核心视角，系统性梳理LLM智能体的能力封装、生命周期、设计范式与安全治理，为智能体从"临时规划"走向"持久技能化"提供完整理论框架。
  - [Memento‑Skills：让AI智能体自己设计自己，无需微调也能持续进化](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/memento_skills.md) - 提出基于记忆强化学习的通用智能体系统，通过"读写反思学习"闭环，让智能体以可执行技能为外部记忆，自主设计、优化、迭代专属任务智能体，全程不更新底层LLM参数实现持续性能跃升。
  - [SkillsBench：首次系统性评测Agent技能，揭开大模型外挂的真实效用](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/skillbench.md) - 打造行业首个以技能为核心评估对象的基准测试平台，覆盖11大领域、84项真实任务，完成超7300次实验，量化揭示Agent技能的真实价值与边界。
  - [KernelSkill：GPU内核优化的多智能体框架](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/kernel_skill.md) - 介绍基于双层记忆架构的多智能体框架，通过协调具备长期记忆（可复用专家技能）和短期记忆（防止重复回溯）的智能体，实现高效的GPU内核优化。
  - [EvoSkill：自动化技能发现框架](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/evol_skill.md) - 提出一种自我进化框架，通过迭代式的失败分析自动发现并优化智能体的技能。该框架在更高的"技能"抽象层级上进行操作，生成的技能具有结构化、可复用和可迁移的特点，显著提升多智能体系统能力。
  - [AutoSkill：经验驱动的终身学习框架](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/auto_skill.md) - 介绍一种经验驱动的终身学习框架，使LLM代理能够从对话和交互痕迹中自动提取技能、持续维护技能库、动态重用技能，在不重新训练基础模型的情况下实现个性化能力的积累。
  - [SCALAR：符号规划与强化学习的技能学习框架](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/scalar.md) - 提出一种创新框架，通过构建双向反馈闭环，将LLM的符号规划能力与强化学习的低层执行能力紧密结合，利用学到的技能库来实现复杂长程任务的自主学习和组合。
  - [XSKILL：多模态智能体的持续学习框架](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/x_skill.md) - 介绍一种双流框架，通过从过去的执行轨迹中持续学习两种互补的可重用知识——经验和技能，使多模态智能体无需更新参数即可不断提升性能，解决工具使用效率低和编排灵活性差的问题。
  - [Skill-Creator：构建智能体技能的元技能系统](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/skill-creator-architecture.md) - 深度解析Skill-Creator的完整架构，包括三大核心智能体（Grader、Comparator、Analyzer）、工具脚本链、完整工作流程和关键设计模式，提供从技能创建、测试评估到持续优化的系统化方法论。
  - [SkillRouter：大规模LLM智能体技能路由的新范式](https://github.com/taishan1994/Agent-Handbook/blob/main/skills/skill_router.md) - 提出两阶段"检索-重排序"流水线，通过实证研究揭示技能实现代码(Body)才是决定性信号，在8万技能池中实现74.0%的Top-1路由准确率，为大规模技能路由提供高效、紧凑的解决方案。

- agent-papers：智能体相关论文深度解析
  - [ProRL Agent：Rollout-as-a-Service for RL Training of Multi-Turn LLM Agents](https://github.com/taishan1994/Agent-Handbook/blob/main/agent-papers/ProRL-Agents.md) - 提出一种名为ProRL Agent的新型基础设施，通过"轨迹生成即服务"(RaaS)的设计理念，将多轮LLM智能体的轨迹生成从RL训练器中完全解耦，解决I/O密集型轨迹生成与GPU密集型策略训练之间的系统需求冲突，显著提升训练效率、系统可维护性和可移植性。
  - [自进化智能体综述：迈向ASI的关键一步](https://github.com/taishan1994/Agent-Handbook/blob/main/agent-papers/Self-Evolving-Agents.md) - 该领域首篇系统性综述，围绕"进化什么、何时进化、如何进化、在哪里进化"四个维度构建自进化智能体的分类体系，为从静态模型到动态进化的智能体研究提供统一理论框架和路线图，最终指向人工超级智能(ASI)的实现。
  - [Claude Code 源码深度架构分析](https://github.com/taishan1994/Agent-Handbook/blob/main/agent-papers/Claude%20Code%20%E6%BA%90%E7%A0%81%E6%B7%B1%E5%BA%A6%E6%9E%B6%E6%9E%84%E5%88%86%E6%9E%90.pdf)
  
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
