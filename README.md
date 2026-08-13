> “Research is formalized curiosity.” — Zora Neale Hurston

<p align="center">
  <img src="https://img.shields.io/badge/Agent%20Skill-agentskills.io-2F6BFF" alt="Agent Skill">
  <img src="https://img.shields.io/badge/license-MIT-3fb950" alt="License MIT">
  <img src="https://img.shields.io/badge/python-%3E%3D3.8-3572A5" alt="Python >=3.8">
  <img src="https://img.shields.io/badge/works%20with-Codex%20|%20Claude%20|%20Cursor%20|%20TRAE-555" alt="Works with major agents">
</p>

# 麦肯锡人力大脑

*200W token 挖来的 MBB 人力顾问，10 年工作经验，关注人才、组织、AI 转型。*

这是一套可复跑的 Codex Skill：从 McKinsey、BCG、Bain 官方网站发现人才管理相关内容，完成正文抽取和质量门禁，再构建带来源、状态、主题和全文索引的 Agent 数据库。飞书回写作为独立发布适配器，支持幂等写入和写后回读。

## Agent 使用契约（运行前必读）

`SKILL.md` 负责总流程，`references/data-contract.md` 负责记录状态，`references/feishu-publish.md` 负责发布边界。Agent 每次运行先确认任务阶段、运行目录、来源范围和是否需要飞书发布。

| 项目 | 规则 |
| --- | --- |
| 触发 | 搜集 MBB 官方人力内容、刷新内容库、构建 Agent 数据库、增量发布到飞书 |
| 首步 | 读取来源配置与上次 manifest，确认 `run_id`、官方域名和正文门槛 |
| 输入 | `targets.json`、`fetched.json`、可选历史 corpus、主题配置和明确的发布目标 |
| 输出 | 带 `source_url`、状态、失败原因、主题和正文的 JSON/CSV/SQLite；发布结果另行报告 |
| 来源边界 | 最终记录只接受 McKinsey、BCG、Bain 官方域名；搜索结果和转载页只作发现线索 |
| 读写 | 采集和构建默认写本地运行产物；飞书写入需要用户授权、目标确认和 dry-run |
| 身份边界 | 个人飞书与公司飞书分开核验；不提交 Base/Wiki 标识、租户信息、Token 或原始快照 |
| 降级 | 受限、无正文、HTTP 错误和认证失败保留状态与原因，不用摘要或猜测补正文 |
| 验证 | 先过记录质量门禁，再按 `source_url` 幂等写入；每批写入后按 URL 回读 |

当前版本的事实源是本地数据库。飞书发布完成与否，以写入后的实际回读为准。

<p align="center"><img src="assets/boards/01-collection-to-db.svg" alt="官方来源经过质量门禁后进入 Agent 数据库" width="960"></p>

## 解决什么问题

长期运行的人力研究，核心风险集中在来源混杂、正文缺失、重复抓取、内容不可追溯和回写重复。Skill 将官方来源采集、数据库构建、飞书发布拆开，每一步都留下可检查的运行产物。

<p align="center"><img src="assets/boards/02-quality-gates.svg" alt="三层门禁决定资料能否被引用" width="960"></p>

## 快速开始

将本目录放进 Codex 的 skills 目录，或在已加载本 Skill 的任务中直接调用：

```text
$mckinsey-people-brain
```

采集阶段由项目内的 MBB 站点适配器负责，统一生成 `targets.json`、`fetched.json`、`raw/` 和 `collect-manifest.json`。本仓库提供通用的质量校验和数据库构建脚本：

```bash
python3 scripts/validate_records.py data/runs/20260806-01/fetched.json --min-body-chars 800 --strict
python3 scripts/build_agent_db.py \
  --run-dir data/runs/20260806-01 \
  --base-corpus data/agent-db/records.json \
  --min-body-chars 800
```

构建结果位于 `agent-db/`：`records.json`、`source-register.csv`、`agent-db.sqlite`、`manifest.json`。采集器可以替换，记录契约和下游格式保持稳定。

## 设计原则

- 只把 MBB 官方域名作为最终来源；搜索结果和转载页只能作为发现线索。
- `source_url` 经过规范化后作为稳定 ID 和幂等键。
- `ok`、`restricted`、`no_body`、`error` 代表不同证据状态，受限内容不能用猜测补齐。
- 原始快照、清洗记录和数据库通过 `run_id`、manifest、source URL 连接。
- 本地数据库是事实来源，飞书发布必须经过用户身份确认、dry-run 和写后回读。

<p align="center"><img src="assets/boards/03-feishu-idempotency.svg" alt="source_url 让飞书回写可重跑" width="960"></p>

## 内容主题

默认主题包括人才战略与组织设计、AI 与未来工作、技能与学习、绩效与激励、People Analytics、员工体验与文化、领导力与管理、劳动力规划与招聘。主题用于检索和聚合，引用仍需回到原始来源 URL。

<p align="center"><img src="assets/boards/04-evidence-loop.svg" alt="三类产物组成证据闭环" width="960"></p>

## 目录

```text
SKILL.md                         Skill 工作流与边界
config.example.json              脱敏后的来源配置示例
references/data-contract.md      记录与状态契约
references/source-adapters.md    MBB 站点适配器约定
references/feishu-publish.md     飞书发布安全规则
references/runtime.md            Agent 运行时契约
scripts/validate_records.py      独立质量校验
scripts/build_agent_db.py        JSON / CSV / SQLite 构建
scripts/doctor.sh                安全的本地运行检查
assets/boards/                   Geometry Blue 语义图示及源描述
```

## 安全边界

仓库不包含网页原始快照、个人飞书数据、Base/Wiki 标识、访问令牌、Cookie、租户信息或本地路径。运行时配置应通过私有项目文件、环境变量或凭据管理器注入。

详细流程见 [SKILL.md](SKILL.md)。
