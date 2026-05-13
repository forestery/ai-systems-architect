# 第 6 章 · Agent 编排实战

---

前五章讲的是「正在发生什么」和「你应该在哪」。这一章开始讲「怎么做」。

编排 Agent 不是理论。它是你在终端里敲的命令、你为每个 Worker 准备的上下文、你在合并前跑的那一步验证。这一章的内容全部来自实际编排经验——有做对的，也有做错了才学会的。

---

## 6.1 选范式

第 2 章分析了三种架构模式。但在一个具体项目开始前，你需要一个简单的决策矩阵。

| 项目规模 | 推荐范式 | 为什么不选更复杂的 |
|---------|---------|------------------|
| 小型（<1 万行） | 单 Agent + 上下文工程 | 多 Agent 编排的开销比任务本身还大 |
| 中型（1-10 万行） | Orchestrator-Worker | 拆 3-5 个子任务刚好，不需要 Planner 层 |
| 大型（>10 万行） | Planner-Worker-Judge | 需要独立的规划和裁决层来管理复杂度 |

### 一个我反复犯的错

刚开始用多 Agent 编排时，我有个毛病：什么任务都拆成三个子任务，分给三个 Worker。觉得这样才「充分利用了多 Agent 的能力」。

然后我发现，一个两分钟的任务——给一个配置文件加个字段——拆成三个子任务后，光协调就花了一分钟。更糟的是，Worker A 等 Worker B 的 spec，Worker B 等 Worker A 的确认——两个 Agent 互相等，死锁了。

**编排的粒度要和任务的复杂度匹配。** 如果一个任务在单 Agent 的上下文窗口里能完整处理，就不要拆。编排本身有成本——任务分解、分配、结果合并、异常协调——这些成本是固定的，你必须确保任务本身的复杂度让它值得。

---

## 6.2 拆任务

这是 Orchestrator 最核心的技能。一个任务拆得好不好，直接决定 Worker 能不能独立执行、能不能并行。拆得好，三个 Worker 一小时干完。拆不好，五个 Worker 互相等，一天出不来。

### 拆得好是什么样的

拆得好的任务有三个特征：

**原子性。** 每个子任务小到一个 Worker 在自己的上下文窗口里能完整处理。不需要中途「查一下另一个模块的文档」——那个文档已经在它的上下文里了。

**独立性。** 子任务之间尽量没有依赖。如果有依赖，必须是明确的、可等待的（「任务 B 在任务 A 完成后再开始」），而不是隐式的（任务 B 做到一半发现它需要任务 A 的结果，但任务 A 还没做）。

**可验证性。** 每个子任务完成后，有一个自动化的标准来判断它「是否做对了」。编译通过不算验证。单元测试全部通过才算。对于没有自动验证方式的任务，不要发给 Agent——Agent 在「没有反馈」的情况下会以为自己做得对，实际上可能全错。

### 一个反例和一个正例

**反例：**

```
任务：「实现用户登录功能」

子任务：
  1. 写前端登录表单
  2. 写后端 API
  3. 写数据库 schema
  4. 写测试
```

为什么这是糟糕的拆法：子任务 1-3 有隐式依赖。前端的表单字段取决于后端 API 的请求格式。后端 API 的格式取决于数据库 schema 的字段定义。但三个 Worker 同时开始工作——每个 Worker 基于自己的理解定义接口格式——最后三个产出在接口层完全不兼容。

**正例：**

```
任务：「实现用户登录功能」

子任务：
  1. [Design Agent] 产出 API 契约和数据模型
     → 输出：auth-api-spec.yaml, user-schema.sql
     → 验证：spec 通过 OpenAPI 校验
     
  2. [Backend Worker] 基于 spec 实现后端
     → 输入：auth-api-spec.yaml, user-schema.sql
     → 独立可运行：是（数据库用 Docker Compose 本地实例）
     → 验证：所有端点 200 OK，单元测试通过
     
  3. [Frontend Worker] 基于 spec 实现前端
     → 输入：auth-api-spec.yaml
     → 独立可运行：是（Mock API 返回 spec 定义的格式）
     → 验证：表单可提交、错误状态可渲染
     
  4. [Test Agent] 基于 spec 编写集成测试
     → 输入：auth-api-spec.yaml, 真实的后端和前端实例
     → 验证：所有测试通过
```

区别：Design Agent 产出的 spec 是其他三个 Worker 的输入。这三个 Worker 之间的依赖被移除——它们不通信，只依赖同一个 spec。

### 怎么上手练

拆任务的能力是练出来的。我用的方法很笨但有效：每次把一个任务拆完后，用一句话问自己——**「Worker B 在执行过程中需要问 Worker A 任何问题吗？」** 如果答案是「是」，回去修。

---

## 6.3 工作空间

一个 Agent 一个工作空间。这是一条铁律。

多 Agent 在同一份文件上并发编辑，不管有没有锁，都会出问题。Git merge 冲突是最好处理的那种——更可怕的是 Agent A 改了文件的前半部分，Agent B 改了后半部分，Git 自动合并了，结果两个修改在逻辑上互相破坏。

### 方案：Git Worktree

```bash
# 为每个 Worker 创建独立 workspace
git worktree add /tmp/ws/worker-foo   # Worker Foo 的工作区
git worktree add /tmp/ws/worker-bar   # Worker Bar 的工作区
git worktree add /tmp/ws/worker-baz   # Worker Baz 的工作区

# 每个 Worker 在自己的 worktree 里工作
# Worker Foo: cd /tmp/ws/worker-foo && [执行任务]
# Worker Bar: cd /tmp/ws/worker-bar && [执行任务]
# Worker Baz: cd /tmp/ws/worker-baz && [执行任务]

# 任务完成后清理
git worktree remove /tmp/ws/worker-foo
```

### 四条规则

1. **一个 Agent = 一个 worktree。** 不共享。不绕开。
2. **Agent 只能在自己的 worktree 里写。** 它可以读主仓库的文件（通过上下文注入），但不能改别的 worktree。
3. **合并由一个专门的角色处理。** 不是我。不是一个 Worker。是 Refinery——一个专门管 merge queue 的 Agent，或者我自己在审查阶段手动合并。
4. **Worktree 在任务结束后立刻删除。** 不保留中间状态。

---

## 6.4 验证循环

Agent 产出的代码需要验证。但「跑一下测试」不够。你需要一个系统性的验证循环——不是一次，是每次合并前都跑。

### 三层验证

```
Layer 1: Agent 自检
  Worker 写代码 → 跑 lint → 跑单元测试 → 
  失败 → 修复 → 重新跑 → 三次失败 → 放弃，升级
  通过 → 进入 Layer 2

Layer 2: 交叉验证
  另一个 Agent (不是同一个 Worker) 审查代码
  检查项：架构一致性、安全基准、错误处理完整性、边界条件
  发现问题 → Worker 修复 → 重新审查
  通过 → 进入 Layer 3

Layer 3: 人类裁决
  人类看 Layer 2 的审查报告
  做最终决定：合并 / 拒绝 / 要求修改
```

最重要的是 Layer 1 的「三次失败就放弃」上限。Agent 在自检循环里可以无限重试——每次改一点，跑一下测试，不通过再改一点。我不止一次看到 Agent 在自检循环里耗了 40 分钟，修改了 15 次，最后还是错的。三次重试之后如果还不通过，说明任务定义有问题、或者上下文不够、或者这个任务不适合 Agent。停止，重新拆任务，不要继续赌。

### 一个具体的验证配置

```yaml
# .agent/gates.yaml
gates:
  layer1:
    - lint: {command: "golangci-lint run ./...", max_retries: 1}
    - unit_test: {command: "go test ./... -count=1", max_retries: 3}
    - build: {command: "go build ./...", max_retries: 1}
    
  layer2:
    reviewer: "cross-verify-agent"  # 不是同一个 Worker
    checks:
      - architecture_consistency
      - error_handling_completeness
      - sql_injection_surface
      - boundary_conditions
    
  layer3:
    human_gate: required
    timeout: 48h  # 48 小时内必须审查，否则自动拒绝 PR
```

---

## 6.5 异常处理

多 Agent 系统中，异常不是特例——它是日常。

Agent 会在不通知你的情况下静默失败（代码编译通过了但逻辑全错）。Agent 会在自检循环里无限循环。Agent 会在上下文不够的情况下开始「编造」——不是故意撒谎，而是模型在信息不足时的统计补齐行为。

你需要一个异常分类和升级机制。

### 异常分类

| 异常类型 | 表现 | 处理方式 |
|---------|------|---------|
| 编译错误 | 代码跑不起来 | Agent 自行修复，3 次失败升级 |
| 测试失败 | 逻辑不符合预期 | Agent 自行修复，5 次失败升级 |
| 静默失败 | 编译通过，测试通过，逻辑全错 | Layer 2 交叉验证捕获 |
| 上下文不足 | Agent 反复修改但始终不对 | 重新注入上下文，重试 |
| 架构冲突 | 两个 Worker 改了同一个文件 | 立即升级给人类 |
| Agent 卡死 | 45 分钟没有响应 | 超时终止，任务重新分配 |

### 升级路由

不是所有异常都应该直接到人类手里。我参考了 Gas Town 的 Deacon 设计，做了一个简单的路由规则：

```python
def route(error):
    if error.is_architecture_conflict:
        return ESCALATE_TO_HUMAN   # 架构冲突只有人能判断
    if error.retries_exceeded:
        return ESCALATE_TO_ORCHESTRATOR  # 让编排者重新考虑任务分解
    if error.is_context_overflow:
        return COMPRESS_CONTEXT     # 先尝试压缩上下文
    if error.is_silent_failure:
        return CROSS_VERIFY         # 让另一个 Agent 重新审查
    return RETRY_WITH_FRESH_AGENT   # 换一个新 Worker 重试
```

关键原则：**人类只处理 Agent 处理不了的事。** 如果你每次异常都自己看，编排的收益就被异常处理吃掉了。

---

## 6.6 模板

以下是三个可以直接改来用的编排模板。它们是我在实际项目中反复用、反复调整过的版本。

### 模板 1：功能开发

```yaml
# 适合：中型项目，1-10 万行，模块化程度好
# 不适合：依赖链超过 3 层的任务

orchestrator:
  strategy: sequential-first  # 先串行拆 spec，再并行执行
  model: claude-sonnet-4
  
stages:
  - name: design
    workers: 1
    task: "设计 API 契约、数据模型、模块接口"
    output: [api-spec.yaml, db-schema.sql, module-interfaces.yaml]
    verify: "spec 通过 OpenAPI 校验 + 数据模型通过 migration lint"
    
  - name: implement
    workers: auto  # Orchestrator 根据剩余子任务数决定
    parallel: true
    depends_on: [design]
    tasks:  # Orchestrator 从 design 产出中自动分解
      - backend
      - frontend
      - docs
    verify: "各自模块的测试通过 + 编译通过"
    
  - name: integrate
    workers: 1
    depends_on: [implement]
    task: "合并所有 Worker 的产出，运行集成测试"
    verify: "集成测试全部通过 + 无 merge conflict"

gates:
  layer2: enabled
  layer3_human: required  # 功能开发必须人类审查后合并
```

### 模板 2：Bug 修复

```yaml
# 适合：有明确复现步骤的 Bug
# 不适合：需要跨多个模块排查的间歇性 Bug

strategy: single-agent  # Bug 修复通常不需要多 Agent

agent:
  model: claude-sonnet-4
  context:
    include:
      - bug_report.md       # 包含复现步骤和期望行为
      - failing_test.go     # 复现 Bug 的测试
      - module_spec.yaml    # 相关模块的 spec
      
  workflow:
    - "阅读 bug_report.md，确保理解了期望行为"
    - "运行 failing_test.go，确认 Bug 存在"
    - "定位根因"
    - "修改代码"
    - "运行 failing_test.go → 应该通过"
    - "运行全量测试 → 确保没有回归"
    
  retry: 2  # Bug 修复最多重试 2 次
  on_failure: ESCALATE_TO_HUMAN  # Bug 修不好直接给人
```

### 模板 3：代码迁移

```yaml
# 适合：批量重命名、框架升级、API 迁移
# 不适合：涉及业务逻辑变更的迁移

strategy: batch-workers

pre_check:
  - "确认迁移脚本的正确性（用一个样例手动验证）"
  - "生成迁移前全量测试的基线数据"

workers: 3
parallel: true
task_template: |
  迁移以下文件从 [旧框架/旧 API] 到 [新框架/新 API]：
  {file_list}
  
  规则：
  - 只修改 API 调用方式，不改变业务逻辑
  - 每个文件修改后立即运行该文件的测试
  - 任何测试失败 → 停止修改 → 报告问题

verify:
  - "迁移后全量测试通过率 = 迁移前通过率"
  - "git diff 统计中，只包含预期的 API 变更多行"

rollback: "git checkout 迁移前的 commit"
```

---

### 使用模板的正确姿势

模板不是拿来就用的。每次用之前做三件事：

1. **把 `model:` 换成你实际用的模型。** 不同模型的能力差异很大，模板里的 `claude-sonnet-4` 只是占位符。
2. **把 `verify:` 换成你项目的实际测试命令。** `「各自模块的测试通过」` 在模板里是一句话，在真实项目里必须是具体的命令和验证标准。
3. **第一次用新模板时先跑一个小任务。** 不要拿新模板直接上核心功能——先拿一个低风险的模块验证整个流程能不能跑通。

---

> *第 6 章是「构建能力」部分的第一章。第 7 章会讨论编排中不可避免的质量和安全问题——当 Agent 产出速度是你自己的 10 倍，你的质量基础设施扛得住吗。*
