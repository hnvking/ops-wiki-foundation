# AGENTS.md — Instructions for AI Coding Agents

This file provides context and rules for AI coding agents working in this repository. If your tool uses a different instruction file (e.g., `.cursorrules`, `.github/copilot-instructions.md`), those files reference this one as the single source of truth.

## Project Overview

ops-wiki-foundation is a Markdown-first, Git-backed operational wiki for IT documentation. It stores service pages, system inventories, integration maps, and incident runbooks.

All documentation lives in `docs/` as Markdown files with YAML frontmatter. Templates are in `templates/`. Schemas are in `schemas/`. Utility scripts are in `scripts/`.

## Repository Structure

```
templates/            — Markdown templates (one per document type)
docs/services/        — IT service ownership pages
docs/systems/         — System and application pages
docs/integrations/    — Integration documentation
docs/runbooks/        — Incident response runbooks
schemas/              — YAML schemas defining required frontmatter fields
scripts/              — Validation and export utilities (Python 3.9+)
scripts/lib/          — Shared Python utilities (frontmatter parsing, etc.)
```

## Rules for AI Agents

### Data Boundary (Critical)

- **NEVER** include real student data, staff PII, credentials, API keys, tokens, or secrets.
- **NEVER** include real ticket contents, vendor contracts, or internal security details.
- Use fictional names, organizations, and details in all examples.
- Use role titles (e.g., "Service Desk Manager") instead of personal names where possible.
- When a real value is unknown, use `"unknown"`, `"needs-review"`, or `"not-applicable"`.

### Document Standards

- Every Markdown file in `docs/` must have YAML frontmatter with at least the required fields defined in `schemas/required-fields.yml`.
- The `type` field in frontmatter must match one of the document types in the schema: `service`, `system`, `integration`, `runbook`.
- Field values must conform to the `field_constraints` defined in the schema (e.g., `status` must be one of `active`, `deprecated`, `draft`, `needs-review`).
- Use the templates in `templates/` as the starting point for new pages.
- Do not invent new frontmatter fields without updating the schema.
- FAQ pages must live at `docs/faqs/<system>/<form>/<page>.md`; `related_form` is required and must match the form directory name. Never place a FAQ directly in `docs/faqs/` or a system root.

### Markdown Style

- Use ATX-style headings (`#`, `##`, etc.), not Setext-style.
- Use one blank line before and after headings, code blocks, and tables.
- Use `##` for top-level sections within a document (the `# Title` heading is the page title).
- Keep lines under 200 characters where practical; do not hard-wrap prose at a fixed column.
- End every file with a single trailing newline.
- Use `-` (not `*`) for unordered lists.

### Dates and the `last_reviewed` Field

- All dates use `YYYY-MM-DD` format (e.g., `"2026-05-17"`).
- When **creating** a new document, set `last_reviewed` to today's date.
- When **editing** an existing document's content, update `last_reviewed` to today's date.
- When making a trivial fix (typo, formatting) that doesn't change meaning, leave `last_reviewed` as-is.

### Validation

- Run `python3 scripts/validate_docs.py` after making changes to docs.
- All documents must pass validation before committing.
- The validator checks: required fields, enum values, date formats, list fields, and correct directory placement.

### Code Standards

- Scripts require **Python 3.9+** and use minimal dependencies (only PyYAML).
- Always use `python3` (not `python`) to run scripts.
- Shared utilities live in `scripts/lib/`. Import from there instead of duplicating logic.
- Keep scripts readable and well-commented.
- Do not add web frameworks, databases, vector stores, or AI/ML libraries.

### What NOT to Build

- Do not build a chatbot, web app, or API server.
- Do not build a vector database or embedding pipeline.
- Do not build Jira, Confluence, or other SaaS integrations.
- Do not build MCP tools or agent frameworks.
- These are planned for future phases but are out of scope now.

### When Adding New Document Types

1. Add the type definition to `schemas/required-fields.yml`, including `field_constraints`.
2. Create a template in `templates/` with an instruction comment at the top.
3. Create a directory in `docs/`.
4. Add a `README.md` to the new directory.
5. Create at least one fictional example page.
6. Update the directory tree in `README.md`.
7. Run validation to confirm everything works.

### Commit Guidelines

- Write clear, concise commit messages.
- Run validation before committing.
- Do not commit generated files (the `exports/` directory is in `.gitignore`).
