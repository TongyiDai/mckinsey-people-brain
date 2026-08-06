---
name: mckinsey-people-brain
description: "Use this skill when the user asks to discover, collect, refresh, review, or publish talent-management content from McKinsey, BCG, or Bain official websites, especially when the result should become a traceable agent knowledge base or be written back to Feishu. It defines a two-stage workflow: official-source collection, then quality-controlled database construction."
---

# 麦肯锡人力大脑

> 200W token 挖来的 MBB 人力顾问，10 年工作经验，关注人才、组织、AI 转型。

## 核心工作方式

这套 Skill 把任务拆成两步：

1. **官方来源采集**：发现 MBB 官网候选页面，抓取正文、标题、日期、最终 URL、状态和原始快照。
2. **Agent 数据库构建**：对采集结果做 URL 规范化、去重、质量门禁、主题归类，输出 JSON、CSV 和 SQLite。

飞书回写属于数据库构建之后的发布适配器。它可选、可重跑、可回读，不能成为本地数据库的唯一事实来源。

## 适用范围

当用户要求以下事项时调用本 Skill：

- 查找 MBB（McKinsey、BCG、Bain）官网的人才管理、组织、领导力、技能、绩效、AI 与未来工作内容。
- 更新既有 MBB 内容库，识别新增、更新、受限、正文缺失和重复来源。
- 将经过质量门禁的记录构建为 Agent 可检索数据库。
- 经用户授权，将已验证记录增量写回个人飞书 Base 或 Wiki。

来源范围固定为官方域名：`mckinsey.com`、`bcg.com`、`bain.com` 及其官方地区子域。第三方摘要、搜索结果页、转载页只能作为发现线索，不能进入最终来源登记表。

## 阶段一：采集官方来源

先读取项目来源配置和上一次 manifest。配置至少包含 firm、官方域名、主题关键词、种子 URL、抓取节奏和正文最小字符数。

优先级依次为：官方 sitemap 或专题索引、官方站内搜索结果、已登记 URL 的刷新。发现结果先写入 `targets.json`，再逐条抓取到 `fetched.json`。每次运行使用独立的 `run_id`，保留 `raw/` 原始快照和 `collect-manifest.json`。

抓取规则：

- 使用 HTTPS、保留最终跳转 URL、去掉追踪参数和片段，按规范化 URL 生成稳定 ID。
- 对 429、5xx、网络错误做有限重试和退避；单条失败写入状态，不中断整批运行。
- 遵守 robots、访问频率、登录和付费墙边界。遇到限制时标记 `restricted`，不以搜索摘要或猜测内容补齐正文。
- `ok` 代表正文达到门槛且来源域名、标题、URL均通过校验；`no_body`、`restricted`、`error` 必须保留失败原因。
- 采集脚本只负责抓取和落盘，不在抓取阶段直接写飞书。

已有项目具备站点专用适配器时，复用适配器；新站点先补适配器测试，再纳入批量运行。通用校验和数据库构建使用本 Skill 内的脚本。

## 阶段二：构建 Agent 数据库

对 `fetched.json` 与可选历史 `base-corpus` 合并后运行：

```bash
python3 scripts/build_agent_db.py \
  --run-dir data/runs/20260806-01 \
  --base-corpus data/agent-db/records.json \
  --min-body-chars 800
```

脚本执行以下动作：

- 规范化 URL，去除同一来源的重复记录。
- 以正文质量、标题完整度和抓取时间选择保留记录，记录 `duplicate_of`。
- 校验域名、firm、状态、正文长度、字符计数和标题。
- 归入统一主题：人才战略、组织设计、AI 与未来工作、技能与学习、绩效与激励、People Analytics、员工体验、领导力、劳动力规划。
- 输出 `agent-db/records.json`、`agent-db/source-register.csv`、`agent-db/agent-db.sqlite`、`agent-db/manifest.json`。

质量门禁：

```bash
python3 scripts/validate_records.py data/runs/20260806-01/fetched.json --min-body-chars 800 --strict
```

只有质量门禁通过的记录适合进入可引用正文集。受限和缺正文记录可以进入监控集合，必须带有状态和失败原因。

## 阶段三：飞书增量回写

回写前确认当前 CLI profile、`identity=user`、目标 Base/Wiki 和字段映射。个人飞书与公司飞书属于两个独立租户，不能凭默认 profile 推断目标。

推荐以 `source_url` 的规范化值作为幂等键：

1. 读取目标表字段和现有记录。
2. 建立 URL → record_id 索引。
3. 新 URL 创建记录，已有 URL 更新必要字段，受限记录只更新状态和失败原因。
4. 每批写入后立即按 URL 回读，核对标题、状态、日期、主题和来源链接。
5. 写入失败或身份过期时停止，保留本地构建产物和待写入清单。

不要把 Base 行数、Wiki token、租户 ID、内部 URL、访问令牌、个人路径或原始网页快照提交到 GitHub。

## 记录契约

最小记录字段为：`id`、`firm`、`title`、`source_url`、`final_url`、`published_date`、`status`、`failure_reason`、`body_text`、`body_chars`、`tags`、`themes`、`fetched_at_utc`。

状态只允许：`ok`、`restricted`、`no_body`、`error`。详细规则见 [references/data-contract.md](references/data-contract.md)。

## 代码 Review 清单

- 采集与数据库构建可单独运行，失败可以定位到 `run_id` 和 URL。
- 重跑不会因同一 URL 产生重复记录，输出写入临时文件后原子替换。
- 原始快照、清洗结果、manifest 三者可以相互追溯。
- 公开来源与内部数据分离，仓库内无 token、Cookie、个人路径、租户标识和真实业务数据。
- HTTP 错误、空正文、站点结构变化、数据库重复键和飞书认证失败都有明确结果。
- 测试覆盖 URL 规范化、域名限制、正文门槛、去重优选和失败状态。

## 参考文件

- [data-contract.md](references/data-contract.md)：记录字段、状态、质量门禁和输出结构。
- [source-adapters.md](references/source-adapters.md)：MBB 官方来源发现与站点适配器约定。
- [feishu-publish.md](references/feishu-publish.md)：飞书身份校验、幂等回写和读回要求。
- `scripts/validate_records.py`：独立质量校验脚本。
- `scripts/build_agent_db.py`：独立数据库构建脚本。
