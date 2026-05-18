# Contributing to ops-wiki-foundation

Thank you for contributing to this operational wiki. This guide covers the essentials for both human contributors and AI agents.

## Quick Start

1. Copy the appropriate template from `templates/` for your document type.
2. Fill in all YAML frontmatter fields (replace placeholders and `"unknown"` values).
3. Write your content using the section structure from the template.
4. Save the file in the correct `docs/` subdirectory for its type.
5. Run validation: `python3 scripts/validate_docs.py`
6. Commit only if validation passes.

## Document Types

| Type | Directory | Template |
|------|-----------|----------|
| `service` | `docs/services/` | `templates/service-page.md` |
| `system` | `docs/systems/` | `templates/system-application-page.md` |
| `integration` | `docs/integrations/` | `templates/integration-page.md` |
| `runbook` | `docs/runbooks/` | `templates/incident-runbook.md` |

## Data Boundary (Critical)

**Never commit:**

- Real student data, staff PII, or personal names
- Credentials, API keys, tokens, or secrets
- Private ticket contents, vendor contracts, or internal security details

Use fictional names and organizations in all examples. Use role titles (e.g., "Service Desk Manager") instead of personal names.

## Frontmatter Rules

- Every Markdown file in `docs/` must have YAML frontmatter.
- Required fields are defined per type in `schemas/required-fields.yml`.
- Field values must conform to `field_constraints` in the schema (e.g., `status` must be `active`, `deprecated`, `draft`, or `needs-review`).
- All dates use `YYYY-MM-DD` format.
- Set `last_reviewed` to today's date when creating or editing a document.

## Markdown Style

- ATX-style headings (`#`, `##`, etc.)
- One blank line before and after headings, code blocks, and tables
- `##` for top-level sections (the `# Title` is the page title)
- Lines under 200 characters where practical
- End every file with a single trailing newline
- Use `-` (not `*`) for unordered lists

## Validation

Always run before committing:

```bash
python3 scripts/validate_docs.py
```

The validator checks:

- Required fields are present and non-empty
- Enum fields have valid values (e.g., `status`, `severity`, `hosting`)
- Date fields match `YYYY-MM-DD` format
- List fields are non-empty when required
- Files are in the correct directory for their document type

## Adding a New Document Type

1. Add the type definition (with `field_constraints`) to `schemas/required-fields.yml`.
2. Create a template in `templates/` with an instruction comment at the top.
3. Create a directory in `docs/`.
4. Add a `README.md` to the new directory.
5. Create at least one fictional example page.
6. Update the directory tree in `README.md`.
7. Run validation to confirm everything works.

## Code Standards

- Scripts require **Python 3.9+** with only PyYAML as a dependency.
- Always use `python3` (not `python`) to run scripts.
- Shared utilities live in `scripts/lib/`. Import from there instead of duplicating logic.

## What NOT to Build

- No chatbots, web apps, or API servers
- No vector databases or embedding pipelines
- No Jira, Confluence, or other SaaS integrations
- No MCP tools or agent frameworks

These are planned for future phases.
