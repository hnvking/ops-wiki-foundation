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
| 简道云 PM 系统 | [jiandaoyun-pm](jiandaoyun-pm/README.md) | 8 | 166 |
| OA 系统 | [oa](oa/README.md) | 4 | 0 |

新增表单时：在对应系统目录下新建表单子目录和 `README.md`，并把链接加入该系统的 `README.md` 与 `_sidebar.md`。

## 按问题类型浏览

FAQ 的物理目录按「系统 → 表单」归档（不变），导航按「问题类型」呈现，与企微表格「问题类型」字段同一口径。侧边栏「5.1 简道云 PM 系统」下已按下列分类展开所有卡片链接：

### 用户操作 FAQ

31 篇。账号登录、菜单操作、单据填写与提交等最终用户可直接处理的问题。分类标签：`problem_type: 用户操作FAQ`。

### 配置与报表

40 篇。字段带出规则、表单视图、台账/报表配置等需要管理员调整配置才能解决的问题。分类标签：`problem_type: 配置与报表`。

### 缺陷与数据问题

36 篇。系统缺陷、数据错误、反写异常等需要技术或数据修复的问题。分类标签：`problem_type: 缺陷与数据问题`。

### 审批流与权限

46 篇。审批节点、流程状态、数据权限与角色授权相关问题。分类标签：`problem_type: 审批流与权限`。

### 系统对接与集成

0 篇（待补充）。简道云与 NC 等外部系统的接口对接问题；目前相关卡片按根因归入上述类别，后续积累后独立成类。分类标签：`problem_type: 系统对接与集成`。

### 其他 / 综合

13 篇。未标注 `problem_type` 的手写文档，以及跨多个类别、暂无法单一归类的内容。

分类统计由 `python scripts/build_sidebar_by_type.py` 从 frontmatter 自动生成；调整分类后重跑该脚本即可同步侧边栏与本页篇数。
