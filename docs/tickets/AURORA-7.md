---
key: "AURORA-7"
title: "Time slots do not name the clinic's time zone"
status: "draft"
assignee: ""
type: "bug"
---

# AURORA-7: Time slots do not name the clinic's time zone

Bug found by the QA stage on [AURORA-6](AURORA-6.md) (AC1), confirmed by the QA reviewer, and
approved for filing by the QA manager on 2026-10-05.

## Bug

- **Story / AC:** AURORA-6 / AC1
- **Environment:** `appointments-web` `main` @ `02551d9`, mock e2e build, Chromium
- **Severity:** Medium. Sighted users see the zone in a caption. Screen-reader users who move
  through the slots one by one never hear it.

### Steps to reproduce

1. Log in as a patient and start "Book an appointment".
2. Choose a clinic, a service, a clinician and a day, then open the Time step.
3. Read a slot button, or its accessible name.

### Expected

"On the Time step, every slot shows the clinic's local time and names the clinic's time zone,
whatever the viewer's own time zone is." (AURORA-6, AC1)

### Actual

Each slot shows only the time, for example "09:00 AM". The zone appears once, in the caption
"Times are in the clinic's time zone (PST)." above the slots
(`src/features/appointments/BookingFlow.tsx:232`).

### Evidence

- QA test file: `e2e/stories/AURORA-6/clinic-time-zone.spec.ts` (branch `qa/AURORA-6`, AC1 tests).
- The slot buttons' accessible names are only the time ("09:00 AM").
- QA report and review: `~/.qa-reports/appointments-web/AURORA-6/` (local).

## Acceptance criteria

1. Every slot on the Time step names the clinic's time zone, on the button and in its accessible name.
2. The zone shown on each slot is the clinic's zone, also across a daylight-saving change (for example PST before and PDT after).

<!-- /refine appends sections below (Links, Open decisions) and then the sealed machine zone.
     Never write the machine zone by hand. -->
