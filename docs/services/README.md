# Services

This directory contains IT service ownership pages. Each page documents a service the IT department provides, including ownership, SLAs, escalation paths, supported hours, and dependencies.

## Template

Use [templates/service-page.md](../../templates/service-page.md) to create new service pages.

## Required Frontmatter

- `title` -- Name of the service
- `type` -- Must be `service`
- `status` -- `active`, `deprecated`, `draft`, or `needs-review`
- `owner` -- Team or role responsible
- `last_reviewed` -- Date of last review (`YYYY-MM-DD`)

See [schemas/required-fields.yml](../../schemas/required-fields.yml) for the full field list.

## Examples

- [helpdesk.md](helpdesk.md) -- IT Help Desk (fictional example)
