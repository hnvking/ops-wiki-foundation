# 系统（Systems）

此目录包含系统和应用文档页面。每个页面描述系统的用途、技术详情、负责人、依赖、集成以及备份/恢复信息。

## 模板

使用 [templates/system-application-page.md](../../templates/system-application-page.md) 创建新的系统页面。

## 必填 frontmatter 字段

- `title` — 系统名称
- `type` — 必须为 `system`
- `status` — `active`、`deprecated`、`draft` 或 `needs-review`
- `owner` — 负责的团队或角色
- `last_reviewed` — 最近评审日期（`YYYY-MM-DD`）

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 示例

- [jiandaoyun-pm-system.md](docs/systems/jiandaoyun-pm-system.md) — 简道云项目管理系统
- [AO.md](docs/systems/AO.md) — OA 系统
