# 集成（Integrations）

此目录包含集成文档页面。每页描述两个或多个系统如何连接、系统间流动的数据、使用的协议以及故障/恢复流程。

## 模板

使用 [templates/integration-page.md](../../templates/integration-page.md) 创建新的集成页面。

## 必填 frontmatter 字段

- `title` — 集成名称
- `type` — 必须为 `integration`
- `status` — `active`、`deprecated`、`draft` 或 `needs-review`
- `owner` — 负责的团队或角色
- `last_reviewed` — 最近评审日期（`YYYY-MM-DD`）
- `systems` — 涉及的系统列表

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 示例

- 暂无。使用上方模板添加你的第一个集成页面。
