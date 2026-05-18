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
