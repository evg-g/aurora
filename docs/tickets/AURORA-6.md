---
key: "AURORA-6"
title: "Booking times stay in the clinic's time zone for every viewer"
status: "in-review"
assignee: "evg-g"
---

# AURORA-6: Booking times stay in the clinic's time zone for every viewer

## Story

As a patient who books from another time zone, I want every appointment time to be the clinic's
local time, with the zone named, so that I book the time I mean and see the same time everywhere.

Built outside ADLC as a bug fix (see [BOOKING-TIMEZONE.md](BOOKING-TIMEZONE.md)), merged as
[appointments-web#18](https://github.com/evg-g/appointments-web/pull/18). This ticket gives that
fix acceptance criteria, so the QA agents can test it independently.

## Acceptance criteria

1. On the Time step, every slot shows the clinic's local time and names the clinic's time zone, whatever the viewer's own time zone is.
2. The time the patient picks is the same time, with the same zone, on the Confirm step, on the appointment page, and in the appointment list.
3. A patient can make several bookings in one session, also after opening an appointment, without an error.
4. A slot that was just booked is not offered again.
5. Slots that have already started, in the clinic's time, are not offered.

## Links

- Bug from the QA stage: [AURORA-7](AURORA-7.md) (AC1, time slots do not name the zone).
