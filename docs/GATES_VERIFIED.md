# Gates verified — break four things

The self-verification step from the bootstrap prompt (§13): deliberately break four safety mechanisms,
one per concern, and confirm **which specific gate fails** — then restore and confirm green. This is
the proof that the safety nets are real and not decorative.

Run on 2026-09-28 in WSL2 (Ubuntu-24.04) against the actual repos. Each break was applied, the gate
run, the failure captured verbatim below, and the change reverted. All four break targets were
confirmed byte-identical to their originals afterwards (`git diff --quiet` clean).

| # | Break | Repo | Gate that caught it | Needs Docker? |
|---|---|---|---|---|
| 1 | Remove the double-booking exclusion constraint | `appointments-api` | unit model-metadata test | no |
| 2 | Rename an OpenAPI response field | `appointments-api` | contract drift test | no |
| 3 | Remove a required ARIA label | `appointments-web` | axe a11y sweep | yes (browser) |
| 4 | Disable CRC validation in the sensor driver | `aurora-sensor-agent` | register-level unit test | no |

---

## 1. Remove the exclusion constraint

**Break.** Commented out the `ExcludeConstraint` in `models/appointment.py` `__table_args__` (and,
separately, the `EXCLUDE` DDL in migration `0001_domain_core.py`).

**Gate that fails:** `tests/unit/test_models_metadata.py::test_appointments_have_the_no_double_booking_exclusion_constraint`

```
>       assert "ck_appointment_no_double_booking" in constraint_names
E       AssertionError: assert 'ck_appointment_no_double_booking' in {None}
tests/unit/test_models_metadata.py:30: AssertionError
1 failed, 2 passed
```

**An honest finding.** Removing the constraint from the *migration* alone did **not** fail the
integration test `test_concurrent_double_booking_only_one_succeeds` — it still passed
(`sorted([r1, r2]) == [201, 409]`). The reason: that test drives the app in-process over
`httpx.AsyncClient` + ASGI on a single event loop, so the two `asyncio.gather`ed requests do not truly
race at the database — the service-layer check (SELECT-then-INSERT) runs to completion for the first
request before the second is scheduled, and the second gets a clean `409`. The database exclusion
constraint's real job is to stop a race between **separate connections/processes**, which that harness
does not reproduce. The constraint *was* proven at the DB level directly against a real Postgres 16 in
milestone 2 (an overlapping insert is rejected; a cancelled overlap is allowed).

Net: the gate that reliably catches "the constraint is gone" is the model-metadata unit test. The
concurrent integration test documents intent but, on its own, does not depend on the DB constraint —
worth knowing, and a candidate to strengthen (drive it through two real connections). See
[ADR 0002](https://github.com/evg-g/appointments-api/blob/main/docs/adr/0002-prevent-double-booking-with-a-postgres-exclusion-constraint.md).

## 2. Rename an OpenAPI response field

**Break.** Renamed `AppointmentOut.starts_at` → `start_time` in `api/schemas.py`.

**Gate that fails:** `tests/contract/test_openapi_drift.py::test_committed_openapi_matches_served_schema`

```
>       assert committed == served, (
            "contracts/openapi.json is out of date with the served OpenAPI schema. ...")
E       AssertionError: contracts/openapi.json is out of date with the served OpenAPI schema.
E         -     "start_time": {
E         +     "starts_at": {
tests/contract/test_openapi_drift.py:39: AssertionError
1 failed
```

The served schema no longer matches the committed `contracts/openapi.json`. In CI this also drives the
`oasdiff` breaking-change gate (a removed/renamed response field is breaking) and, downstream, the web
repo's generated-client drift gate. See
[CONTRACT_WORKFLOW.md](https://github.com/evg-g/appointments-api/blob/main/docs/CONTRACT_WORKFLOW.md).

## 3. Remove a required ARIA label

**Break.** Removed the accessible name from the compact `ThemeToggle` buttons in the app header
(`components/ui/ThemeToggle.tsx`).

**A note on doing this properly.** Removing only `aria-label` did **not** fail the gate — the buttons
kept an accessible name from their `title` attribute (axe accepts `title` as a name source), so the
sweep passed. Removing the `title` fallback *as well* left the icon-only buttons with no name at all,
which is the real violation.

**Gate that fails:** `e2e/a11y/a11y.spec.ts` — the axe sweep on the dashboard, both themes:

```
2 failed
  [chromium] › a11y — light theme › dashboard has no serious or critical violations
  [chromium] › a11y — dark theme  › dashboard has no serious or critical violations

button-name (impact: critical) — tags: wcag2a, wcag412, cat.name-role-value
  Fix any of the following:
    Element does not have inner text that is visible to screen readers
    aria-label attribute does not exist or is empty
    Element has no title attribute
  <button type="button" aria-pressed="true" class="...">
```

A screen-reader user hears "button" with no idea what it does — a critical WCAG 2.2 name-role-value
failure, caught before it could ship. See [ADR 0006](https://github.com/evg-g/appointments-web/blob/main/docs/adr/0006-browser-test-tiers.md).

## 4. Disable CRC validation in the sensor driver

**Break.** In `drivers/sht4x.py`, replaced the two `verify_word(...)` calls with a plain
`(msb << 8) | lsb` combine, so a corrupt sensor word is no longer checksum-verified.

**Gate that fails:** `tests/unit/sim/test_faults.py::test_bad_crc_is_rejected_then_recovers`

```
>       with pytest.raises(CrcError):
E       Failed: DID NOT RAISE <class 'aurora_sensor_agent.protocol.crc.CrcError'>
tests/unit/sim/test_faults.py:37: Failed
1 failed, 18 passed
```

Without the CRC check a line glitch turns into a believed (wrong) temperature, which becomes a false
excursion — or a missed one. The register-level fault test injects a bad CRC and expects the driver to
raise. Runs on a bare laptop, no hardware. See
[ADR 0002](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/adr/0002-sht4x-register-level-driver-and-sim-replay.md).

---

## After restoring

Each break was reverted and the four files confirmed identical to their committed versions. The
matching gates return green (the CRC, contract, and model-metadata tests pass; the a11y sweep passes
with the accessible names present). These four breaks are also written up as guided exercises, with
predictions, in each repo's `docs/EXERCISES.md`.
