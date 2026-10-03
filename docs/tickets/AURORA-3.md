---
key: "AURORA-3"
title: "Do not report success when the database did not save the change"
status: "draft"
assignee: ""
---

# AURORA-3: Do not report success when the database did not save the change

## Story

As a clinic user, I want the API to tell me the truth about whether my change was saved, so that I
never act on a change that the database does not have.

Today `get_session` (`appointments-api/src/appointments_api/db.py:40`) commits in the exit of a
yield dependency, and FastAPI 0.141.1 runs that exit after the response is sent. So when the
COMMIT fails, the client has already received a success response (for example 200 with a
`CANCELLED` body), while the database keeps the old state. This affects every write endpoint. It
was found while proving AURORA-2 (see `test_ac1_data_failed_cancel_commit_leaves_no_audit_row` in
appointments-api#19).

Related, and not settled here: webhooks are published before the commit, so a failed commit can
still send an event for a change that was not saved.

## Acceptance criteria

1. When a write request's database commit fails, the client gets an error response, never a success response.
2. After a write request returns a success response, a new read of the same resource shows the change.
3. When a commit fails, nothing from that request is saved: neither the change itself nor its audit-log entry.

<!-- /refine appends sections below (Links, Open decisions) and then the sealed machine zone.
     Never write the machine zone by hand. -->
