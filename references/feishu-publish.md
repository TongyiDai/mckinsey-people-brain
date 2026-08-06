# 飞书发布适配器

飞书只接收已经通过本地质量门禁的记录。发布器应支持 dry-run、增量写入和写后读回。

## 发布前

确认：

1. 当前 profile 指向用户要求的租户。
2. 身份为 `identity=user`，且用户 API 可用。
3. 目标 Base/Wiki、字段名和权限已读取确认。
4. 本地 `manifest.json` 与待写入记录数一致。

认证缺失、身份不明、目标表不可读或字段映射不完整时，停止发布并输出待处理清单。不能用机器人身份或历史快照代替当前用户数据。

## 幂等回写

使用规范化 `source_url` 作为幂等键。读取现有记录建立索引后：

- 新 URL：创建记录。
- 已有 URL：更新标题、日期、正文、主题、状态、失败原因和抓取时间等允许更新字段。
- `restricted`、`no_body`、`error`：保留记录并更新状态，不能用空正文覆盖已有有效正文。

每批写入后按 URL 回读，至少核对 URL、firm、title、status 和 themes。输出 created、updated、skipped、failed 四类结果。

## 安全边界

目标 token、Base ID、Wiki space ID、租户信息和访问令牌只能来自运行时配置或环境变量，不能写进 Skill、README、测试数据或提交记录。
