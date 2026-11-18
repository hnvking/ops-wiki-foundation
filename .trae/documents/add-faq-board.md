# 新增「运维问题解答（FAQ）」板块实现计划

## Context（背景）

用户已有「系统(systems)、服务(services)、集成(integrations)、应急手册(runbooks)」四个顶级分类，现需新增一个大板块「运维问题解答」来记录各系统运维问题的解答，并**按系统分类记录**。

用户已确认：
- **组织结构**：独立顶级分类 `docs/faqs/`，每个系统一个子目录（如 `docs/faqs/jiandaoyun-pm/`），FAQ 按系统归档，侧边栏独立入口。
- **FAQ 记录字段**：问题+解答（核心正文）、所属系统（frontmatter 字段）、严重级别/影响、解决状态。

本计划新增 `faq` 文档类型，完整接入 schema、模板、前端插件、后端导航注册、侧边栏，并建一个示例验证按系统子目录可行。

## 关键设计决策（已论证）

1. **字段命名**（避免与现有语义冲突）：
   - 所属系统 → `related_system`（字符串，必填，自由文本，不设 enum，系统名开放集合）
   - 严重级别 → **复用 `severity`**（enum: critical/high/medium/low/unknown，runbook 已定义，前端 FIELD_DEFS 已存在）
   - 解决状态 → **`resolution`**（enum: open/in-progress/resolved/unknown，不复用 `status`，status 是文档生命周期语义）
   - `owner` 放 optional，`last_reviewed` 保留必填（AGENTS.md 统一要求）

2. **系统子目录不建 README.md**：`docs/faqs/<system>/` 只放 FAQ 的 .md。原因：前端 `analyzeRoute()` 对 `docs/faqs/<system>/README.md` 会判为 mode="doc"（普通文档页）而非索引页，改通用逻辑风险大。系统归属靠 frontmatter 的 `related_system` + README 分组表格体现。零改动兼容现有路由/校验/注册。

3. **新增页面路径预填**：保持现有 `category + "/"`（即 `faqs/`），用户手动补系统目录和文件名。README 中明确「文件放在 `faqs/<系统名>/` 下」。

4. **后端 `register_new_page` 兼容二级子目录**（已验证）：`_sidebar.md` 注册按扁平子链接插入父项下，README 在「## 示例」区追加，均不受二级目录影响。前提：新增 `CATEGORY_LABELS["faqs"]`。

5. **目录校验零改动**：`validate_docs.py` 用 `startswith("docs/faqs")` 前缀匹配，二级子目录天然通过；`docs/faqs/README.md` 被排除不校验。

## 改动清单

### A. `schemas/required-fields.yml`（修改）
在 `document_types:` 下、`runbook` 后追加 `faq` 类型：

```yaml
  faq:
    description: "Operational FAQ entries grouped by system"
    directory: "docs/faqs"
    template: "templates/faq-page.md"
    required:
      - title
      - type
      - related_system
      - severity
      - resolution
      - last_reviewed
    optional:
      - description
      - owner
      - tags
    field_constraints:
      last_reviewed:
        type: date
        format: "YYYY-MM-DD"
      severity:
        type: enum
        values: [critical, high, medium, low, unknown]
      resolution:
        type: enum
        values: [open, in-progress, resolved, unknown]
```

### B. `templates/faq-page.md`（新建）
仿 `templates/incident-runbook.md` 风格：顶部说明注释 + frontmatter 示例 + 正文结构。
frontmatter 示例字段：`title / type: faq / related_system / severity / resolution / last_reviewed / description / owner / tags`。
正文 `##` 节：问题描述、影响范围、原因分析、解决方案、预防措施、相关页面、变更记录。

### C. `docs/faqs/README.md`（新建，分类索引页）
仿 `docs/runbooks/README.md` 结构：简介（按系统归档，每系统一子目录 `docs/faqs/<系统名>/`）、`## 模板`、`## 必填 frontmatter 字段`（列出 title/type/related_system/severity/resolution/last_reviewed 及 enum 值）、`## 按系统归档` 分组表格、`## 示例` 列出示例链接。

### D. `docs/faqs/jiandaoyun-pm/sso-login-fail.md`（新建示例）
基于简道云 PM 系统 SSO 登录失败问题：
- frontmatter：`title: 简道云 PM 系统 SSO 登录失败`、`type: faq`、`related_system: 简道云 PM 系统`、`severity: high`、`resolution: resolved`、`last_reviewed: 2026-11-18`、`description`、`owner: 数字化创新团队`、`tags: [SSO, 登录]`。
- 正文：问题描述（企业微信扫码后跳转失败/白屏）、影响范围、原因分析（回调地址未同步）、解决方案、预防措施、相关页面（链接 `docs/systems/jiandaoyun-pm-system.md`）、变更记录。
- 全部用虚构值，不写真实凭据。

### E. `docsify-editor-plugin.js`（修改，5 处）
1. `CATEGORY_TYPE`（L154-159）加：`faqs: "faq",`
2. `type` 下拉 options（L164-172）追加：`{ v: "faq", t: "faq（运维问题）" },`
3. `FIELD_DEFS`（L162-222）追加：
   - `related_system`: `{ label: "所属系统 related_system", kind: "text", required: true, help: "问题所属系统，如「简道云 PM 系统」" }`
   - `resolution`: `{ label: "解决状态 resolution", kind: "select", required: true, options: [{v:"open",t:"open（未解决）"},{v:"in-progress",t:"in-progress（处理中）"},{v:"resolved",t:"resolved（已解决）"},{v:"unknown",t:"unknown（未知）"}], help: "问题解决状态" }`
   - `severity` 已存在，直接复用不改。
4. `TYPE_FIELDS`（L225-230）追加：`faq: ["title", "type", "related_system", "severity", "resolution", "last_reviewed", "description", "owner", "tags"],`
5. `buildFrontmatter` 的 keys 数组（L271-274）追加：`"related_system", "resolution"`（关键——否则表单填的这两个字段不会写进 frontmatter，校验会 422）。

### F. `backend/main.py`（修改，1 处）
`CATEGORY_LABELS`（L77-82）加：`"faqs": "运维问题 Faqs",`（`register_new_page`/`unregister_page` 逻辑零改动）。

### G. `_sidebar.md`（修改）
在「应急手册 Runbooks」块后、「校验规则」前加：

```markdown
- [运维问题 Faqs](docs/faqs/README.md)
  - [简道云 PM 系统 SSO 登录失败](docs/faqs/jiandaoyun-pm/sso-login-fail.md)
```

子链接扁平（与 `register_new_page` 自动注册格式一致，避免后续自动插入破坏手动分组）。

## 验证

1. `python scripts/validate_docs.py`（本机用 `python` 非 `python3`，PyYAML 已装）——预期含 `OK docs/faqs/jiandaoyun-pm/sso-login-fail.md`，退出码 0。
2. 后端启动 `python backend/main.py`，确认无导入错误。
3. 功能走查：
   - 打开 `#/docs/faqs/README.md`，确认「➕ 新增页面」出现，type 下拉默认 `faq`，路径预填 `faqs/`，表单含 `related_system / severity / resolution` 必填项。
   - 手动输入 `faqs/jiandaoyun-pm/test-faq.md`，填必填字段，运行校验通过后提交，确认自动注册进 `_sidebar.md` faqs 下与 README「## 示例」区。
   - 打开 `#/docs/faqs/jiandaoyun-pm/sso-login-fail.md`，确认「编辑此页」出现、frontmatter 正确回填、正文可编辑保存。
   - 用错误值（如 `resolution: bad`）保存，确认后端 422 拦截。
4. 删除功能：删除示例 FAQ，确认 `_sidebar.md` 与 README 链接同步移除。
5. 再次 `python scripts/validate_docs.py`，确认无回归。

## 已知小瑕疵（本轮不修）

- `validate-content` 校验新页面时可能残留空目录 `docs/faqs/<system>/`（无害，空目录无 .md 被跳过）。
- 系统名（`related_system` 自由文本）与目录名（如 `jiandaoyun-pm/`）靠 README 分组表格人工映射，不强制自动对应。
