# Tickets

One file per ticket, `AURORA-<n>.md`, made from the plugin's `templates/ticket.template.md`.
This is Aurora's tracker for the ADLC loop:

1. Write the story and numbered acceptance criteria (status `draft`).
2. `/refine AURORA-<n>` — interview, ADRs, sealed machine block, status `ready-for-agent`.
3. `/implement AURORA-<n>` — proves each criterion and opens one PR per repo.

Never edit the `adlc` machine block at the end of a ticket by hand. Re-run `/refine`.
