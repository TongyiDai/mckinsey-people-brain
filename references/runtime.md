# Agent runtime contract

这份文件补充运行时判断。记录字段、状态值和飞书写入细节分别以 `data-contract.md`、`feishu-publish.md` 为准。

## 触发与首步

用户要求发现、采集、刷新、审阅或发布 MBB 人力内容时触发。首步读取来源配置和最近一次 manifest，生成独立 `run_id`，确认官方域名、主题、正文最小字符数和发布目标。

## 阶段边界

1. 采集阶段只发现和抓取官方来源，输出 `targets.json`、`fetched.json`、`raw/` 和 manifest。
2. 构建阶段只处理通过字段、域名、正文和状态校验的记录，输出 JSON、CSV、SQLite 和 manifest。
3. 发布阶段可选。只有用户明确授权并完成 profile、目标 Base/Wiki、dry-run 和字段映射核验时才写飞书。

## 失败处理

- 429、5xx 和网络错误有限重试；单条失败保留 `error` 和原因。
- 付费墙、登录限制或正文缺失保留 `restricted` / `no_body`，不从搜索摘要补写。
- 重复 URL 进入 `duplicate_of` 关系，不新增重复记录。
- 飞书身份、权限或读回失败时停止发布，保留本地产物和待写清单。

## 验证要求

采集后运行 `scripts/validate_records.py`，构建后检查 manifest、去重结果和数据库记录。飞书写入后按规范化 `source_url` 回读标题、状态、日期、主题和来源链接。没有证据的记录只能进入监控集合，不能进入可引用正文集。
