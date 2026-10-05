# Bug fix: booking times shift for viewers outside the clinic's time zone

Found by hand on the live demo, from Israel, on 2026-10-05. Fixed on the `time-zone-problem` branch
of `appointments-web`, outside ADLC (a quick fix, with its tests written first-to-fail by hand).

## What was wrong

1. **The picked time changed.** A viewer in Israel picked 12:20 on the Time step; Confirm and the
   saved appointment showed 02:20. The slot buttons used the browser's time zone, while Confirm and
   the appointment page used the clinic's (`America/Los_Angeles`). The demo's mock backend also
   built the working hours in the browser's zone.
2. **A second booking failed.** After opening any appointment, the next booking showed "Could not
   book. Something went wrong." The optimistic update treated the cached appointment page as a list
   and threw before the request was sent. A just-booked slot was also still offered.
3. **Times looked like the past.** "Oct 5, 09:00" in Seattle reads as past to a viewer in Israel,
   and the demo offered slots that had already started.

The tests all ran in UTC, where 1 and 3 hid; 2 needed two bookings in one session.

## What changed

- Every clinic time (slots, Confirm, appointment page, list, dashboard, audit label) uses the
  clinic's zone and names it, e.g. `09:00 AM PDT`, with a caption on the Time step.
- The optimistic update touches only the appointment lists, and the open-slot lists refresh after
  a booking.
- The demo dataset no longer offers slots that already started, as the real API does.

## Automated tests

All run in the `Asia/Jerusalem` time zone. Each was seen failing on the old code first.

| Test | What it checks | Runs |
|---|---|---|
| [`e2e/stories/timezone/booking-timezone.spec.ts`](https://github.com/evg-g/appointments-web/blob/main/e2e/stories/timezone/booking-timezone.spec.ts) | Pick 12:20 PM → the same time with the zone on Confirm, the appointment page and the list; three bookings in one session; a booked slot is not offered again | every PR (`e2e + a11y + visual`) |
| [`e2e/pages/booking-timezone.spec.ts`](https://github.com/evg-g/appointments-web/blob/main/e2e/pages/booking-timezone.spec.ts) | On the live-demo build with the clock fixed at 10:00 PDT: only slots from 10:00 on are offered, labelled PDT, and one books | before each live-demo deploy (`pages.yml`) |
| `src/features/appointments/BookingFlow.test.tsx`, `src/mocks/availability.test.ts`, `src/lib/datetime.test.ts` | The same rules at component and unit level, including DST changes | every PR (unit tests) |
