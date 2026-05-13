# 附录 A · 术语表

---

| 术语 | 英文 | 定义 |
|------|------|------|
| **智能体驱动开发** | Agentic Development | 人类编排 Agent、Agent 编写代码的开发范式 |
| **编排器—工作者** | Orchestrator-Worker | 一个编排 Agent + 多个工作 Agent 的架构模式 |
| **规划—执行—裁决** | Planner-Worker-Judge | Cursor 演化的三层架构：Planner 生成任务，Worker 执行，Judge 裁决 |
| **Gas Town** | Gas Town | Steve Yegge 的多 Agent 协调系统，包含 Mayor/Polecats/Refinery/Deacon/Overseer |
| **上下文工程** | Context Engineering | 设计、构建和管理注入到 AI Agent 中的信息环境的工程实践 |
| **50 First Dates 问题** | 50 First Dates Problem | Agent 在每次新会话中丢失所有记忆的问题，比喻自同名电影 |
| **代理记忆系统** | Agent Memory System | 为 Agent 提供跨会话持久记忆的基础设施 |
| **语义检索** | Semantic Retrieval | 基于向量嵌入的上下文检索，找到与当前任务最相关的信息 |
| **上下文窗口** | Context Window | LLM 一次能处理的 token 上限 |
| **分层注入** | Tiered Injection | 将上下文分为多层（全局/按需/深度），按需注入给 Agent |
| **验证循环** | Verification Loop | Agent 自检 → 交叉验证 → 人类裁决的三层质量门 |
| **升级路由** | Upgrade Routing | 当 Agent 遇到无法解决的问题时的升级路径设计 |
| **意图定义** | Intent Definition | 将模糊需求翻译为 Agent 可执行的 spec 的能力 |
| **委托鸿沟** | Delegation Gap | 人类愿意委托给 Agent 的比例 vs Agent 实际能处理的比例之间的差距 |
| **信任校准** | Trust Calibration | 人类对 Agent 能力的判断与 Agent 实际能力之间的一致性 |
| **模型上下文协议** | MCP (Model Context Protocol) | Agent 与外部工具交互的标准化协议 |
| **ADR** | Architecture Decision Record | 架构决策记录，记录关键设计决策及其理由 |
| **Beads** | Beads | Steve Yegge 的 Git-based Agent 记忆和 issue 追踪系统 |
