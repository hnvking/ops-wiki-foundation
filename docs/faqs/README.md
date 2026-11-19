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
| 简道云 PM 系统 | `docs/faqs/jiandaoyun-pm/` | 11 |

新增时，在「新增页面」对话框将路径填入 `faqs/<系统标识>/<文件名>.md`，并在 frontmatter 的 `related_system` 中填写系统名称。

## 简道云 PM 系统 FAQ 索引

- [简道云 PM 系统 SSO 登录失败](docs/faqs/jiandaoyun-pm/sso-login-fail.md) — 企业微信 SSO 登录失败问题的排查与解决
- [分包付款申请累计计量金额异常](docs/faqs/jiandaoyun-pm/subcontract-payment-cumulative-amount-error.md) — 「6.3.9分包付款申请」累计计量金额虚高
- [NC 接口同步失败](docs/faqs/jiandaoyun-pm/nc-interface-sync-fail.md) — 单据推送 NC 失败（编码/单价/单位不一致）
- [税率字段配置与同步](docs/faqs/jiandaoyun-pm/tax-rate-field-config.md) — 税率字段缺失或未同步
- [流程单删除与回退](docs/faqs/jiandaoyun-pm/flow-delete-and-rollback.md) — 流程缺回退、需删除流程单
- [权限开通与回收](docs/faqs/jiandaoyun-pm/permission-grant-revoke.md) — 查看/导入/发起/编辑权限管理
- [发票登记与进项票流程](docs/faqs/jiandaoyun-pm/invoice-registration-entry.md) — 发票重复登记、无法引用对账流程
- [材料采购合同数据导入](docs/faqs/jiandaoyun-pm/material-contract-import.md) — 合同批量导入模板与培训
- [附加费自动带出](docs/faqs/jiandaoyun-pm/surcharge-auto-fill.md) — 入库单附加费无法自动带出价格
- [供应商扣罚单正负数逻辑](docs/faqs/jiandaoyun-pm/supplier-penalty-sign.md) — 扣罚金额正负数填写约定
- [物资超库存](docs/faqs/jiandaoyun-pm/material-overstock.md) — 库存数据超库存排查
