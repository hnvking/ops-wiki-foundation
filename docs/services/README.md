# 服务（Services）

此目录包含 IT 服务负责人页面。每页记录 IT 部门提供的一项服务，包括负责人、SLA、升级路径、支持时间和依赖。

## 模板

使用 [templates/service-page.md](../../templates/service-page.md) 创建新的服务页面。

## 必填 frontmatter 字段

- `title` — 服务名称
- `type` — 必须为 `service`
- `status` — `active`、`deprecated`、`draft` 或 `needs-review`
- `owner` — 负责的团队或角色
- `last_reviewed` — 最近评审日期（`YYYY-MM-DD`）

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 示例

- [项目管理服务](jiandaoyun-pm-service.md) — 基于简道云 PM 系统
