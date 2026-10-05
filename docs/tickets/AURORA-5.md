---
key: "AURORA-5"
title: "Limit a patient to two appointments per day"
status: "in-refinement"
assignee: "evg-g"
---

# AURORA-5: Limit a patient to two appointments per day

## Story

As a clinic manager, I want a patient to have no more than two appointments on the same day, so
that one patient cannot block many slots and other patients can still find a free time.

## Acceptance criteria

1. A patient can book up to two appointments on the same day.
2. When a patient already has two appointments on a day, a third booking for that day is refused, and the patient sees a clear message that explains the daily limit.
3. Cancelled appointments do not count toward the limit.
4. The limit is per patient: one patient's bookings do not affect another patient.
5. Appointments on other days are not affected by the limit.

<!-- /refine appends sections below (Links, Open decisions) and then the sealed machine zone.
     Never write the machine zone by hand. -->
