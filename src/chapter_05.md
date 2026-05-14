# 第 5 章 · Context Engineering：2026 年的承重技能

---

2024 年冬天，我花了三个晚上调试一个 Agent 编排任务。任务是让两个子 Agent 协作完成一个 API 模块——一个写实现，一个写测试。模型用的 Claude Sonnet，指令写得很清楚，每个 Agent 的任务边界都画好了。

结果连续三次，实现 Agent 写出的代码用了错误的数据模型。不是语法错误——逻辑是对的，模型是对的——但它用的 Schema 是项目三个月前的版本。我一直盯着 Prompt 改。换了三种措辞。加了「请使用最新的 schema」。不行。

最后发现问题不在 Prompt。在上下文。Agent 启动时加载的项目文档里，API 契约那一页还是旧版本的缓存。它没有「错」。它只是看到了错误的信息。

我把那页文档更新了。同样 Prompt，同样模型，一次跑通。

这是我第一次真正理解「Context Engineering」这个词。不是从论文里读到的，是从三个晚上的挫败里长出来的。

---

## 5.1 提示词不够了

2023 年，整个 AI 行业都在做同一件事：找那套神奇的话术，让模型输出更好的结果。「Let's think step by step」「你是一个专业的软件工程师」「请确保代码包含完整的错误处理」——每个人手上都攒了一套自己觉得好用的模板。

这个事情，叫 Prompt Engineering。

到 2024 年底，讨论开始变了。不是提示词不重要了——而是所有人都意识到，提示词能做的事已经摸到了天花板。你可以在 Prompt 里写一万字的指令，但如果 Agent 拿到的项目上下文是错的，指令再精准也没用。

2025 年到 2026 年，行业关注的重心开始迁移。Anthropic 在它的 *2026 Agentic Coding Trends Report* 里把一句话放在了很显眼的位置：

> **Context Engineering is the load-bearing skill of 2026.**

「承重技能」。这个词选得很准。它的意思是：在多 Agent 系统里，有很多东西在运转——Prompt、模型能力、任务分解、验证循环——但如果上下文工程这个承重墙垮了，整个系统都站不住。

那什么是 Context Engineering？

最简单的定义：**设计、构建和管理注入给 AI Agent 的信息环境。**

展开说，它包括四件事：

1. **信息选择**——从海量项目知识里，选哪些给 Agent 看
2. **信息结构**——以什么格式、什么层级组织这些信息
3. **注入时机**——在 Agent 执行周期的哪个阶段给什么
4. **信息更新**——项目状态变化时，怎么同步 Agent 的认知

它和 Prompt Engineering 的核心区别是：Prompt 决定 Agent 「怎么想」，Context 决定 Agent 「知道什么」。一个人思考得再好，如果知道的信息是错的，结论必然出错。

---

## 5.2 上下文窗口的物理约束

理解 Context Engineering，要从一个冷冰冰的数字开始。

目前主流的上下文窗口是 128K tokens。这个数字听起来很大——大概相当于一本中篇小说。但它一旦被分配，立刻捉襟见肘：

```
128K tokens 总预算
  - 10%  系统提示（工具定义、角色设定、行为规则）
  - 10%  Agent 间通讯协议（MCP 等）
  - 5%   当前会话的对话历史
  ────────────────
  ≈ 96K tokens 留给项目上下文
```

96K tokens 对于一个 10 万行的代码库意味着什么？意味着你只能给 Agent 看这个项目的冰山一角。

这就是 Context Engineering 的第一个硬约束：**你不能把全部信息塞进去。你必须选择。而你选择什么，直接决定了 Agent 的理解深度和决策质量。**

这个约束不像「模型能力不足」那样可以通过升级模型来解决。上下文窗口会继续扩大——200K、500K、1M——但项目也会变得更大。比例问题不会消失。

更微妙的是第二个约束：**上下文太长会降低准确率。** 这不是猜测。多项研究已经表明，当上下文超出某个阈值（通常是 60-80% 窗口容量），模型在长上下文中的「中间部分」会开始丢失信息。它的注意力被稀释了。

所以 Context Engineering 的目标不是「塞更多信息」，恰恰相反——是**用更少、更精准的信息，让 Agent 做出更准确的判断。**

---

## 5.3 四个核心策略

我在实践中收敛到四个策略。它们不是理论推演，是在多个项目的 Agent 编排中反复验证过的。

### 策略 1：分层注入

不是一次性把所有上下文倒给 Agent。而是按照「Agent 在什么时候需要什么」来分批次、分深度地注入。

```
Layer 1 (Always)       项目骨架：技术栈、目录结构、核心架构原则、编码规范
Layer 2 (On-Demand)    模块级上下文：当前任务相关的模块文档、API 契约、数据模型
Layer 3 (Deep Dive)    决策背景：相关 ADR、历史设计权衡、已知陷阱和边界条件
```

Agent 启动时只拿到 Layer 1。这足够让它在不犯错的前提下理解项目的形状。当它开始执行一个具体任务——比如「实现用户认证 API」——再注入 Layer 2：认证模块的 spec、数据库 schema、与之交互的模块的接口契约。如果它在执行过程中触发了某个架构相关的决策——比如「缓存策略应该用 Redis 还是本地缓存」——给它 Layer 3：之前关于缓存选型的 ADR 和性能测试数据。

分层注入的价值不是省 token，是**减少噪音**。Agent 同时看到的无关信息越多，它做出错误推断的概率越大。

### 策略 2：语义检索

你不能手动为每个任务挑选上下文——任务太多，上下文太复杂。

语义检索的做法是：把项目知识向量化存储，Agent 接到任务后，自动检索与之最相关的文档、代码片段和决策记录。

具体实现：

```python
# 项目知识入库
# 源：文档、代码注释、ADR、Spec、API 契约
# 嵌入模型：bge-m3（多语言，中文表现好）
# 向量库：Qdrant

def retrieve_context(task_description: str, top_k: int = 5) -> list[Document]:
    query_vector = embed(task_description)
    results = qdrant.search(
        collection_name="project-knowledge",
        query_vector=query_vector,
        limit=top_k
    )
    return [doc for doc in results if doc.score > 0.7]
```

这里有一个参数值得注意：**top_k = 5，不是 20。** 不是检索越多越好。Agent 能有效消化的并行信息量是有限的。给 5 个高度相关的文档，效果远好于给 20 个勉强相关的。

### 策略 3：结构化上下文

Agent 不只是需要信息。它需要**结构化的**信息。

对比一下：

```
❌ 非结构化上下文：
「我们项目用的 PostgreSQL，API 是 RESTful 的，前端用的 React，
认证那边用的是 JWT，注意 token 有效期是 24 小时，
数据库连接池最大是 50，对了我们最近把日志切到了 OpenTelemetry...」
```

```
✅ 结构化上下文：
```yaml
project:
  name: payment-service
  stack:
    backend: go 1.21
    database: postgresql 15
    cache: redis 7
  architecture:
    pattern: modular-monolith
    modules: [auth, payment, notification, billing]

auth:
  method: JWT
  token_ttl: 24h
  refresh_window: 7d

database:
  pool_max: 50
  migration_tool: golang-migrate

constraints:
  - p95_latency < 200ms
  - test_coverage >= 80%
  - no_circular_module_deps
```

非结构化上下文消耗的 token 和结构化的一样多——但 Agent 从结构化版本里提取关键信息的速度快得多。它不需要在段落里翻找「数据库连接池是多大」。更重要的是，结构化上下文减少了 Agent 的「自由推断」空间——它不会因为读了一段模糊描述而脑补出错误的默认配置。

### 策略 4：上下文刷新

这是最容易被忽略，但出问题概率最高的一个。

项目在变化。昨天合并的 PR 改了 API 契约，今天上线的配置变更了缓存策略。如果 Agent 的上下文还停留在昨天的状态，它就会基于过时的假设做出决策。

我踩过的坑：Agent 用三天前的 API 契约写了一整天的代码，合并后发现接口不匹配——整个 PR 废掉。

上下文刷新的核心机制：

```
触发条件:
  - PR 合并 → 更新相关模块的 API 契约
  - 配置变更 → 更新约束条件
  - 架构决策 → 追加 ADR 到 Layer 3

刷新方式:
  - 不是全量重建（太慢）
  - 是增量更新 + 版本标记
  - Agent 可查询「这段时间发生了什么变化」
```

实现上不需要很复杂。一个简单的 Git Hook 在每次 main 分支有新提交时，检查变更文件列表，更新对应的上下文模块就行了。

---

## 5.4 Agent 的失忆症：你不说，它就不知道

Steve Yegge 用一个比喻说清楚了 Agent 最致命的问题：

> **每次新会话，Agent 都像电影《初恋 50 次》里的女主角——完全不记得昨天的事。**

传统的软件工程里，团队记忆通过文档、代码注释、Jira、Slack 聊天记录，以及最重要的——每个人的大脑——来传播。但在多 Agent 系统中，Agent 没有「大脑」。它每次启动都是一张白纸。

这个问题叫「50 First Dates」。

Yegge 的解法是 Beads——一个以 Git 为基础的 Agent 记忆系统。每次会话结束，Agent 把关键的学习写入 Git 仓库。下次启动时，这些学习被注入到上下文里。

借鉴这个思路，更通用的实现可以是这样：

```
~/.agent-memory/
├── sessions/
│   ├── 2026-05-01.md    ← 每次会话的关键学习
│   │   「auth 模块的 token 刷新逻辑有竞态条件，需要加分布式锁」
│   │   「payment 模块的第三方回调需要用幂等键去重」
│   └── 2026-05-02.md
│       「notification 的批量发送在 10K+ 时 OOM，需要分页」
│
├── decisions/
│   ├── ADR-001.md       ← 为什么选了 Redis 而不是本地缓存
│   └── ADR-002.md       ← 为什么 user 表没用 UUID 做主键
│
└── pitfalls/
    └── known-issues.md  ← 已知陷阱，新 Agent 启动时必须注入
        「payment 模块的退款接口不是幂等的——不要在生产环境直接调」
```

关键不是格式。关键是**Agent 停止会话前必须输出自己的学习总结。** 如果它不写，记忆链就断了。这是一个人的流程问题，不是工具问题。

---

## 5.5 搭一个能用的 Context System

这一节不是「概念介绍」。是我在实际项目中用的方案。你可以直接拿去改。

### 架构

```
                    ┌─────────────┐
                    │ Orchestrator │
                    │   (Agent)    │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │ Context      │ │ Semantic    │ │ Memory       │
  │ Builder      │ │ Search      │ │ Store        │
  └──────┬───────┘ └──────┬──────┘ └──────┬───────┘
         │                │                │
         └────────┬───────┴────────────────┘
                  ▼
        ┌─────────────────┐
        │ Knowledge Base   │
        │ docs / code /     │
        │ ADRs / specs      │
        └─────────────────┘
```

### 三个组件的核心实现

**Context Builder** —— 负责为每个任务组装上下文包：

```python
class ContextBuilder:
    def build(self, task: Task) -> Context:
        # Layer 1: 全局上下文（每次都注入）
        global_ctx = self.load_template("global.yaml")

        # Layer 2: 语义检索相关模块
        relevant_docs = self.semantic_search(task.description, top_k=5)

        # Layer 3: 相关决策记录
        decisions = self.load_decisions(task.modules)

        # 注入最近的 Agent 记忆
        memory = self.load_recent_sessions(days=3)

        return Context(
            global=global_ctx,
            relevant=relevant_docs,
            decisions=decisions,
            memory=memory,
            token_budget=90000  # 预留 6K 给对话
        )

    def compute_tokens(self, ctx: Context) -> int:
        # 估算 token 数。中文粗略换算：1 字符 ≈ 1.5 token
        total_chars = sum(len(str(v)) for v in ctx.__dict__.values())
        return int(total_chars * 1.5)
```

**Semantic Search** —— 用向量检索找到与任务相关的上下文：

```python
# 依赖：qdrant-client, sentence-transformers
# 嵌入模型：BAAI/bge-m3

class SemanticSearch:
    def __init__(self):
        self.encoder = SentenceTransformer("BAAI/bge-m3")
        self.client = QdrantClient(path="./qdrant_data")

    def index_project(self, docs_dir: str):
        """首次运行：将项目文档入库"""
        for f in Path(docs_dir).rglob("*.md"):
            doc = f.read_text()
            chunks = self._chunk(doc, max_chars=2000)
            for i, chunk in enumerate(chunks):
                vector = self.encoder.encode(chunk).tolist()
                self.client.upsert(
                    collection_name="project-knowledge",
                    points=[{
                        "id": f"{f.stem}_{i}",
                        "vector": vector,
                        "payload": {"source": str(f), "content": chunk}
                    }]
                )

    def search(self, query: str, top_k: int = 5) -> list[str]:
        vector = self.encoder.encode(query).tolist()
        results = self.client.search(
            collection_name="project-knowledge",
            query_vector=vector,
            limit=top_k,
            score_threshold=0.7
        )
        return [r.payload["content"] for r in results]
```

**Memory Store** —— Git-based Agent 记忆，借鉴 Beads 思路：

```python
class MemoryStore:
    def __init__(self, repo_path: str = "~/.agent-memory"):
        self.repo = Path(repo_path).expanduser()
        self.repo.mkdir(parents=True, exist_ok=True)

    def save_session(self, agent_id: str, learnings: list[str]):
        """每个 Agent 会话结束前必须调用"""
        date = datetime.now().strftime("%Y-%m-%d")
        file = self.repo / "sessions" / f"{date}_{agent_id}.md"
        file.parent.mkdir(exist_ok=True)
        content = "\n".join(f"- {l}" for l in learnings)
        file.write_text(content)
        # git commit（如果有 Git 仓库）

    def load_recent(self, days: int = 3) -> str:
        """加载最近 N 天所有 Agent 的学习"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []
        for f in sorted((self.repo / "sessions").glob("*.md")):
            if datetime.fromtimestamp(f.stat().st_mtime) > cutoff:
                recent.append(f.read_text())
        return "\n---\n".join(recent)
```

### 验证这套系统好不好用的三个测试

搭完之后不要直接上生产。先跑三个测试：

**测试 1：旧知识测试。** 给 Agent 一个任务，涉及三天前变更过的 API 契约。观察它是否使用了最新的契约。如果它用了旧版本，你的上下文刷新机制有 bug。

**测试 2：噪音干扰测试。** 在 Layer 2 里故意注入 3 个与当前任务无关的文档。观察 Agent 是否被无关信息带偏，开始讨论不相干的模块。如果被带偏了，你的语义检索阈值太高（top_k 太大或 score_threshold 太低）。

**测试 3：记忆持久化测试。** 在一个会话中让 Agent A 发现一个 Bug 并记录到 Memory Store。启动一个新的 Agent B，给它一个相关任务，观察它是否从 Memory Store 中读到了 Agent A 的发现并避开了同样的坑。如果没避开，你的记忆注入流程有缺口。

---

## 5.6 为什么这件事现在必须做

对 Context Engineering 最常见的误解是：「等工具成熟了再说。」

但 Context Engineering 不是一个「可以等的工具」。它是**决定你的 Agent 系统能否工作的基础设施。** 模型能力每提升一次，能做的事情就更多——能做的越多，错误上下文造成的损失就越大。

一个简单的类比：数据库索引不是「等数据量大了再建」——数据量大了你才发现没建索引，你已经慢了半年。Context Engineering 是一样的。你现在不建，等项目复杂度和 Agent 数量都上来的时候再补——那时候每个 Agent 都在基于错误或过时的信息做决策，你要同时修正上下文和修正已经被破坏的代码。

我在 Yegge 的 Gas Town 案例里看到过一个细节，每次重读都让我觉得后怕：Agent 擦除了生产数据库的密码配置。「数据库下线两天。」如果 Gas Town 有完善的 Context Engineering——如果 Agent 在操作数据库配置时能看到一个上下文约束写着「数据库密码 = 不可触碰的生产基础设施」——这件事可能不会发生。

Context Engineering 做的不是锦上添花。它做的是防止灾难。

---

> *第 5 章是《代码之后》全书中最具技术深度的章节。如果你觉得有用，也可能会对第 6 章（Agent 编排实战 + 可复用模板）和第 8 章（12 个月转型计划）感兴趣。本书在 GitHub 开源更新，Star 仓库跟踪进度。*
