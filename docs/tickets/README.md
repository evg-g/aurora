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
| [`AURORA-2`](AURORA-2.md) | `ready-for-agent` | Record an audit-log entry when an appointment is cancelled. The first ticket to go through ADLC; refined (ADR 0016 on `story/AURORA-2`), next is `/implement`. |

`AURORA-1` predates this tracker and has no ticket file. It was the dashboard cold-chain card, and
its tests were written with the toolkit's `e2e-test-generation` skill rather than through ADLC —
see [`appointments-web/e2e/stories/AURORA-1/`](https://github.com/evg-g/appointments-web/tree/main/e2e/stories/AURORA-1).
