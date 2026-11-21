# ops-wiki-foundation

A Markdown-first, Git-backed operational wiki foundation for IT documentation.

## Purpose

This repository provides a structured, ready-to-fork foundation for documenting IT service ownership, system inventories, integration maps, escalation paths, SLAs, and incident runbooks.

It is designed for **humans first** -- clear templates, consistent frontmatter, and readable Markdown -- with a structure that also supports AI coding agents and future RAG workflows.

## Getting Started (Make It Your Own)

This repo is meant to be forked and customized for your organization. Here's how:

### 1. Fork or clone the repo

```bash
# Option A: Fork on GitHub, then clone your fork
git clone https://github.com/YOUR-ORG/ops-wiki-foundation.git
cd ops-wiki-foundation

# Option B: Clone directly and set your own remote
git clone https://github.com/decyphered/ops-wiki-foundation.git
cd ops-wiki-foundation
git remote set-url origin https://github.com/YOUR-ORG/ops-wiki-foundation.git
```

### 2. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

Requires **Python 3.9+**. The only dependency is PyYAML.

### 3. Delete the fictional example pages

The `docs/` directories ship with fictional example pages so you can see the format. Once you're comfortable, delete them and start fresh:

```bash
# Remove all example docs (keeps the README.md in each directory)
find docs -name '*.md' ! -name 'README.md' -delete
```

Or keep them as reference and add your own alongside them.

### 4. Create your first real page

Pick a system or service you know well and start there:

```bash
# Copy a template
cp templates/system-application-page.md docs/systems/my-system.md

# Edit the file -- replace all UPPERCASE_PLACEHOLDERS and "unknown" values
# The template has an instruction comment at the top to guide you
```

**Frontmatter tips:**

- Set `status` to `draft` while you're writing, then change to `active` when it's ready.
- Set `last_reviewed` to today's date (`YYYY-MM-DD` format).
- Set `owner` to a team or role name, not a person's name.
- See `schemas/required-fields.yml` for all valid field values.

### 5. Validate your work

```bash
python3 scripts/validate_docs.py
```

The validator checks required fields, allowed values (e.g., `status` must be `active`, `deprecated`, `draft`, or `needs-review`), date formats, and that files are in the correct directory for their type.

A GitHub Actions workflow (`.github/workflows/validate.yml`) is also included so validation runs automatically on every push and pull request that touches `docs/`, `schemas/`, or `scripts/`.

### 6. Customize for your organization

Things you'll likely want to change:

- **`schemas/required-fields.yml`** -- Add or modify `field_constraints` to match your org's vocabulary (e.g., add `tier-4` to service tiers, add new protocol types).
- **`templates/`** -- Adjust section headings and prompts to match what your team actually documents.
- **`docs/*/README.md`** -- Update the descriptions and examples list as you add real pages.
- **`AGENTS.md`** -- Update the data boundary rules and project description to match your org.
- **`LICENSE`** -- Replace with your organization's license if needed.

### 7. Suggested order for documenting your environment

You don't need to document everything at once. A practical order:

1. **Systems** -- Start with the 5-10 systems your team touches most. These are the foundation that services, integrations, and runbooks reference.
2. **Services** -- Document the IT services your team provides (help desk, network support, etc.). Link to the systems they depend on.
3. **Integrations** -- Document how your systems connect. SSO, data syncs, API integrations. Link to the systems on both ends.
4. **Runbooks** -- Write runbooks for your most common or most critical incidents. Link to the affected services and systems.

### Quick reference: Document types

| Type | Directory | Template | Use for |
|------|-----------|----------|---------|
| `service` | `docs/services/` | `templates/service-page.md` | IT services your team provides to users |
| `system` | `docs/systems/` | `templates/system-application-page.md` | Applications, platforms, and infrastructure |
| `integration` | `docs/integrations/` | `templates/integration-page.md` | Data flows and connections between systems |
| `runbook` | `docs/runbooks/` | `templates/incident-runbook.md` | Step-by-step incident response procedures |

## Data Boundary

**This repository must never contain:**

- Real student data or personally identifiable information (PII)
- Real staff data (names, emails, phone numbers)
- Credentials, API keys, tokens, or secrets
- Private ticket contents or internal security details
- Vendor contracts or confidential agreements
- Unsanitized organizational information

All example pages use fictional names, organizations, and details. When documenting real systems, use role titles instead of personal names where possible, and never commit sensitive data.

## Repository Structure

```
ops-wiki-foundation/
├── README.md                    # This file
├── AGENTS.md                    # AI agent instructions (single source of truth)
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT license
├── .gitignore
├── requirements.txt             # Python dependencies (Python 3.9+, minimal)
├── .cursorrules                 # Cursor AI agent rules
├── .clinerules                  # Cline AI agent rules
├── .windsurfrules               # Windsurf AI agent rules
├── .cursor/
│   └── rules/
│       └── agents.mdc           # Cursor MDC rules
├── .github/
│   ├── copilot-instructions.md  # GitHub Copilot instructions
│   └── workflows/
│       └── validate.yml         # CI — validates docs on push/PR
├── schemas/
│   └── required-fields.yml      # Required frontmatter fields & constraints
├── scripts/
│   ├── validate_docs.py         # Validate frontmatter against schemas
│   ├── export_for_rag.py        # Export docs to JSON for RAG pipelines
│   └── lib/                     # Shared Python utilities
│       ├── __init__.py
│       └── frontmatter.py       # Frontmatter parsing & repo-root helpers
├── templates/                   # Markdown templates (one per doc type)
│   ├── service-page.md
│   ├── system-application-page.md
│   ├── integration-page.md
│   └── incident-runbook.md
└── docs/                        # Documentation pages
    ├── services/                # IT service ownership pages
    ├── systems/                 # System and application pages
    ├── integrations/            # Integration documentation
    └── runbooks/                # Incident response runbooks
```

## Usage

### Creating a New Page

1. Copy the appropriate template from `templates/`.
2. Fill in the YAML frontmatter fields (replace placeholders and `"unknown"` values).
3. Replace placeholder content with real documentation.
4. Save the file in the correct `docs/` subdirectory.
5. Run the validation script to check your work.

### Validating Documentation

```bash
python3 scripts/validate_docs.py
```

The validator checks that every Markdown file in `docs/` has the required frontmatter fields defined in `schemas/required-fields.yml`. It also validates enum values (e.g., `status`, `severity`), date formats (`YYYY-MM-DD`), list fields, and correct directory placement.

### Exporting for RAG

```bash
python3 scripts/export_for_rag.py
```

This exports all documentation pages to a JSON file in `exports/` for use in future RAG (retrieval-augmented generation) pipelines. The export format is designed to be simple and tool-agnostic.

## AI Agent Support

This repository includes instruction files for multiple AI coding tools so agents can help you write and maintain documentation:

| File | Tool |
|------|------|
| `AGENTS.md` | OpenCode, general reference (single source of truth) |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.cursorrules` | Cursor |
| `.cursor/rules/agents.mdc` | Cursor (MDC rules) |
| `.clinerules` | Cline |
| `.windsurfrules` | Windsurf |

All tool-specific files reference `AGENTS.md` as the single source of truth. You can use any of these AI tools to help create new pages, fill in templates, and maintain documentation.

## Future AI/RAG Direction

This repository is structured to support future AI workflows:

- **Consistent YAML frontmatter** makes documents machine-parseable.
- **The export script** produces JSON suitable for embedding and retrieval.
- **The schema file** defines what metadata each document type must have, including allowed values.

Future work may include:

- Local embedding generation and vector search
- AI-assisted document drafting from templates
- Automated freshness checks and review reminders
- MCP tool integration for agent-based workflows

These features are **not built yet** and are out of scope for the initial version.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

Quick start:

1. Use the templates. Do not invent new frontmatter fields without updating the schema.
2. Run `python3 scripts/validate_docs.py` before committing.
3. Keep all examples fictional and sanitized.
4. Review the data boundary rules above before adding any new content.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

# 整体思路方案：IT 运维知识库闭环（中文）

> 本节是本项目在实际落地中的完整设计说明：如何把「企业微信智能表格采集」与「本 Git 知识库」联动，并进一步接入 WeKnora + 企微 Agent 形成可消费、可回流的闭环。方案的核心原则是 **单向数据流 + 人工定稿权威 + 只读消费**，任何环节都不允许 AI 反向覆盖人工确认过的内容。

## 1. 为什么要分两层：表格负责采集，Git 负责定稿

这两者不是重复，而是上下游关系：

| 层 | 载体 | 职责 | 特点 |
| --- | --- | --- | --- |
| 采集层 | 企微智能表格「PM运维知识库 → PM运维知识卡」 | 大圆 AI 每天总结企微聊天，把「提问—处理—结论」写入表格；人工在此审核 | 高吞吐、结构化、便于筛选统计 |
| 定稿层 | 本仓库（`docs/faqs/`） | 审核通过的卡片发布为 FAQ Markdown，人工修订后成为权威知识 | Markdown-first、Git 版本化、可检索、AI 友好 |
| 消费层 | WeKnora（RAG）+ 企微 Agent | 把定稿知识做成可问答的知识库，员工在企微里直接提问 | 只读消费，带来源溯源 |

数据流是**单向**的：

```
企微聊天记录
   │ 大圆 AI 每日总结写入
   ▼
企微智能表格（采集/审核台）
   │ sync_from_wecom.py（增量 + 冲突保护）
   ▼
本 Git 仓库 FAQ（人工定稿权威源）
   │ export_for_rag.py → JSON
   ▼
WeKnora 知识库（只读消费）
   │ MCP / API
   ▼
企微 Agent → 员工问答（回答带 source_card_id 溯源）
   │ 人发现答错 → 回到本仓库修订文档
   └──────────────► 重新导出 → 增量喂回 WeKnora（闭环）
```

**关键约定**：WeKnora 只做只读消费，**绝不反向写回 Git 仓库**。人工在本仓库修订后的文档才是权威版本。

## 2. 为什么不上 PostgreSQL

本项目的灵魂是 **Markdown-first + Git-backed**：文档本身就是唯一数据源（single source of truth）。

- 几百到几千篇 FAQ，用纯文件 + Docsify 全站搜索 + RAG 索引完全够用。
- 引入 PG 会立刻制造「谁是唯一数据源」的难题：文件和数据库双写，就要处理一致性、同步、冲突，运维成本远超收益。
- 需要结构化统计（复用次数、满意度、审核状态）时，**留在企微表格**即可——它本就是为结构化字段设计的。
- 若将来确实需要轻量索引，SQLite 也比 PG 更契合本项目「最小依赖」的原则。

结论：**当前阶段不需要 PostgreSQL**。

## 3. 表格字段 → FAQ 文档映射

| 表格字段 | FAQ 位置 |
| --- | --- |
| 关键词/摘要 | `title` / `description` |
| 问题原话（脱敏后） | 正文「问题描述」 |
| 根因分类 + 业务规则与判断逻辑 | 正文「原因分析」 |
| 处理结果一句话 + 标准操作步骤 | 正文「解决方案」 |
| 注意事项/风险提示 | 正文「预防措施」 |
| 影响范围说明/分类 | 正文「影响范围」+ `severity` |
| 模块 | `related_system`（简道云 PM 系统 / OA 系统） |
| 涉及表单名称 | `related_form`（映射到 8 个表单目录） |
| 标签 | `tags` |
| 处理日期 | `last_reviewed` |
| 卡片编号 | `source_card_id`（溯源锚点） |

`source_card_id` 是连接两层的主键：WeKnora 回答时带上它，员工点一下就能直达原卡；同步脚本也用它定位文档，而不是靠文本模糊匹配。

## 4. 沉淀类型分流

不是所有卡片都值得进仓库：

- **B 类（新问题，值得沉淀）** → 主体，审核通过后发布。
- **C 类（一次性，不沉淀）** → 不导入，避免仓库变成聊天记录堆。表格中记为「不适用」。
- **A 类（已有卡引用）** → 更新已有 FAQ 页面，而非新建。
- **结论未定的卡片** → 暂挂，不写成「已解决」的正式文档。

表格「状态」字段作为发布闸门：只有 **已发布 / 已审核** 的 B 类卡片才会被同步脚本处理；待审核、不适用的不会进入仓库。当前 277 条状态已补齐（已发布 153 / 待审核 69 / 不适用 55）。

## 5. 脱敏红线（不可协商）

项目 `AGENTS.md` / `CONTRIBUTING.md` 三处硬性规定：不得写入真实人名、工单内容、内部信息。因此导入时必须：

- 真实人名 → 岗位角色：提问人写「业务同事」，处理人写「IT 运维组」。
- 单据编号（如 `PMCLJXFP-202609-0036`）→ 不写入正文，或替换为 `[单据编号]`。
- 图片占位标记 `(huangn)` 英文账号、聊天时间戳、转发/引用标记 → 全部清除。
- 无依据的字段留空，不推测、不编造。

同步脚本 `scripts/sync_from_wecom.py` 内置这套脱敏逻辑，生成的每篇文档都经过处理。

## 6. 增量同步机制（核心）

`scripts/sync_from_wecom.py` 解决的关键矛盾是：**人在仓库里改过的文档，下次同步不能被表格原样覆盖**。

机制设计：

- **主键**：卡片编号（`source_card_id`），唯一识别一张卡。
- **`content_hash`**：表格关键字段的哈希。重算对比，变了才算「表格侧有更新」。
- **`generated_hash`**：生成时正文的哈希。若当前正文哈希 ≠ 此值，说明人改过正文。
- **冲突保护**：检测到人工修改 → 跳过并报告，**绝不覆盖**。仓库里人工定稿的内容永远优先。
- **闸门**：只处理 B 类 + 状态「已发布/已审核」。
- **基线建立**：首次同步时，对已存在但无 hash 的旧文档，仅追加 hash 字段，正文原样保留。
- **幂等**：内容未变的卡片直接跳过，重复运行结果一致。

每次同步输出四类报告：**新增 / 更新 / 冲突跳过 / 未变更**。

## 7. 目录导航：扁平化 + 搜索

FAQ 的物理目录结构（8 个表单目录）不动——schema、校验、后端都依赖它。但**导航呈现**做扁平化：

- 侧边栏只保留 8 个表单目录，单篇 FAQ 不进深树（避免「材料入库单」下平铺 60+ 篇）。
- 每个表单的 `README.md` 升级为索引页，列出该目录下所有 FAQ（链接 + 一句话摘要）。
- 查找单篇靠两条路：① Docsify 全站搜索（浏览）；② `source_card_id` 直达锚点（AI 回答给出来源后人点过去）。
- 统计数字由脚本生成，不再手写，避免失真。

## 8. 消费与反馈闭环

- **喂给 WeKnora**：`python scripts/export_for_rag.py` 导出 `exports/docs_export.json`（170 篇，含 `source_card_id`）。导入 WeKnora 时以此作为文档 ID，回答时回传溯源编号。
- **人改完重新喂**：修订文档 → 重跑导出 → WeKnora 按 `source_card_id` 增量删旧导新，不必全量重建。
- **反馈回流到表格**：表格预留「复用次数」「满意度评分」字段。Agent 每次引用某卡片回答后给该卡复用次数 +1、收集满意度；每周筛出「低满意度/高复用」的卡片人工复核。反馈只回流到表格，**不直接改文档**。

## 9. 日常运维命令

```bash
# 1) 从企微表格导出最新数据（需 wecom-cli，且已授权）
wecom-cli smartsheet records query \
  --docid 's3_AfsAUAYsANQCNg6CtWWh8RnK0zr3K' \
  --sql 'SELECT RECORD_ID, `卡片编号`, `关键词/摘要`, `问题原话`, `处理结果一句话`, `业务规则与判断逻辑`, `标准操作步骤`, `注意事项/风险提示`, `根因分类`, `关键词/摘要`, `标签`, `适用系统/流程`, `影响范围说明`, `影响范围分类`, `涉及表单名称`, `模块`, `沉淀类型`, `状态`, `处理日期` FROM `PM运维知识卡` LIMIT 500' \
  -o export.json

# 2) 增量同步（先 dry-run 看报告，再 --apply 写入）
python scripts/sync_from_wecom.py --input export.json --report sync_report.json
python scripts/sync_from_wecom.py --input export.json --apply --report sync_report.json

# 3) 校验文档
python scripts/validate_docs.py

# 4) 导出给 RAG / WeKnora
python scripts/export_for_rag.py

# 5) 本地预览（后端同源托管 Docsify + 编辑 API）
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
# 浏览器打开 http://localhost:8000
```

**注意**：直接手写新增 `.md` 文件时，侧边栏 `_sidebar.md` 不会自动更新。要么通过网页「编辑此页」按钮新建（后端自动注册导航），要么运行导航注册脚本补注册。

## 10. 三阶段落地路线

1. **阶段一（已完成）**：把表格内容做对——脱敏、字段映射、目录归类、校验通过、可导出；实现增量同步脚本并试跑验证冲突保护。
2. **阶段二**：补反馈闭环——利用「复用次数/满意度」字段做定期复核提醒；导航扁平化 + 索引页升级。
3. **阶段三**：接 WeKnora——导入导出 JSON，暴露 MCP/API 给企微 Agent，实现员工问答 + 溯源 + 回流。

阶段性成果均已通过 `validate_docs.py`（0 错误）与 `export_for_rag.py`（170 篇）验证。
