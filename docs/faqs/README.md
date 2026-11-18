# 运维问题解答（Faqs）

此目录记录各系统在运维过程中遇到问题的解答。每条 FAQ 按所属系统归档，每个系统使用一个子目录（如 `docs/faqs/<系统名>/`），方便按系统分类浏览和检索。

## 模板

使用 [templates/faq-page.md](../../templates/faq-page.md) 创建新的运维问题解答。

## 必填 frontmatter 字段

- `title` — 问题标题
- `type` — 必须为 `faq`
- `related_system` — 问题所属系统（如「简道云 PM 系统」）
- `severity` — `critical`、`high`、`medium`、`low` 或 `unknown`
- `resolution` — `open`、`in-progress`、`resolved` 或 `unknown`
- `last_reviewed` — 最近评审日期（`YYYY-MM-DD`）

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 按系统归档

每条 FAQ 的正文文件需放在对应系统的子目录下，目录名建议使用系统标识（小写连字符），如：

| 系统 | 子目录 | FAQ 数 |
|------|--------|--------|
| 简道云 PM 系统 | `docs/faqs/jiandaoyun-pm/` | 1 |

新增时，在「新增页面」对话框将路径填入 `faqs/<系统标识>/<文件名>.md`，并在 frontmatter 的 `related_system` 中填写系统名称。

## 示例

- [简道云 PM 系统 SSO 登录失败](docs/faqs/jiandaoyun-pm/sso-login-fail.md) — 企业微信 SSO 登录失败问题的排查与解决
