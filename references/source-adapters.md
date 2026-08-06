# MBB 来源适配器

## 发现策略

按 firm 维护独立适配器，统一输出：`firm`、`url`、`discovery_source`、`discovered_at_utc`、`priority`。适配器可以读取 sitemap、专题页或官方站内搜索结果，搜索引擎摘要只能作为线索。

推荐发现词：talent management、people strategy、organization、leadership、skills、learning、performance management、employee experience、workforce planning、artificial intelligence、future of work、people analytics。

## 抓取约定

每个适配器接收一个规范化 URL，返回统一记录。站点专用逻辑只负责请求、跳转、正文选择器、标题、日期、标签和访问状态。以下内容交给公共层：

- URL 规范化和稳定 ID。
- 正文字符计数和质量门禁。
- 去重、主题归类和数据库输出。
- manifest、重跑和增量回写。

### McKinsey

保留官网文章的 canonical URL；解析页面 metadata、正文主体和文章日期。遇到地区站点或语言站点时，记录最终 URL，不把同文不同 URL自动判成独立洞见。

### BCG

优先读取文章 canonical、标题 metadata 和正文主体。页面脚本、推荐卡片、导航、页脚和 Cookie 文案不能混入 `body_text`。

### Bain

优先使用官方洞见或专题文章页。对正文较短的页面标记 `no_body`，保留页面标题和失败原因供刷新。

## 站点变化

解析器失败时保留原始响应、HTTP 状态和选择器版本，进入 review 队列。单个站点结构变化不应阻断其他 firm 的采集。新选择器至少补一条“正文存在”和一条“正文为空”的测试样本。
