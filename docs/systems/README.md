# Systems

This directory contains system and application documentation pages. Each page describes a system's purpose, technical details, ownership, dependencies, integrations, and backup/recovery information.

## Template

Use [templates/system-application-page.md](../../templates/system-application-page.md) to create new system pages.

## Required Frontmatter

- `title` -- Name of the system
- `type` -- Must be `system`
- `status` -- `active`, `deprecated`, `draft`, or `needs-review`
- `owner` -- Team or role responsible
- `last_reviewed` -- Date of last review (`YYYY-MM-DD`)

See [schemas/required-fields.yml](../../schemas/required-fields.yml) for the full field list.

## Examples

- [ticket-tracker.md](ticket-tracker.md) -- IT ticketing system (fictional example)
- [email-system.md](email-system.md) -- District email platform (fictional example)
- [identity-provider.md](identity-provider.md) -- Central identity and SSO provider (fictional example)
