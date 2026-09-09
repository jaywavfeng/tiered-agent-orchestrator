# tiered-agent-orchestrator

[English](README.md) | [简体中文](README.zh-CN.md)

**先正确完成任务，再提高每个 token／credit 的实际产出。强模型负责决策，经济模型负责执行，工程文件负责接续。**

项目状态：**v0.6.0 · Apache-2.0 · Benchmark pending**

> Use the cheapest model that is likely to complete the task correctly without costly rework.

TAO 是通过 `$tao` 调用的 Codex skill。Project Lead 负责意图、架构和验收；长期复用的经济模型 Worker 负责实现与验证。默认只使用一个 Worker，跨里程碑复用。**你不需要复制任何上一段聊天内容。**

## v0.6.0 更新

- 增加可选任务绑定、简短派发消息、发送回执和完成／阻塞通知，支持已有 Worker 任务自动接力。
- 自动新建任务仍须用户明确授权，并在实质执行前提供实际生效模型及推理档位证明。当前桌面任务工具契约没有承诺这种证明；创建成功不等于路由已验证。
- 采用 **纯 TAO 协调 token ÷ 实际任务 token ≤ 10%** 的目标；benchmark 支持可选用途统计。无法归因时标为未测量，不要求日常 token 台账。
- 按角色生成上下文；普通状态操作只检查当前状态，不反复读取历史。只读查询不再隐式恢复，真实中断通过显式 `recover` 处理。
- 统一用 Python 解释器运行工具。普通 TAO 操作不得自动把脚本用 VS Code 或文件面板打开。脚本本身没有启动编辑器的实现，含糊的裸脚本调用说明已清理；历史 GUI 触发原因尚未通过原始调用记录复现。

## 安装与启动

通过 Codex 的 skill installer 安装仓库 `jaywavfeng/tiered-agent-orchestrator`，仓库内路径为 `.`，安装名为 `tiered-agent-orchestrator`。调用名保持 `tao`；唯一运行依赖是 Python 3.9+，只使用标准库。GitHub 发布不会自动覆盖已有全局安装。

新复杂项目先选好 Lead 模型，再描述目标：

```text
$tao 规划并完成本工程。默认使用一个可复用 Worker，以工程文件保存接续状态。
```

需要自动接力时，可一次性明确授权：

```text
$tao 自动向我选定的 Worker 任务发送分派，并向 Lead 发送完成或阻塞通知。优先复用已有 Worker。没有合适 Worker 且宿主能在实质执行前证明实际模型与推理档位时，创建 gpt-5.6-luna / xhigh 的新任务，直接使用当前保存的工程目录，不创建隔离 worktree。Lead 保持 gpt-5.6-sol；需要升级时优先使用 gpt-5.6-terra。
```

Lead 记录已有授权并绑定真实任务 ID，不猜测标题。宿主限制仍然有效。缺少 actual/effective 证明时，由用户先手动创建或选定经济模型任务，发送 `$tao continue worker-1`，之后在授权范围内复用自动接力。Owner-created 会话完全不检查 reasoning：Luna/high、Luna/极高 或看不到模型指示都不要求反复证明；明确看到模型系列错误时只提示修正同一任务一次。

| 操作 | 请求 |
|---|---|
| 零聊天历史接续 Lead | `$tao continue lead` |
| 继续已有 Worker | `$tao continue worker-1` |
| 继续已登记且确实独立的 Worker | `$tao continue worker-2` |
| 查询状态 | `$tao status` |

维护 TAO 本身、粘贴示例或存在 `.tiered-agent` 都不会隐式启动编排。简单局部任务直接完成。

## 工程状态与自动接续

Lead 维护目标、指令、全局状态、任务分配及可选 `TRANSPORT.json`；Worker 只维护允许范围内代码、自己的状态和阻塞证据。`HANDOFF.md` 是精简冷启动说明；`OWNER_STATUS.md` 是人类报告，不是机器状态数据库。每个事实只保留一个权威来源。

Lead 先写好 ready 分派，核实绑定任务的目录和可用状态，生成简短消息，记录 `pending`，调用 `send_message_to_thread`，再记录 `sent`、明确未送达的 `not-sent` 或 `unknown`。待定／不明确回执禁止盲目重发。Worker 检查分派版本后执行、验证并更新结果，在完成或阻塞时通知 Lead 一次。消息送达不代表任务验收通过。

使用有界、带游标的 `wait_threads`。一次无变化超时后结束等待，后续通知可唤醒空闲 Lead；不做定时轮询或重复摘要。`reassign-worker` 归档完成分派后复用同一 Worker；针对完成项目的实质修改先通过 `reopen-project` 留存快照。没有传输配置的旧工程继续人工接力。

完整宿主流程和回执格式见 [host dispatch](references/host-dispatch.md)，两次分派示例见 [one Worker flow](examples/one-worker-flow.md)。内部子代理也受严格模型证明门槛约束，不能自动视为用户已配置好的独立任务。

## 通过 Python 执行工具

在本仓库中使用：

```console
python scripts/statectl.py --help
python scripts/statectl.py init --project-root /path/to/project --project-id my-project
python scripts/statectl.py add-worker --project-root /path/to/project --worker-id worker-1 --objective "Implement parser" --allowed-scope "src/**" --completion-criterion "Parser tests pass"
python scripts/statectl.py context --project-root /path/to/project --role worker-1
python scripts/statectl.py status --project-root /path/to/project
python scripts/statectl.py validate --project-root /path/to/project
```

从 Windows 全局安装调用时，使用实际绝对路径：

```powershell
& "<python.exe 的绝对路径>" "<技能目录的绝对路径>\scripts\statectl.py" context --project-root "<工程目录>" --role worker-1
```

替换占位符，并正确引用包含空格和中文的路径。使用环境中已核实的解释器。不得直接启动 `.py` 文件、用 `code`／`Invoke-Item` 打开它，或把编辑器打开当成命令成功。参数不清楚时运行对应子命令的 `--help`；只有具体诊断需要才读取源码。无需修改文件关联或编辑器设置。

新增子命令为 `bind-thread`、`context`、`dispatch-context`、`record-dispatch`、`notification-context`、`recover`。自动接力的状态写入带 `--assignment-revision`。普通 `status` 不再返回归档数量，因为不再扫描历史；显式 `validate` 仍完整检查历史。原有所有权、依赖、写入范围、完成门槛和审查失效规则保持有效。

## 管理开销与验证

目标为同一完成任务累计的 **协调 token ÷ 实际任务 token ≤ 0.10**。架构设计和实质验收属于实际任务，即便由 Lead 完成；协议加载、派发、管理记录和重复状态检查属于协调。按模型或会话划分不能替代按用途归因，不能用账户总额度或猜测 token 数证明比例。

benchmark 记录可选增加 `purpose_usage`。数据来源、分类不完整和模拟数据规则见 [测量协议](benchmarks/README.md)。只有成功完成、归因完整且非模拟的记录才判定比例。超过 10% 时合并任务、缩减重复上下文与管理汇报，不削弱实际验证。

> **Prefer the simplest mechanism that is sufficiently reliable for the actual failure modes of the project.**

不建立常驻台账、周期审计、校验和树或额外恢复系统。只报告实际测得的文档、读取和协调动作变化，不把代理指标说成真实 token／credit 节省。公开节省证据继续标记为 **Benchmark pending**。

```console
python -m unittest discover -s tests -v
python scripts/benchmark.py --help
python scripts/benchmark.py overhead benchmarks/runs.jsonl
```

`runs.jsonl` 由实际测量提供，仓库不附带伪造的真实数据。测试使用隔离临时工程与模拟宿主回执，CI 覆盖 Windows／Ubuntu × Python 3.9／3.13。`evals/` 中场景定义不等于已经执行真实 Agent 测试；模拟接力也不能证明真实桌面自动新建或 GUI 行为已通过。

发布证据与测量边界见 [v0.6.0 验证说明](benchmarks/v0.6.0-validation.md)。Git 发布、生产部署和全局配置修改仍需用户授权。
