# Integrations

This directory contains integration documentation pages. Each page describes how two or more systems connect, what data flows between them, the protocol used, and failure/recovery procedures.

## Template

Use [templates/integration-page.md](../../templates/integration-page.md) to create new integration pages.

## Required Frontmatter

- `title` -- Name of the integration
- `type` -- Must be `integration`
- `status` -- `active`, `deprecated`, `draft`, or `needs-review`
- `owner` -- Team or role responsible
- `last_reviewed` -- Date of last review (`YYYY-MM-DD`)
- `systems` -- List of systems involved

See [schemas/required-fields.yml](../../schemas/required-fields.yml) for the full field list.

## Examples

- [sso-identity-provider.md](sso-identity-provider.md) -- SSO integration (fictional example)
