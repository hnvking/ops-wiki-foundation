---
title: "校验规则"
type: system
status: draft
owner: "知识库维护团队"
last_reviewed: "2026-11-19"
description: "本文档说明运维知识库文档校验（validate_docs.py）所检查的具体规则，帮助新增/编辑页面时一次通过校验。"
tags:
  - 校验
---

# 校验规则

> 本文档说明知识库文档校验（`scripts/validate_docs.py`）具体校验哪些内容。
> 无论你是通过「新增页面」还是「编辑此页」创建/修改文档，提交前都会经过这套校验；
> 校验不通过时，系统会**阻止保存**（前端拦截 + 后端 422 强制兜底）。

## 校验做什么

校验脚本读取 `schemas/required-fields.yml` 中的规则定义，逐一检查 `docs/` 下每个非 README 的 `.md` 文件，**不通过则整体失败**。它不做拼写、语法、内容的语义审查，只检查**文档元数据（frontmatter）和文件位置**是否合规。

## 校验的核心内容

### 1. 必须有 YAML frontmatter

每个文档开头必须是 `---` 包裹的 YAML 元数据块：

```yaml
---
title: "系统名称"
type: system
status: draft
owner: "负责团队"
last_reviewed: "2026-11-17"
---
```

- 开头第一行必须是 `---`，并存在第二个 `---` 结束。
- 缺少 frontmatter → 报错 `No valid YAML frontmatter found.`
- YAML 解析失败（缩进/引号/冒号错误）→ 同样报错。

### 2. `type` 字段必须存在且合法

`type` 决定该文档属于哪一类，以及后续要求哪些必填字段。

| `type` 值 | 必须所在目录 | 用途 |
|-----------|------------|------|
| `system`  | `docs/systems/` | 系统/应用技术文档 |
| `service` | `docs/services/` | IT 服务文档 |
| `integration` | `docs/integrations/` | 系统间集成文档 |
| `runbook` | `docs/runbooks/` | 应急手册 |
| `faq` | `docs/faqs/<系统>/<表单>/` | 运维问题（必须按系统→表单两级归档） |

- 缺少 `type` → 报错 `Missing 'type' field in frontmatter.`
- `type` 不是上述合法值 → 报错 `Unknown document type`.

### 3. 必填字段必须存在且非空

不同 `type` 有各自的必填字段，**缺一不可**：

| 类型 | 必填字段 |
|------|---------|
| `system` / `service` / `runbook` | `title`、`type`、`status`、`owner`、`last_reviewed` |
| `integration` | 上述全部 **+ `systems`**（列表） |
| `runbook` | 上述全部 **+ `severity`** |
| `faq` | `title`、`type`、`related_system`、`related_form`、`severity`、`resolution`、`last_reviewed` |

- 字段缺失 → 报错 `Missing required field: '<field>'`
- 字符串为空 → 报错 `Required field '<field>' is empty.`
- 列表为空 → 报错 `Required field '<field>' is an empty list.`

### 4. FAQ 必须按「系统 → 表单」归档

`faq` 类型除通用字段外，还有两条硬规则：

1. 路径必须是 `docs/faqs/<系统标识>/<表单标识>/<问题>.md`，不允许直接放在 `docs/faqs/` 或系统目录根部；
2. frontmatter 的 `related_form` 必须等于所在表单目录名。

例如系统 `jiandaoyun-pm` 下表单 `system-access` 的问题，应保存为 `docs/faqs/jiandaoyun-pm/system-access/sso-login-fail.md`，并填写 `related_form: system-access`。

新增问题时，「所属系统」和「所属表单」下拉会自动列出已建好的目录，并据此生成保存路径；没有对应表单时，先建表单目录和 `README.md` 再写问题。

违反时报错 `FAQ 必须放在 docs/faqs/<系统标识>/<表单标识>/<问题>.md` 或 `related_form is ... but the FAQ is in form directory ...`。

### 5. 枚举字段取值必须合法

某些字段的值只能从固定集合中选，否则报错。

**`status`（所有类型通用）**

```
active | deprecated | draft | needs-review
```

**`hosting`（system）**

```
on-prem | cloud | hybrid | unknown
```

**`authentication`（system）**

```
SSO | LDAP | local | none | unknown
```

**`tier`（service）**

```
tier-1 | tier-2 | tier-3 | unknown
```

**`direction`（integration）**

```
one-way | two-way | unknown
```

**`protocol`（integration）**

```
API | SFTP | LDAP | SAML | SCIM | OAuth | webhook | unknown
```

**`severity`（runbook）**

```
critical | high | medium | low | unknown
```

- 非法值 → 报错 `Field '<field>' has invalid value '<value>'. Allowed: ...`

### 6. 日期字段必须符合 YYYY-MM-DD

`last_reviewed` 必须写成 `YYYY-MM-DD` 格式（如 `2026-11-17`）。

- 不符合 → 报错 `Field '<field>' has invalid date format '<value>'. Expected: YYYY-MM-DD`

### 7. 列表字段必须是非空数组

`systems`（integration）、`dependencies`、`tags`、`related_services` 等字段若是列表：

- 不是列表类型 → 报错 `Field '<field>' should be a list, got <type>.`
- 空列表 → 报错 `Field '<field>' is an empty list.`

### 8. 文件必须放在正确目录

文档的 `type` 必须与其所在目录匹配（见第 2 节表格）。例如：

- `type: system` 的文件必须在 `docs/systems/` 下
- `type: runbook` 的文件必须在 `docs/runbooks/` 下

- 放错目录 → 报错 `File is in '<目录>' but type '<type>' should be in '<期望目录>'.`

## 校验的触发时机

| 场景 | 触发校验 | 校验不过能否保存 |
|------|---------|:---:|
| 新增页面「运行校验」 | ✅ 仅预检（临时写入后删除） | — |
| 新增页面「提交」 | ✅ 前端先校验，后端再强制兜底 | **不能保存**（前端拦截 / 后端 422） |
| 编辑此页「保存」 | ✅ 同新增 | **不能保存** |
| 全库「运行校验」 | ✅ 校验 `docs/` 下所有文档 | — |

> 后端强制兜底：即使绕过前端直接调用 `POST /api/files`，服务端也会先校验，不通过返回 **422** 拒绝落盘。

## 校验不通过怎么办

提交前，校验结果会显示在模态框下方的结果区（绿色=通过，红色=不通过并列出具体错误）。根据错误提示逐条修正：

1. **补全/修正 frontmatter**（必填字段、枚举值、日期格式）
2. **检查目录是否放对**（`type` 与目录匹配）
3. **确保列表字段非空**

修正后重新点「运行校验」，通过后再「提交」。

## 参考文件

- 校验脚本：`scripts/validate_docs.py`
- 规则定义：`schemas/required-fields.yml`
- 文档模板：`templates/`
