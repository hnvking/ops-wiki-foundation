# 运维问题解答（Faqs）

本目录记录各系统在运维过程中遇到问题的解答。

## 归档规则（强制）

每条 FAQ 必须按 **系统 → 表单** 两级目录归档，路径格式固定为：

`docs/faqs/<系统标识>/<表单标识>/<问题>.md`

- 系统标识与 `docs/systems/` 中的系统一一对应（如 `jiandaoyun-pm`、`oa`）。
- 表单目录在系统目录中预先建好，一个表单一个目录（如 `system-access`、`subcontract-payment`）。
- **禁止**把 FAQ 直接放在 `docs/faqs/` 或系统目录根部；没有对应表单时，先建表单目录再写问题。
- frontmatter 的 `related_form` 必填，值必须等于所在表单目录名。
- 校验脚本会拒绝不符合上述路径与字段要求的 FAQ。

## 模板与字段

使用 [templates/faq-page.md](../../templates/faq-page.md) 创建新的运维问题解答。

必填 frontmatter 字段：`title`、`type`（固定 `faq`）、`related_system`、`related_form`、`severity`、`resolution`、`last_reviewed`。

完整字段列表见 [schemas/required-fields.yml](../../schemas/required-fields.yml)。

## 系统目录

| 系统 | 目录 | 表单数 | FAQ 数 |
|------|------|--------|--------|
| 简道云 PM 系统 | [jiandaoyun-pm](jiandaoyun-pm/README.md) | 8 | 11 |
| OA 系统 | [oa](oa/README.md) | 4 | 0 |

新增表单时：在对应系统目录下新建表单子目录和 `README.md`，并把链接加入该系统的 `README.md` 与 `_sidebar.md`。
