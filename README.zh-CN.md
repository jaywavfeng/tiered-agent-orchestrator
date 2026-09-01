# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**使用最有可能正确完成任务且不会造成昂贵返工的最低成本模型，并让项目状态跨 Agent 对话持续存在。**

一个项目。一个长期保留的经理。可复用的长期 Workers。共享的仓库状态。

> 项目状态：v0.4.2 · Apache-2.0 · Benchmark pending

## 为什么需要它

强模型适合理解模糊意图、做架构决策、拆分任务、重大纠偏和困难 Review，但用它持续搜文件、改普通代码、跑命令和重复测试通常并不划算。

`tiered-agent-orchestrator` 把大型工程任务组织成一个小型软件团队：

```text
OWNER
  └── PROJECT_LEAD（strong）
        ├── WORKER 1（economy）
        ├── WORKER 2（economy，仅在真正可并行时）
        └── REVIEWER（balanced 或 strong，仅在值得时）
```

Project Lead 把昂贵推理蒸馏成精炼计划和明确任务，Workers 完成大部分实现。运行状态保存在 `.tiered-agent/`，所以全新对话不依赖聊天历史也能接班。

**你不需要复制任何上一段聊天内容。**

### 完成价值优先执行

> **Use the cheapest model that is likely to complete the task correctly without costly rework.**

TAO 的优先级是：先正确完成任务，再减少 strong/Sol 使用量，再减少 credits/成本，再减少不必要的上下文和模型切换，最后才是减少总 Token。目标是每个已完成任务的价值，而不是单次运行的最低成本。Sol 只处理模糊需求、架构、重大决策、高风险 blocker 和最终验收；普通执行默认由 Luna/xhigh Worker 负责。为避免返工，允许 Luna 使用更多 reasoning Token。

模型路由是硬约束。普通执行直接默认 `gpt-5.6-luna / xhigh`，不要为了省一点单次 native reasoning 导致返工。只有宿主既接受显式 `model: "gpt-5.6-luna"`、`reasoning_effort: "xhigh"`，又返回两者的机器可读 actual/effective 值时，才允许原生 dispatch。参数被接受或回显、success 标志和 nickname 都不是证明；元数据缺失或矛盾时必须在实质 native 工作前 fail closed，Sol 也不得接手代做。Owner 自己创建的顶层对话不同：TAO 最多检查明确可见的模型类型，完全不校验、不门控 reasoning。Luna/high、Luna/极高或 Luna 的其他 reasoning 都直接继续；Agent 看不到模型指示时也直接继续，不要求检查 selector 或重发命令。路由证据不等于计费证据：只有宿主按模型/按对话遥测或有记录的人工测量才能把 Token/credits 归因给 Luna。Native Terra 升级和 Reviewer 保留严格门控；手动顶层对话使用较轻规则。

## 它会做什么

- 为整个项目保留一个固定 Project Lead 对话。
- 默认只使用一个长期 Worker 对话，并在连续 milestones 之间复用它。
- 只有真正并行、职责或上下文明显不同、上下文隔离收益明确，或原 Worker 已明确停用时才增加 Worker，而且收益必须高于协调和 Token 成本。
- 每个 Worker 都有目标、写入范围、依赖、禁止修改项和完成标准。
- 复用稳定 Worker ID 前先归档已完成 assignment，旧任务证据不会被无记录覆盖。
- 只为新的 actionable Owner 工作 reopen 已完成项目，并先归档不可变的完成快照。
- 将 Lead 的全局状态与 Worker 自有状态分开，避免并发争写。
- 把 Review 当作同步屏障；一旦重新进入 execution，旧 Review 证据自动失效并要求重新 Review。
- 分配 strong-tier Review 前必须记录明确的高风险理由。
- 升级的是决策和模糊意图，而不是让 Owner 人工搬运消息。
- 按角色渐进加载上下文，Worker 不读取 Lead 的全部探索过程。
- 提供无第三方依赖的状态校验、状态转换和管理汇总。
- 提供成对 benchmark 工具，但不发布未经真实测量的节省结论。

它**不会**在无法保证低成本模型时自动切换顶层模型或创建指定模型对话，也不会自动 push、部署生产环境或绕过宿主审批。

## 快速开始

### 1. 安装 Skill

在单个 Codex 仓库中使用时，克隆到仓库级 Skill 目录：

```console
git clone https://github.com/jaywavfeng/tiered-agent-orchestrator.git .agents/skills/tiered-agent-orchestrator
```

希望 Codex 对所有项目可发现时，放到：

```text
$HOME/.agents/skills/tiered-agent-orchestrator
```

其他兼容 Agent Skills 的 Coding Agent 可以把同一个目录安装到它支持的 Skill 位置。可移植接口是根目录 `SKILL.md`；`agents/openai.yaml` 只是可选的 OpenAI 专用元数据。

该 Skill 仅支持显式调用，不会因普通自然语言自动触发。每次编排请求都必须显式包含 `$tao`；仅仅存在 `.tiered-agent`、以前调用过 TAO、或正在修改 TAO 自身，都不能隐式激活 Skill。

### 2. 打开 Project Lead

选择 strong 模型，然后直接用自然语言描述最终目标：

```text
$tao 构建导入流水线、迁移现有调用方，并跑通完整集成测试。
```

Lead 只读取做架构决策所需的最少入口，创建 `.tiered-agent` 状态，并判断委派是否能减少强模型工作量。常规机械工作必须下放给低成本 Worker；dispatch 后 Lead 可以 passive wait 等待自动推进，但不轮询 `STATUS.json`。timeout 不算 milestone，禁止 timeout → Sol 重新分析 → 查 STATUS → 再 wait 的高频循环。

### 3. 只创建一次默认 Worker，之后持续复用

典型提示是：

```text
创建一个 economy Worker 对话，并发送：
$tao continue worker-1
```

进入下一个串行 milestone 时，Lead 会把新任务重新分配给 `worker-1`，Owner 回到原 Worker 对话即可。仅仅切换 milestone 绝不会创建 `worker-2`。

已完成项目后来收到 actionable 反馈时，在原 Lead 对话显式调用 `$tao`。Lead 用 `reopen-project` 归档旧完成态、回到 planning，再把任务重新分配给原 completed Worker。提问、总结、解释、状态查询或尚不明确的意见不会 reopen；方向不清时先澄清，项目保持 complete。

平时在 Worker 对话中工作。遇到 blocker、模糊方向变化、架构决策或想看总进度时，回到最初的 Project Lead 对话：

```text
$tao status
```

### 跨 milestone 复用

```text
Lead:
$tao 完成这个项目

Worker conversation:
$tao continue worker-1

M1 完成
↓
回到 Lead：继续
↓
Lead 将 M2 重新分配给 worker-1
↓
回到原 Worker 对话：
$tao continue worker-1
```

只有另一项工作真正独立并可并行，或需要明显不同的职责和隔离上下文时，Lead 才应提示 Owner 创建新对话：

```text
$tao continue worker-2
```

### Dispatch 生命周期

理想的原生模式（仅限返回回执证明 actual/effective model 与 reasoning 的宿主）：

```text
Owner
  ↓
Sol Project Lead
  ↓
显式 spawn gpt-5.6-luna / xhigh worker-1
  ↓
Lead passive wait 等待事件（timeout 不算 milestone）
  ↓
Luna 完成检查 / 实现 / 训练
  ↓
milestone event
  ↓
Sol 读取摘要并决定下一阶段
  ↓
Lead 重新分配同一个 worker-1
```

effective model/reasoning 元数据缺失、不受支持、被拒绝或互相矛盾时：

```text
Sol Project Lead 准备 worker-1，并停止未经确认的 native Worker
  ↓
Sol 停止
  ↓
Owner 打开 gpt-5.6-luna（建议 xhigh）并发送：
$tao continue worker-1
```

对 Owner 自己创建的对话，只检查明确可见的模型类型，完全不检查 reasoning：Luna/high、Luna/极高或 Luna 的其他 reasoning 都继续。Agent 看不到模型指示时，直接继续原 Worker，不要求 Owner 检查 selector、重发命令、提供证明或新建 Worker。明确显示模型错误时，最多简短提醒一次并保留同一对话。计费归因仍需宿主遥测或有记录的人工测量。TAO 不会在 dispatch 后持续轮询或重复 Worker 工作；一次 passive wait 没有新事件便结束等待，不再触发 Sol 分析循环。Luna 同一失败方案无新证据时必须停止，先升级 Terra，不得无意义重试。

## 命令

| 调用 | 行为 |
|---|---|
| `$tao <目标>` | 先做复杂度门控，只为合适的工作初始化 Project Lead |
| `$tao continue worker-1` | 仅凭仓库状态继续一个明确 Worker |
| `$tao continue reviewer-1` | 继续 Lead 明确创建的 Review |
| `$tao status` | 汇总 Workers、Review、blockers、风险和下一角色 |
| `$tao continue lead` | 让原 Project Lead 与最新仓库状态重新同步 |

简单、局部、低风险任务由当前 Agent 直接完成，不创建完整组织状态。

## 运行时状态

```text
.tiered-agent/
├── STATE.json
├── PLAN.md
├── OWNER_DIRECTIVES.md
├── HANDOFF.md
├── inbox/owner/<event-id>.md
├── history/completion-<revision>/
│   └── 完整的全局、Worker 与 Review 完成快照
├── workers/<worker-id>/
│   ├── TASK.md
│   ├── STATUS.json
│   ├── BLOCKER.md
│   └── history/assignment-<revision>/
│       ├── TASK.md
│       ├── STATUS.json
│       └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    ├── REPORT.md
    └── history/review-<revision>/
```

`STATE.json` 保持很小，不保存聊天记录、隐藏推理、secret、终端历史或具体模型名。`PLAN.md` 保存正式决策而不是思维过程，`HANDOFF.md` 只保存下一角色必须知道的内容。

全局状态、计划、正式 Owner 指令、任务分配和 assignment 归档只有一个写入者：PROJECT_LEAD。每个 Worker 只能写自己的代码范围、当前状态、blocker 和唯一命名的 Owner 反馈事件。任务完成后，只有 Lead 的 reassignment 事务可以归档这些文件并把 Worker 重置为 `ready`。

## 状态辅助工具

Python 3.9+ 是唯一运行依赖，工具只使用标准库。初始化不会覆盖已有状态；reopen 会先快照完成项目；Worker 与 Review reassignment 会保留旧证据，并在替换当前状态前恢复任何中断的多文件事务。

```console
python scripts/statectl.py init --project-root /path/to/project --project-id my-project --profile generic
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement the parser" --allowed-scope "src/parser/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py reopen-project --project-root /path/to/project --reason "Owner requested a correction" --milestone "M2 correction"
python scripts/statectl.py reassign-worker --project-root /path/to/project --worker-id worker-1 --milestone "M2" --objective "Integrate the parser" --allowed-scope "src/integration/**" --completion-criterion "Integration tests pass"
python scripts/statectl.py resolve-owner-feedback --project-root /path/to/project --event-id <event-id> --resolution "Integrated into M2"
python scripts/statectl.py validate --project-root /path/to/project
python scripts/statectl.py status --project-root /path/to/project
```

没有 Python 时，Agent 可以手动维护这些文件，但必须遵守 schema 和所有权规则。

## 模型 Profiles

核心协议只认识 `strong`、`balanced` 和 `economy`。

- [OpenAI Codex Profile](profiles/openai-codex.md) 映射当前 Sol/Terra/Luna 系列。
- [通用 Profile](profiles/generic.md) 说明如何映射其他宿主或模型提供方。

Profile 是可编辑建议。替换具体模型映射不会改变项目持久化状态。

## Owner 反馈与 Blocker

明确、局部的 Owner 纠正由 Worker 直接执行。如果 Owner 说“这个方向太工程化了”之类的高层反馈，Worker 不会擅自翻译成架构修改，而是保存 Owner 原话、暂停冲突工作并把决策交回原 Project Lead。

完成态被冻结但可以 reopen。Lead 对只读 follow-up 直接回答且不改状态；actionable 工作先快照旧完成态、显式 reopen，再复用原 Worker。Owner event 只从 frontmatter 读取状态，Owner 原文无法伪造 pending event。

升级策略基于证据，而不是“失败三次必停”。只要每次尝试都验证新的明确假设，Worker 可以继续；当它开始重复同类失败且没有新证据时就停止。

## Review 策略

低风险且验证充分的工作可以不创建独立 Review。中大型修改通常使用 balanced Reviewer。只有高风险、核心算法、架构、安全或多 Worker 集成任务才使用 strong Reviewer。

Review 后代码一旦变化，旧 approval 立即失效。TAO 保留旧证据、要求新的 Review，并在发布新 Review assignment 时归档旧 Review。

## Benchmark

Benchmark pending.

仓库包含配对 JSONL schema 和聚合工具，用于比较：

- strong-model-only 全程执行；
- strong Lead + economy Workers + 可选 Review 的分层执行。

记录内容包括任务成功、测试通过率、总 Token 和分层 Token、可选成本或 credits、耗时、模型切换、Worker 对话数、升级次数和 Owner 干预。详见 [benchmark 协议](benchmarks/README.md)。发布可比的真实运行数据前，不声明任何节省百分比。

## 验证

```console
python -m unittest discover -s tests -v
python scripts/statectl.py --help
python scripts/benchmark.py --help
```

测试覆盖原子初始化、可恢复的 Worker 注册/重分配/Review 分配、completed project reopen/history、schema 与路径安全、Worker 复用、依赖与普通路径/glob 写域冲突、陈旧 Review 防护、Owner 原话保存、显式激活与模型路由契约、A–P 行为契约，以及 benchmark 归因与聚合。

## 兼容性与当前限制

- 不同对话必须共享一个可写仓库。
- v1 由 Owner 手动打开指定模型的顶层对话。
- 仓库状态可以在宿主对话丢失后恢复同一个 formal Worker，但 TAO 无法复活宿主本身已经丢失的 conversation object。
- 初始化采用原子发布；Worker 注册、reopen、Worker reassignment 和 Review assignment 都支持 crash recovery。旧版本已经留下的 partial runtime 仍会 fail closed，需要人工检查后处理。
- 不同宿主的模型和 reasoning 名称可能不同，必要时使用通用 Profile。Owner 创建的对话绝不根据 reasoning 标签门控 continuation。
- Native effective metadata 只证明 native 路由，不证明计费；手动路由由 Owner 控制。Token 与 credits 归因必须来自宿主按模型/按对话遥测或有记录的人工测量，否则记为 unknown。
- SkillsMP 独立按自己的周期扫描公开 GitHub 仓库；发布仓库不能保证立刻完成索引。

项目结构遵循 [Agent Skills 规范](https://agentskills.io/specification)和[官方 OpenAI Skill 文档](https://learn.chatgpt.com/docs/build-skills)。OpenAI 模型映射依据[官方模型说明](https://learn.chatgpt.com/docs/models)。

## 卸载

从 Agent 的 Skill 目录删除本项目即可。项目运行状态与 Skill 安装相互独立；只有在明确希望丢弃某个项目的编排历史时，才删除该项目的 `.tiered-agent/`。

## 许可证

Apache-2.0，详见 [LICENSE](LICENSE)。
