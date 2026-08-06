# 数据契约

## 输入

采集脚本输出 JSON 数组，或输出包含 `records`、`items` 或 `data` 数组的 JSON 对象。每条记录至少包含：

```json
{
  "firm": "McKinsey",
  "title": "Official article title",
  "source_url": "https://www.mckinsey.com/...",
  "published_date": "2026-01-01",
  "status": "ok",
  "body_text": "正文",
  "tags": ["talent management"]
}
```

`id` 可以由规范化 `source_url` 的 SHA-256 前 16 位生成。`body_chars` 必须由实际 `body_text` 重新计算，不能信任抓取器传入的旧值。

## 规范化规则

- URL 使用小写 scheme 和 host。
- 去掉 fragment、尾部多余 `/`、`utm_*` 和 `gclid` 参数。
- 只接受 HTTPS 和官方 MBB 域名。
- 同一规范化 URL只保留一条记录；正文更长、状态更好、抓取时间更新的记录优先。

## 状态

| 状态 | 含义 | 可否进入可引用正文集 |
| --- | --- | --- |
| `ok` | 正文完整，达到最小字符数 | 可以 |
| `restricted` | 403、登录、付费墙或明确访问限制 | 不可以 |
| `no_body` | 页面可访问，但正文抽取不足 | 不可以 |
| `error` | 网络、解析或未知错误 | 不可以 |

受限与缺正文记录仍需保留来源 URL、标题、HTTP 状态或失败原因，方便下一轮刷新。

## 输出

`manifest.json` 至少记录：构建时间、输入运行目录、记录总数、按 firm 和 status 的计数、无效记录数以及输出文件名。SQLite 数据库应提供 `records` 表和按 firm/status、published_date 的索引；有条件时增加全文索引。
