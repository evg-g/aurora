---
key: "AURORA-2"
title: "Record an audit-log entry when an appointment is cancelled"
status: "in-refinement"
assignee: "evg-g"
---

# AURORA-2: Record an audit-log entry when an appointment is cancelled

## Story

As a clinic admin, I want every appointment cancellation to appear in the audit log, so that I
can see who cancelled which appointment and when.

Today nothing writes to the `audit_log` table, so `GET /api/v1/audit-log` is always empty against
the real API (see `appointments-api/docs/KNOWN_GAPS.md`, "Audit log has no write instrumentation").
This ticket closes that gap for cancellation only. Other actions come later.

## Acceptance criteria

1. When an appointment is cancelled, exactly one audit-log entry is recorded for it, naming the user who cancelled it, the action `appointment.cancelled`, the appointment, and its status before and after.
2. An admin can see that entry through `GET /api/v1/audit-log`, including when filtering by the appointment's id.
3. A cancel request that is refused records no audit-log entry.
