# Runbooks

This directory contains incident response and operational runbooks. Each runbook documents how to detect, respond to, escalate, and resolve a specific type of incident.

## Template

Use [templates/incident-runbook.md](../../templates/incident-runbook.md) to create new runbooks.

## Required Frontmatter

- `title` -- Name of the incident scenario
- `type` -- Must be `runbook`
- `status` -- `active`, `deprecated`, `draft`, or `needs-review`
- `owner` -- Team or role responsible
- `last_reviewed` -- Date of last review (`YYYY-MM-DD`)
- `severity` -- `critical`, `high`, `medium`, `low`, or `unknown`

See [schemas/required-fields.yml](../../schemas/required-fields.yml) for the full field list.

## Examples

- [email-outage.md](email-outage.md) -- Email system outage response (fictional example)
