---
title: "Ticket Tracker"
type: system
status: active
owner: "Service Desk Team"
last_reviewed: "2026-05-17"
description: "Web-based IT ticketing system used for incident, request, and change management."
vendor: "Fictional Vendor Inc."
hosting: cloud
authentication: SSO
dependencies:
  - "Identity Provider"
  - "Email System"
  - "Asset Management"
tags:
  - ticketing
  - itsm
  - support
---

# Ticket Tracker

## Overview

Ticket Tracker is the primary IT service management (ITSM) platform for Fictional Unified School District (FUSD). It handles incident tickets, service requests, change requests, and asset tracking. All IT support interactions are logged here.

> **Note:** All names, vendors, and details in this page are fictional examples.

## Technical Details

| Field            | Value                        |
|------------------|------------------------------|
| Vendor           | Fictional Vendor Inc.        |
| Version          | 4.2 (fictional)             |
| Hosting          | Cloud (vendor-hosted SaaS)   |
| Authentication   | SSO via district IdP         |
| URL / Access     | https://tickets.example.com  |

## Owner / Support

| Role              | Name / Team                  |
|-------------------|------------------------------|
| System owner      | Service Desk Team            |
| Vendor support    | Fictional Vendor Inc. support portal |
| Internal support  | Systems Administration Team  |

## Dependencies

- Identity Provider (SSO authentication)
- Email System (ticket notifications)
- Asset Management database (linked records)

## Integrations

- SSO integration with district Identity Provider (see [SSO Integration](../integrations/sso-identity-provider.md))
- Email notifications via district mail relay

## Backup & Recovery

- **Backup frequency:** Vendor manages daily backups (SaaS)
- **Recovery process:** Contact vendor support for data restoration
- **RPO / RTO:** RPO 24 hours / RTO 4 hours (per vendor SLA)

## Related Pages

- [IT Help Desk Service](../services/helpdesk.md)
- [Identity Provider](identity-provider.md)
- [Email System](email-system.md)
- [SSO Identity Provider Integration](../integrations/sso-identity-provider.md)

## Change Log

| Date       | Author             | Summary                       |
|------------|--------------------|-------------------------------|
| 2026-05-17 | Wiki Contributor   | Initial fictional example     |
