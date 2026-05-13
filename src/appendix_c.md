# 附录 C · Agent 编排工具对比

---

## 主流工具矩阵 (2026 年 5 月)

| 工具 | 编排模式 | 多 Agent 支持 | Context Engineering | 开源 | 适用场景 |
|------|---------|:---:|:---:|:---:|------|
| **Claude Code** | Orchestrator-Worker | ✅ delegate_task | ❌ 手动 | ❌ | 中型项目、功能开发 |
| **OpenAI Codex** | Orchestrator-Worker + /goal | ✅ sub-agent | ❌ 手动 | ✅ | 中型项目、长期目标 |
| **OpenCode** | PR Review Pipeline | ✅ 专用审查 Agent | ❌ 手动 | ✅ | CI/CD 代码审查 |
| **Cursor** | Planner-Worker-Judge | ✅ 内部架构 | 部分 | ❌ | IDE 集成、大型项目 |
| **Gas Town** | Mayor-Polecat-Refinery-Deacon | ✅✅✅ 完全自主 | ✅ Beads | ✅ | 研究/实验 |
| **Hermes Agent** | Orchestrator-Worker + Kanban | ✅ delegate_task | ✅ Skill + Memory | ✅ | 自动化工作流 |

---

## 选择指南

### 如果你刚开始（Phase 1）

→ **Claude Code 或 Codex**。学习如何用单 Agent 高效完成日常编码。

### 如果你要编排多 Agent（Phase 2）

→ **Claude Code / Codex + Git Worktree**。Orchestrator-Worker 模式是最容易入门的多 Agent 范式。

### 如果你要构建大规模 Agent 系统（Phase 3）

→ 自研编排层 + 开源组件（Qdrant + bge-m3 + Git Worktree）。Gas Town 是参考架构。

---

## 关键基础设施组件

| 组件 | 推荐工具 | 用途 |
|------|---------|------|
| 向量数据库 | Qdrant / Pinecone | 语义上下文检索 |
| 嵌入模型 | bge-m3 / text-embedding-3 | 多语言文档向量化 |
| 工作空间 | Git Worktree | Agent 隔离 |
| 记忆系统 | Git-based (Beads 风格) | 跨会话持久记忆 |
| CI/CD 质量门 | GitHub Actions + 自定义 Gate | 自动验证循环 |
