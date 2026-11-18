# 应急手册（Runbooks）

此目录包含事件响应和操作应急手册。每本手册记录如何检测、响应、升级并解决某一类特定事件。

## 模板

使用 [templates/incident-runbook.md](../../templates/incident-runbook.md) 创建新的应急手册。

## 必填 frontmatter 字段

- `title` — 事件场景名称
- `type` — 必须为 `runbook`
- `status` — `active`、`deprecated`、`draft` 或 `needs-review`
- `owner` — 负责的团队或角色
- `last_reviewed` — 最近评审日期（`YYYY-MM-DD`）
- `severity` — `critical`、`high`、`medium`、`low` 或 `unknown`

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 示例

- [简道云 PM 系统故障应急手册](docs/runbooks/jiandaoyun-pm-outage.md) — 系统不可访问/登录异常/数据异常处置
