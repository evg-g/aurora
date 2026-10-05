# Tickets

One file per ticket, `AURORA-<n>.md`, made from the plugin's `templates/ticket.template.md`.
This is Aurora's tracker for the ADLC loop:

1. Write the story and numbered acceptance criteria (status `draft`).
2. `/refine AURORA-<n>` — interview, ADRs, sealed machine block, status `ready-for-agent`.
3. `/implement AURORA-<n>` — proves each criterion and opens one PR per repo.

Never edit the `adlc` machine block at the end of a ticket by hand. Re-run `/refine`.

## Tickets

| Ticket | Status | Notes |
|---|---|---|
| [`AURORA-2`](AURORA-2.md) | `done` | Record an audit-log entry when an appointment is cancelled. The first ticket to go through ADLC; merged as [appointments-api#19](https://github.com/evg-g/appointments-api/pull/19), 3/3 criteria proven. |
| [`AURORA-3`](AURORA-3.md) | `done` | Do not report success when the database did not save the change. Merged as [appointments-api#20](https://github.com/evg-g/appointments-api/pull/20), 4/4 criteria proven. |
| [`AURORA-5`](AURORA-5.md) | `draft` | Limit a patient to two appointments per day. The pilot for the QA stage: ADLC builds it, then the QA agents test it independently. |

Bug fixes made outside ADLC have a short note here too: [booking time zone](BOOKING-TIMEZONE.md).

`AURORA-1` predates this tracker and has no ticket file. It was the dashboard cold-chain card, and
its tests were written with the toolkit's `e2e-test-generation` skill rather than through ADLC —
see [`appointments-web/e2e/stories/AURORA-1/`](https://github.com/evg-g/appointments-web/tree/main/e2e/stories/AURORA-1).
