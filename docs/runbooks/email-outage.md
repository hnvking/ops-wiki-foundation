---
title: "Email System Outage"
type: runbook
status: active
owner: "Systems Administration Team"
last_reviewed: "2026-05-17"
description: "Response procedures for a district-wide email system outage."
severity: critical
related_services:
  - "IT Help Desk"
  - "Email System"
tags:
  - email
  - outage
  - critical
---

# Email System Outage

## Summary

This runbook covers the response procedure when the district email system becomes unavailable for all or most users. An email outage is classified as critical because it affects communication for all staff and may impact student-facing services.

> **Note:** All contacts, systems, and procedures in this page are fictional examples.

## Severity

- **Level:** Critical
- **Impact:** All staff and student email is unavailable
- **Affected users:** Approximately 5,000 (all FUSD users)

## Detection

How is this incident detected?

- Automated monitoring alert from uptime checker (fictional)
- Spike in help desk calls and tickets reporting email issues
- Staff reports via phone or walk-in

## Immediate Response

1. Acknowledge the monitoring alert within 15 minutes.
2. Verify the outage is real (not a false alarm) by testing from multiple locations.
3. Open a critical incident ticket in Ticket Tracker.
4. Notify the Systems Administration Team lead.
5. Post an initial status update to the internal status page.

## Escalation Path

| Level   | Contact                          | Method              |
|---------|----------------------------------|---------------------|
| Level 1 | Systems Administration on-call   | Phone / chat        |
| Level 2 | Infrastructure Team Lead         | Phone               |
| Level 3 | IT Director (fictional)          | Phone               |

## Communication

- **Internal notification:** Post to IT staff chat channel and send all-staff notification via backup channel (phone tree or text).
- **User-facing communication:** Update the district status page with estimated time of resolution.
- **Status page update:** Every 30 minutes until resolved.

## Resolution Steps

1. Check email service health dashboard.
2. Verify DNS and MX records are resolving correctly.
3. Check vendor status page for known outages.
4. If vendor-side: open a support case with the email provider and track vendor ETA.
5. If internal: restart mail relay services, check firewall rules, verify certificates.
6. Confirm service restoration by sending test emails from multiple accounts.
7. Update the status page to "resolved."

## Post-Incident

- [ ] Conduct post-incident review within 48 hours
- [ ] Update this runbook with lessons learned
- [ ] File follow-up tickets for any root-cause fixes
- [ ] Send post-incident summary to IT leadership

## Related Pages

- [IT Help Desk Service](../services/helpdesk.md)
- [Email System](../systems/email-system.md)
- [SSO Identity Provider Integration](../integrations/sso-identity-provider.md)

## Change Log

| Date       | Author             | Summary                       |
|------------|--------------------|-------------------------------|
| 2026-05-17 | Wiki Contributor   | Initial fictional example     |
