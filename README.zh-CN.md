# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**让昂贵模型负责决策，让低成本模型负责执行，让项目状态跨 Agent 对话持续存在。**

一个项目。一个长期保留的经理。恰当数量的 Workers。共享的仓库状态。

> 项目状态：v0.1.0 · Apache-2.0 · Benchmark pending

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

## 它会做什么

- 为整个项目保留一个固定 Project Lead 对话。
- 默认只使用一个 Worker，仅在工作独立且写入范围互斥时并行。
- 每个 Worker 都有目标、写入范围、依赖、禁止修改项和完成标准。
- 将 Lead 的全局状态与 Worker 自有状态分开，避免并发争写。
- 升级的是决策和模糊意图，而不是让 Owner 人工搬运消息。
- 按角色渐进加载上下文，Worker 不读取 Lead 的全部探索过程。
- 提供无第三方依赖的状态校验、状态转换和管理汇总。
- 提供成对 benchmark 工具，但不发布未经真实测量的节省结论。

它**不会**自动切换顶层模型、创建指定模型对话、自动 push、部署生产环境或绕过宿主审批。

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

### 2. 打开 Project Lead

选择 strong 模型，然后直接用自然语言描述最终目标：

```text
$tiered-agent-orchestrator 构建导入流水线、迁移现有调用方，并跑通完整集成测试。
```

Lead 会检查仓库、创建 `.tiered-agent` 状态、决定架构，并判断委派是否真的能减少强模型工作量。

### 3. 只创建 Lead 要求的 Workers

典型提示是：

```text
创建一个 economy Worker 对话，并发送：
$tiered-agent-orchestrator continue worker-1
```

如果存在三个真正独立的任务，Lead 会给出三行分别对应 Worker 的命令；如果工作强耦合，就只使用一个 Worker。

平时在 Worker 对话中工作。遇到 blocker、模糊方向变化、架构决策或想看总进度时，回到最初的 Project Lead 对话：

```text
$tiered-agent-orchestrator status
```

## 命令

| 调用 | 行为 |
|---|---|
| `$tiered-agent-orchestrator <目标>` | 先做复杂度门控，只为合适的工作初始化 Project Lead |
| `$tiered-agent-orchestrator continue worker-1` | 仅凭仓库状态继续一个明确 Worker |
| `$tiered-agent-orchestrator continue reviewer-1` | 继续 Lead 明确创建的 Review |
| `$tiered-agent-orchestrator status` | 汇总 Workers、Review、blockers、风险和下一角色 |
| `$tiered-agent-orchestrator continue lead` | 让原 Project Lead 与最新仓库状态重新同步 |

简单、局部、低风险任务由当前 Agent 直接完成，不创建完整组织状态。

## 运行时状态

```text
.tiered-agent/
├── STATE.json
├── PLAN.md
├── OWNER_DIRECTIVES.md
├── HANDOFF.md
├── inbox/owner/<event-id>.md
├── workers/<worker-id>/
│   ├── TASK.md
│   ├── STATUS.json
│   └── BLOCKER.md
└── review/
    ├── TASK.md
    ├── STATUS.json
    └── REPORT.md
```

`STATE.json` 保持很小，不保存聊天记录、隐藏推理、secret、终端历史或具体模型名。`PLAN.md` 保存正式决策而不是思维过程，`HANDOFF.md` 只保存下一角色必须知道的内容。

全局状态、计划、正式 Owner 指令和任务分配只有一个写入者：PROJECT_LEAD。每个 Worker 只能写自己的代码范围、状态、blocker 和唯一命名的 Owner 反馈事件。

## 状态辅助工具

Python 3.9+ 是唯一运行依赖。工具只使用标准库，并且不会覆盖已经初始化的状态。

```console
python scripts/statectl.py init --project-root /path/to/project --project-id my-project --profile generic
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement the parser" --allowed-scope "src/parser/**" --completion-criterion "Parser tests pass"
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

升级策略基于证据，而不是“失败三次必停”。只要每次尝试都验证新的明确假设，Worker 可以继续；当它开始重复同类失败且没有新证据时就停止。

## Review 策略

低风险且验证充分的工作可以不创建独立 Review。中大型修改通常使用 balanced Reviewer。只有高风险、核心算法、架构、安全或多 Worker 集成任务才使用 strong Reviewer。

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

测试覆盖不覆盖式初始化、schema 与路径安全、Worker 注册和转换、并行写域冲突、blocker 恢复、Review、Owner 原话保存、管理汇总、A–J 全部行为契约和 benchmark 聚合。

## 兼容性与当前限制

- 不同对话必须共享一个可写仓库。
- v1 由 Owner 手动打开指定模型的顶层对话。
- 不同宿主的模型和 reasoning 名称可能不同，必要时使用通用 Profile。
- Token 与 credits 必须来自宿主遥测或有记录的人工测量。
- SkillsMP 独立按自己的周期扫描公开 GitHub 仓库；发布仓库不能保证立刻完成索引。

项目结构遵循 [Agent Skills 规范](https://agentskills.io/specification)和[官方 OpenAI Skill 文档](https://learn.chatgpt.com/docs/build-skills)。OpenAI 模型映射依据[官方模型说明](https://learn.chatgpt.com/docs/models)。

## 卸载

从 Agent 的 Skill 目录删除本项目即可。项目运行状态与 Skill 安装相互独立；只有在明确希望丢弃某个项目的编排历史时，才删除该项目的 `.tiered-agent/`。

## 许可证

Apache-2.0，详见 [LICENSE](LICENSE)。
