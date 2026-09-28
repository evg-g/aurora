# Aurora Clinic — Build Plan

Reference-grade learning system: appointment scheduling + medication cold-chain monitoring,
built as three independent repos. Source spec: `CLAUDE_CODE_BOOTSTRAP_PROMPT.md`.

Built inside WSL2 Ubuntu-24.04 at `~/aurora/`. See each repo's `CLAUDE.md` for conventions.

## ▶ RESUME HERE (read this first after /clear)

**Next milestone: 12 — web foundation** (work moves to `appointments-web`): design tokens, layout
shell, the generated API client (from `appointments-api/contracts/openapi.json`), the auth flow,
four-state primitives, and Storybook. The two backend/device repos are complete through milestone 11.

Milestone 11 delivered (done, in `aurora-sensor-agent`): device SIL + CI/CD.
- Real transports behind the `Transport` seam: `transport/mqtt.py` (paho v2, QoS 1, waits for PUBACK
  so a failure surfaces synchronously and the agent buffers+retries), `transport/http.py` (httpx,
  posts the batch envelope to `POST /devices/{id}/telemetry:batch` with `X-Device-Secret`),
  `transport/fallback.py` (MQTT primary → HTTP fallback, same idempotency key on either path).
- Device-side telemetry-contract self-test (`tests/contract/`) + drift gate (`scripts/check_contract.py`,
  checksums + cross-repo byte-compare vs the API's vendored copy) — the API's reverse gate mirrored.
- `fleet/`: a `fleet.yaml` schema, a fleet simulator (`VirtualClock` + `SimUplink`, N real agents on
  seeded sim sensors), and `StagedRollout` (canary → 10% → fleet, auto-halt when a cohort's error rate
  rises past the policy). `ota.py` verifies a signed Ed25519 manifest (signature → artifact hash/size →
  version direction) before applying; `scripts/{gen_ota_key,build_ota_manifest}.py` sign/verify; no
  keys committed.
- **SIL** (`tests/sil/`, marked `sil`): testcontainers brings up Postgres+Redis+Mosquitto+the
  appointments-api image (HTTP) + its MQTT worker; the agent's real HTTP and MQTT transports are driven
  end to end and read back via the API time-series. Verified green against real Docker (2 passed).
  hil (`tests/hil/`) is deselected + hardware-guarded.
- CI: `ci.yml` gains contract, sil (builds the API image when `API_REPO` is set), and package (wheel +
  .deb + signed OTA manifest) jobs; matrix excludes sil. `nightly.yml` = soak + x3 flake + gated hil.
  actionlint clean. Packaging: `scripts/build_deb.sh` vendors the agent + deps into a .deb; enhanced
  gateway image. ADRs 0005–0007; docs CI_CD / PACKAGING / OTA_ROLLOUT / KNOWN_GAPS; HARDWARE_TESTING
  extended.
- Verified: ruff + mypy --strict clean (98 files); 236 passed / 5 skipped / 4 deselected on the
  non-Docker gate; `make sil` green against Docker; `make deb` builds the package; `make ota-demo`
  and `make fleet`/`rollout` run. New deps: paho-mqtt, httpx, cryptography, PyYAML (runtime);
  jsonschema, testcontainers, types-PyYAML, types-jsonschema (dev).
- Deviations (see `aurora-sensor-agent/docs/KNOWN_GAPS.md`): SIL needs Docker + the built API image;
  the MQTT path trusts the broker topic/ACL (no per-message secret, matching the API worker); the .deb
  is arch-specific + Python-3.12-only (compiled deps); a 4xx from HTTP is raised+logged but retried.

Milestones 1–11 are done and committed.

What milestone 10 delivered (done, in `appointments-api`): telemetry ingestion end-to-end.
- Models + migration 0003: `Device` (per-device Argon2 secret, status), `TelemetryReading`
  (`(device_id, sequence)` unique = idempotency key; **BRIN** index on `measured_at`; no TimescaleDB),
  `ThresholdPolicy` (device- or clinic-scoped band), `Excursion` (keyed `(device_id, started_at)`).
- Ingestion service (`services/telemetry/ingestion.py`, pure, Protocol seams): idempotent
  (`INSERT ... ON CONFLICT DO NOTHING`), order-independent (re-derives excursions from `measured_at`
  after every batch, so a late backfill still alarms), clock-skew (flag past skew / reject future).
  One service; HTTP endpoint and MQTT worker both build it via `telemetry_wiring`.
- Server excursion engine (`services/telemetry/excursion.py`) is a faithful port of the device's;
  proved equal on the shared fixtures (vendored `tests/fixtures/excursions/cases.json`).
- API: device provisioning + credential rotation, `POST /devices/{id}/telemetry:batch` (per-item
  result array, X-Device-Secret auth), time-series `?bucket=&agg=` (date_bin), device health,
  excursion list/acknowledge, SSE `/streams/telemetry` (Redis Stream, Last-Event-ID resume).
- MQTT worker (`workers/telemetry_mqtt.py`, `python -m ...`, aiomqtt) — the primary path.
- Telemetry contract: **the device repo now owns** `aurora-sensor-agent/contracts/telemetry.schema.json`
  + `telemetry.asyncapi.yaml`; the API vendors them into `appointments_api/contracts/telemetry/`,
  validates every inbound message (jsonschema), accepts version N and N-1, and gates drift with
  `scripts/check_telemetry_contract.py` (checksum guard + cross-repo byte compare) — the OpenAPI gate
  in reverse. Docs: `docs/TELEMETRY.md` (Mermaid data path + retention/downsampling), ADR 0014,
  `CONTRACT_WORKFLOW.md` telemetry section. Retention job `scripts/retention.py` (`make retention`).
- Verified: ruff + mypy --strict (139 files) clean; unit+contract 114, integration 95, plus property
  (SSE op skipped — unbounded stream) + security (authz matrix extended); coverage gate 95.14% line /
  86.30% branch on services/+api/; OpenAPI + telemetry drift gates green. New deps: jsonschema,
  aiomqtt (runtime), types-jsonschema (dev).
- Deviations (see `docs/KNOWN_GAPS.md`): full-series excursion re-derivation per batch (bounded-window
  is the follow-up); SSE uses bearer auth (EventSource needs cookie/token — milestone 12); future
  reading is a per-item `rejected` rather than a top-level 422 (bulk endpoint); device-side contract
  self-test + drift gate deferred to milestone 11.

Context for a fresh session:
- Work happens in WSL2 Ubuntu-24.04 at `/home/evgenig/aurora/`. Edit files via the
  `\\wsl.localhost\Ubuntu-24.04\home\evgenig\aurora\...` path; run commands with
  `wsl -d Ubuntu-24.04 bash /path/to/script.sh`.
- WSL execution quirk: do NOT pass inline `$VAR`/`$(...)`/quotes/heredocs through
  PowerShell→wsl (they get mangled). Write a script file with the Write tool, run it, read a
  log file. Always `export HOME=/home/evgenig` (and source nvm for node) at the top of scripts.
  Full details in memory `aurora-build-environment`.
- Tools ready: uv, Node 20 (nvm), Python 3.12, Docker (from WSL, `postgres:16` + `redis:7` images
  pulled), make/gcc, git identity `evgmongo-maker`. sudo needs a password (hand to the user).
- Milestones 1–7 are done and committed. API working tree clean. Backed up to private GitHub repos
  under personal account `evg-g` (remotes set; `~/.gh_personal` holds the push token).
- Backups: the three code repos push to `evg-g/<name>`. This PLAN.md and the top-level docs are
  tracked in a 4th private repo **`evg-g/aurora`** (a git repo rooted at `~/aurora/` that ignores
  the three code dirs). After updating PLAN.md at the end of a milestone, run `git -C ~/aurora push`
  too, or the checklist/progress backup goes stale.

What milestone 3 delivered (done):
- FastAPI surface under `/api/v1`: auth (`/auth/login|refresh|logout|me`), users, clinics,
  clinicians, services, availability, appointments (book/list/get/transition/cancel).
- Auth: Argon2 passwords, JWT access tokens, opaque **refresh-token rotation with reuse detection**
  in Redis (`services/tokens.py` + `repositories/redis_tokens.py`).
- RBAC: PATIENT (own), CLINICIAN (their clinic), admins (all — CLINIC_ADMIN scoping deferred, see
  `docs/KNOWN_GAPS.md`). RFC 9457 problem+json (`api/errors.py`, `docs/ERROR_CATALOG.md`).
  Cursor/keyset pagination (`api/pagination.py`). Async DB + Redis wiring in `db.py`.
- Repositories in `repositories/`; schemas in `api/schemas.py`; deps in `api/deps.py`; routers in
  `api/routers/`. `/health/ready` now checks DB + Redis.
- Tests: 30 unit (no I/O) + 20 integration with **testcontainers** (real Postgres + Redis, no
  doubles) — auth rotation/reuse, RBAC 401/403/happy, working-hours 422, sequential AND concurrent
  double-booking (409 via the exclusion constraint), state machine, cancellation window, cursor
  stability. New deps: pyjwt, argon2-cffi, redis, pydantic[email]; dev: testcontainers, polyfactory,
  pytest-xdist. `make ci-local` green (ruff, mypy --strict on 62 files, unit); `make test-integration`
  green (needs Docker).

What milestone 4 delivered (done): Idempotency-Key on create (Redis SET NX + fingerprint; replay /
409 in-progress / 422 key-reused / release-on-failure); ETag/If-Match optimistic concurrency
(strong ETag from `version`; 428 missing, 412 stale; StaleDataError → 412); per-principal rate
limiting (fixed window in Redis, middleware, `RateLimit-*` + `429`/`Retry-After`, fail-open, health
exempt); signed webhooks (HMAC-SHA256 + signed timestamp) published on state changes to a Redis
event queue, delivered by a background worker (fan-out to `WebhookSubscription` rows, retry with
exponential backoff + jitter, dead-letter after max attempts) runnable in-process or via
`python -m appointments_api.workers.webhooks`. New: migration 0002 (webhook_subscriptions),
admin-only subscription CRUD router, `fakeredis` + `respx` dev deps. ADRs 0007–0010. Verified:
ruff + mypy --strict clean (95 files), 83 unit + 36 integration green.

What milestone 5 delivered (done): property tier (`tests/property/`) — `hypothesis` slot invariants +
Schemathesis fuzzing every OpenAPI op (no 500s / schema conformance, authenticated); security tier
(`tests/security/`) — authz matrix (every role × endpoint), JWT tampering, injection-shaped inputs,
mass-assignment. Coverage gate `scripts/check_coverage.py` (line ≥90% / branch ≥85% on services/+api/,
combined over all tiers; `concurrency=["greenlet"]` so async handlers are attributed) — actual 96.6% /
92.4%. Mutation gate `scripts/check_mutation.py` on services/ via unit runner — baseline 421 killed /
94 survived / 126 no-tests / 1 timeout (kill rate ≈81.6% over tested; gate ≥78%). `docs/TESTING.md`
(mock/stub/fake/spy taxonomy + why integration uses no doubles + why coverage is weak), READMEs per
tier, ADR 0011. New dev deps: hypothesis, schemathesis, mutmut, pytest-mock. Extra functional
integration tests added to close the routers to the gate. CI: `coverage` job per-PR, `mutation` job
nightly + workflow_dispatch. `make ci-local` = lint + typecheck + coverage gate. Verified: ruff +
mypy --strict clean (112 files), 88 unit + property + security + integration = 281 tests green,
coverage + mutation gates green.

What milestone 6 delivered (done): backend CI/CD complete. `ci.yml` expanded (build, security =
pip-audit + Trivy fs/image + gitleaks + CycloneDX SBOM, CodeQL, dedicated integration job, composite
action `setup-python-uv`, JUnit/coverage/SBOM artifacts, job summaries, PR-title + workflow lint).
New `cd.yml`: release-please → build → cosign keyless sign + provenance → GHCR (semver+SHA) → deploy
staging → smoke → production manual approval → smoke, with OIDC Azure auth, a separate expand-phase
migration step, and revision rollback on smoke failure; every Azure step gated by
`vars.DEPLOY_ENABLED` so a fork stays green with zero secrets. New `nightly.yml`: integration flake
re-run ×3, mutation (moved off per-PR), Locust load smoke with a p95 gate, dependency freshness.
Added `tests/load/` (Locust) + `scripts/{seed,smoke_test,check_load}.py`, hardened Dockerfile (OCI
labels) + `.dockerignore`, `docker-compose.yml` (local full stack) + `docker-compose.prod.yml`
(no-cloud fallback), Azure Bicep IaC (`infra/`), and docs CI_CD/DEPLOYMENT/BRANCH_PROTECTION/
FIRST_PUSH/CORPORATE_NETWORK + ADR 0012. Real bug found + fixed: `httpx` was dev-only but imported at
runtime, so the `--no-dev` production image crashed on startup — moved to runtime deps.

What milestone 7 delivered (done): OpenAPI contract publication + drift + breaking gates.
`scripts/export_openapi.py` renders `app.openapi()` deterministically to `contracts/openapi.json`
(OpenAPI 3.1.0, 21 paths); `make contract` regenerates, `make contract-check` fails on staleness.
`tests/contract/` drift test asserts served == committed (byte-identical, reusing the exporter's
serializer). CI `contract` job: drift test + publishes openapi.json artifact + `oasdiff` breaking-change
gate vs the base branch, overridable only with the `breaking-change` PR label. `make contract-diff`
runs the same oasdiff locally (binary pinned v1.32.1, installed at `~/.local/bin/oasdiff`).
`docs/CONTRACT_WORKFLOW.md` (Mermaid: change flow + expand/contract rollout across the 3 repos) +
ADR 0013. Verified: ruff + mypy --strict (114 files) clean, 89 unit+contract tests green, oasdiff
exit 0 on identical / exit 1 on a removed path. Web-side drift check is milestone 12; telemetry
AsyncAPI contract is milestone 10.

First actions on resume: read this PLAN.md, then work in **`aurora-sensor-agent`** for milestone 11 —
read its `CLAUDE.md`, recall memory `aurora-build-environment`. Milestone 11 (device SIL + CI/CD)
needs Docker: testcontainers running Mosquitto + the API so the agent's MQTT publish path is exercised
end-to-end against the milestone-10 ingestion. The device owns the telemetry contract at
`aurora-sensor-agent/contracts/` (schema + AsyncAPI, added in milestone 10); wire its self-test +
drift gate into the device CI. The API side of telemetry ingestion is complete and green (see the
milestone-10 summary above); `appointments-api` `make ci-local` + the OpenAPI/telemetry contract gates
all pass.

## Repos

- `appointments-api/` — Python 3.12 + FastAPI backend
- `appointments-web/` — React 19 + TypeScript + Vite frontend
- `aurora-sensor-agent/` — Python IoT cold-chain device agent
- `README.md` — top-level system overview with Mermaid diagram

## Milestones

- [x] 1. Scaffolding: all three repos, git init, tooling configs, Makefiles, compose, CI skeleton that already passes.
- [x] 2. API domain core: models, migrations, exclusion constraint, services, unit tests.
- [x] 3. API surface: auth, RBAC, CRUD, availability, problem+json, pagination; integration tests with testcontainers.
- [x] 4. API advanced semantics: idempotency, ETag/If-Match, rate limiting, webhooks + worker; tests for each.
- [x] 5. Property-based and security test suites; coverage and mutation gates wired into CI.
- [x] 6. Backend CI/CD complete: build, scan, sign, deploy, smoke, nightly.
- [x] 7. Contract publication + `oasdiff` gate.
- [x] 8. Device foundation: protocols, SHT4x register-level driver, CRC, simulator, driver contract suite.
- [x] 9. Device behaviour: excursion state machine, filtering, store-and-forward buffer, batching, backoff, GPIO/serial tiers, fault injection, soak tests.
- [x] 10. Telemetry ingestion in the API: MQTT worker + HTTP batch, idempotency, out-of-order/backfill, clock-skew, server-side excursion engine, SSE, telemetry contract.
- [x] 11. Device SIL + CI/CD: agent vs Mosquitto+API in testcontainers, fleet simulator, matrix CI, packaging, signed OTA manifest, staged rollout, nightly soak, hil gated off.
- [ ] 12. Web foundation: design tokens, layout shell, generated API client, auth flow, four-state primitives, Storybook.
- [ ] 13. Web features: calendar, booking flow, admin views, audit log, settings, cold-chain dashboard.
- [ ] 14. Web test suites: unit, component+MSW, Playwright E2E, axe, visual, Lighthouse budgets.
- [ ] 15. Web CI/CD complete, including E2E against the composed stack + fleet simulator.
- [ ] 16. Documentation, exercises, diagrams, final polish.

## Progress log

- 2026-09-26: Environment ready in WSL2 (uv, Node 20, Python 3.12, Docker, make/gcc, git identity). Starting milestone 1.
- 2026-09-26: Milestone 1 complete. All three repos scaffolded, verified green, and committed:
  - `appointments-api`: FastAPI app factory + health endpoints, ruff/mypy --strict clean, 2 unit tests, 100% cov. 5 commits.
  - `aurora-sensor-agent`: SHT4x CRC-8 primitive + config + CLI, ruff/mypy clean, 15 tests (incl. hypothesis), 97% cov. 4 commits.
  - `appointments-web`: React 19 + TS strict + Vite, eslint/prettier/tsc clean, 2 component tests, 100% cov, prod build OK. 4 commits.
  - Top-level README with system Mermaid diagram. Each repo has CI workflow, Dockerfile, ADR, dependabot, templates, CODEOWNERS, Makefile.
  - Note: web has 3 dev-only moderate npm-audit advisories (0 in production bundle); tracked in appointments-web/docs/KNOWN_GAPS.md.
- 2026-09-26: Milestone 2 complete (`appointments-api`). Domain core built and verified:
  - Models: User, Clinic, Clinician (+ working-hours table), Service, Appointment, AuditLogEntry;
    shared enums at `appointments_api/enums.py`; optimistic-lock `version` column on Appointment.
  - Alembic (`alembic.ini`, `migrations/`) + migration `0001_domain_core`: `btree_gist` extension
    and the `ck_appointment_no_double_booking` EXCLUDE constraint (partial: excludes CANCELLED/
    NO_SHOW). Single driver psycopg 3 for app + migrations.
  - Pure services: appointment state machine, cancellation-window policy, DST-aware slot
    computation + `AvailabilityService`; injected `Clock`; `tests/fakes/` (FixedClock + in-memory
    repo). ADRs 0002 (exclusion constraint), 0003 (time/DST), 0004 (optimistic lock + psycopg).
  - Verified green: ruff, mypy --strict (30 files), 31 unit tests, 100% coverage. Also applied the
    migration to a real Postgres 16: overlapping insert rejected, cancelled overlap allowed,
    downgrade clean. Deps added: sqlalchemy, alembic, psycopg[binary], tzdata, freezegun.
  - Deviation: none. Concurrency test for the constraint is deferred to milestone 3 (integration
    tier with testcontainers), as planned.
- 2026-09-27: Milestone 3 complete (`appointments-api`). API surface built and verified:
  - Routers under `/api/v1`: auth (login/refresh/logout/me), users, clinics, clinicians, services,
    availability, appointments (book/list/get/transition/cancel). Layered api → services →
    repositories → models; deps in `api/deps.py`, schemas in `api/schemas.py`.
  - Auth: Argon2 passwords, JWT access tokens, opaque refresh-token rotation with reuse detection
    (Redis). RBAC per spec rule 5 (patient/clinician scoped; admin broad — CLINIC_ADMIN scoping
    deferred, see KNOWN_GAPS). RFC 9457 problem+json + ERROR_CATALOG. Keyset cursor pagination.
    Async DB/Redis in `db.py`; `/health/ready` checks both.
  - Tests: 30 unit (no I/O) + 20 integration (testcontainers, real Postgres+Redis, no doubles),
    covering auth rotation/reuse, RBAC 401/403/happy, working-hours 422, sequential + concurrent
    double-booking (409 via exclusion constraint), state machine, cancellation window, cursor
    stability under inserts. ADRs 0005 (auth) and 0006 (problem+json + pagination).
  - Verified green: ruff, ruff format, mypy --strict (62 files), 30 unit, 20 integration. Deps
    added: pyjwt, argon2-cffi, redis, pydantic[email]; dev: testcontainers[postgres,redis],
    polyfactory, pytest-xdist. `postgres:16` + `redis:7` images pulled.
  - Deviation: CLINIC_ADMIN clinic-scoping deferred (no admin↔clinic link in the model yet);
    documented in `docs/KNOWN_GAPS.md`. Idempotency/ETag/rate-limit/webhooks are milestone 4.
- 2026-09-27: Milestone 4 complete (`appointments-api`). API advanced semantics built and verified:
  - Idempotency-Key on `POST /appointments`: Redis SET NX claim + request fingerprint; replay of the
    original 201 (`Idempotency-Replayed: true`), 409 while in progress, 422 on key-reuse-with-different-body,
    release-on-failure. `services/idempotency.py` + `repositories/redis_idempotency.py`.
  - ETag/If-Match: strong ETag from `version` on every appointment response; transition/cancel require
    If-Match (428 missing, 412 stale); `StaleDataError` mapped to 412. `api/conditional.py`.
  - Rate limiting: fixed-window per principal (token sub or IP) in Redis, HTTP middleware, `RateLimit-*`
    headers + 429/`Retry-After`, fail-open, health/docs exempt. `services/rate_limit.py` +
    `repositories/redis_rate_limit.py` + `api/middleware.py`.
  - Webhooks: state changes publish an event (dispatcher → Redis list); a worker fans out to
    `WebhookSubscription` rows, signs with HMAC-SHA256 (+ signed timestamp), retries with exponential
    backoff + jitter, dead-letters after max attempts. Runnable in-process (off by default) or
    `python -m appointments_api.workers.webhooks`. Model + migration 0002 + admin-only CRUD router +
    `services/webhooks/*` + `repositories/redis_webhooks.py` + `repositories/webhooks.py`.
  - Tests: unit demonstrate fakeredis (idempotency, rate limit), respx (sender), AsyncMock interaction
    (dispatcher), fakes + fixed clock (worker); integration on real Redis for all four features
    (idempotency replay/reuse, 428/412 ETag flow, 429 + headers, webhook enqueue/deliver/retry/dead-letter,
    subscription CRUD authz). ADRs 0007 (idempotency), 0008 (ETag), 0009 (rate limit), 0010 (webhooks).
  - Verified green: ruff, ruff format --check, mypy --strict (95 files), 83 unit, 36 integration.
    New deps: dev `fakeredis`, `respx`. `make ci-local` green.
  - Deviation: webhook emission is not transactional with the DB commit (at-least-once delivery;
    receivers dedupe on `X-Webhook-Id`); a transactional outbox is the documented follow-up
    (`docs/KNOWN_GAPS.md`, ADR 0010).
- 2026-09-27: Milestone 5 complete (`appointments-api`). Property + security tiers and the quality
  gates built and verified:
  - Property tier `tests/property/`: `hypothesis` invariants for slot computation (duration, ordering,
    past-filter, blackout-monotonicity, cross-check with `fits_working_hours`, across DST timezones);
    Schemathesis fuzzes every OpenAPI operation for no-500 + response-schema conformance, authenticated
    as a platform admin. The fuzzed app gets a per-call resource lifespan (create+dispose engine/Redis
    each `TestClient` cycle) so async calls don't cross event loops; OpenAPI 3.1 enabled in Schemathesis.
  - Security tier `tests/security/`: data-driven authz matrix (every role × endpoint: 401/403/allowed),
    JWT tampering (forged sig, `alg:none`, wrong secret, expired, refresh-as-access, inflated-role that
    can't escalate since RBAC reads role from DB), injection-shaped inputs (stored literally / clean
    4xx / DB intact), mass-assignment (smuggled id/status/version/is_active ignored; no patient-id spoof).
  - Coverage gate `scripts/check_coverage.py`: line ≥90% / branch ≥85% on services/+api/ over all tiers
    combined. Needed `concurrency=["greenlet"]` in coverage config — SQLAlchemy async runs handlers over
    greenlet switches and coverage otherwise mis-attributes router lines (looked like 52% branch; real
    92%). Actual: 96.6% line / 92.4% branch.
  - Mutation gate `scripts/check_mutation.py`: `mutmut` on services/ via the unit runner. Baseline 421
    killed / 94 survived / 126 no-tests / 1 timeout of 642; kill rate ≈81.6% over tested mutants; gate
    ≥78%. `only_mutate` scopes mutation to services/ while copying the whole package so imports resolve.
  - Docs: `docs/TESTING.md` (mock/stub/fake/spy with repo examples, why integration uses no doubles,
    why coverage alone is weak), README per test tier, ADR 0011. Added the missing `spy` demonstration
    (`mocker.spy`, pytest-mock) proving no N+1 in availability.
  - Added functional integration tests (`test_appointments_flows`, `test_catalog`, `test_auth_flows`,
    `test_webhooks_api`, `test_appointments_idempotency`) to bring the routers up to the coverage gate.
  - CI: `coverage` job per-PR (Docker on the runner → testcontainers), `mutation` job nightly +
    workflow_dispatch. `make ci-local` = lint + typecheck + coverage. New Make targets test-property,
    test-security, coverage, mutation.
  - Verified green: ruff + ruff format --check + mypy --strict (112 files); 281 tests (88 unit +
    integration + security + property); coverage gate OK; mutation gate OK. New dev deps: hypothesis,
    schemathesis, mutmut, pytest-mock.
  - Deviation: mutation runs nightly/on-demand rather than per-PR (a full run is heavy); this matches
    the spec's own nightly-mutation split (§6). ~126 services mutants have "no tests" under the unit
    runner (webhook delivery I/O paths, covered by the integration tier) and are excluded from the score.
- 2026-09-27: Milestone 8 complete (`aurora-sensor-agent`). Device foundation built and verified —
  no network, no Docker, no hardware needed:
  - Six hardware seams as `typing.Protocol` in `src/aurora_sensor_agent/protocols.py`: `I2CBus`,
    `SerialPort`, `GpioPin`, `Clock`, `Transport`, `BufferStore`. `I2CBus` + `Clock` are implemented
    and exercised this milestone; the other four are the agreed contracts, implemented in 9-11.
  - `Reading` value object (`models.py`); real `SystemClock` (`clock.py`); a `FakeClock` in
    `tests/fakes/` whose `sleep` advances time instead of blocking.
  - SHT4x register-level driver (`drivers/sht4x.py`): command bytes (0xFD/0xF6/0xE0), measurement
    delay via the injected Clock, 6-byte frame = two 16-bit words each + CRC-8 (reuses the milestone-1
    `protocol/crc.py`), per-word CRC verify, raw->°C/%RH conversion (humidity clamped 0..100), soft
    reset, serial-number read. Talks only to the `I2CBus` seam — no hardware imports.
  - Three buses satisfy that seam: `real/i2c.py` (smbus2, LAZY imports — module loads with no
    hardware, first op raises ModuleNotFoundError, proven by a test); `sim/` — a register-level chip
    simulator (`sim/i2c.py`) enforcing the conversion delay and emitting real CRCs, driven by a
    seeded, time-pure fridge `ThermalModel` (`sim/thermal.py`: setpoint, door-open warm-ups, noise,
    drift) with chip/bus fault injection (`sim/faults.py`: BAD_CRC, NACK, TIMEOUT, SHORT_READ,
    POWER_LOSS, STUCK); `replay/i2c.py` — byte-for-byte replay of a recorded `.jsonl` trace with
    command-drift detection.
  - Driver-contract suite (`tests/driver_contract/`): one abstract `Sht4xStackContract` run against
    sim + replay (real tier skipped, needs a Pi) — proves the three are interchangeable. Plus
    register-level driver tests, sim thermal + fault tests, replay error-path tests, clock/model tests.
  - `scripts/record_trace.py` captures the committed fixture `tests/fixtures/traces/sim_baseline.jsonl`
    (deterministically, from the sim). `.gitignore` fixed to track that fixture (was caught by
    `traces/*.jsonl`). `aurora-agent sim` CLI subcommand + `make sim` run the driver against the sim.
    Docs: `docs/HARDWARE_TESTING.md` (milestone-8 portion) + ADR 0002.
  - Verified green: ruff + ruff format --check + mypy --strict (37 files) clean; 78 tests passed,
    5 hardware-skipped; 95% total coverage (`real/i2c.py` at 42% is the unavoidable on-device path).
    `aurora-agent sim` prints realistic ~4.4 °C / 45 %RH readings. No new dependencies.
  - Deviation: the higher-layer faults from spec §7 (NaN in the pipeline, disk full, clock jump) are
    buffer/clock-seam faults, not chip/bus faults; they land with the buffer + fault tier in
    milestone 9. Recorded in ADR 0002.
- 2026-09-27: Milestone 9 complete (`aurora-sensor-agent`). Device behaviour built and verified —
  no network, no Docker, no hardware needed:
  - Pure logic layer (`logic/`, zero I/O, injected `Clock`): the **excursion state machine**
    (`excursion.py`, NORMAL→PENDING→EXCURSION→CLEARING; dwell/recovery; short-spike-no-alarm;
    no-flapping; peak tracking; backward-clock guard; a `detect_excursions` series runner driven by a
    **shared fixture set** `tests/fixtures/excursions/cases.json` that the server engine will be held
    to in milestone 10); calibration + **median-of-N** filter with a NaN/inf guard (`filter.py`);
    exponential **backoff with full jitter** (`backoff.py`); **batch splitting** with a stable
    per-batch idempotency key (`batch.py`); and the LED/buzzer **indicator** mapping (`indicator.py`).
  - **SQLite store-and-forward buffer** (`buffer/sqlite.py`, ADR 0004): write-before-send, bounded
    ring-buffer eviction (oldest dropped when full), row id = device `sequence` via AUTOINCREMENT,
    survives close/reopen.
  - **Serial tier**: legacy UART probe (`drivers/legacy_probe.py`) — a pure `FrameParser` (NMEA-style
    `$T=..,H=..*CS`, resync past garbage/corrupt frames, checksum count) + `LegacyProbe` I/O; real
    port via `pyserial` (`real/serial.py`), tested over `loop://` and a `pty` pair.
  - **GPIO tier**: `real/gpio.py` over `gpiozero`, tested through its `MockFactory` (no hardware).
  - **Higher-layer fault catalogue** (`sim/pipeline_faults.py`, `tests/faults/`): NaN (rejected),
    disk full (flagged, no crash, no loss of buffered data, still drains), clock jump (no spurious
    excursion, skew flagged); guarantee proven: no fault loses buffered data or duplicates on the
    server (retried batch reuses its idempotency key). A guard test fails if a fault is added without
    a test.
  - **Agent run loop** (`agent.py`): skew-check → sample → calibrate/filter → excursion → indicator →
    buffer → drain (batch + publish + backoff), with a `HealthBeacon`. Transport is still a seam; an
    in-memory transport (`transport/memory.py`) backs the loop and soak. `serde.py` owns the reading
    wire format.
  - **Soak tier** (`tests/soak/`): seven simulated days in <1 s on a `FakeClock` — tracemalloc shows
    no memory creep, the buffer stays bounded across a two-day outage then drains, and it crosses an
    EU DST boundary. `make soak` runs it; `make run` / `aurora-agent run` runs the loop against the sim.
  - New dev deps: `pyserial`, `gpiozero` (+ `colorzero`); mypy overrides mark both untyped. New ADRs
    0003 (excursion machine + injected clock) and 0004 (buffer + batching). `docs/HARDWARE_TESTING.md`
    extended; per-tier READMEs added. CI `test` job (already `pytest tests` over 3.12/3.13) now covers
    all new tiers.
  - Verified green: ruff + ruff format --check + mypy --strict (73 files) clean; 173 tests passed,
    5 hardware-skipped; 97% total coverage (`real/i2c.py` 42% is the unavoidable on-device path).
  - Deviation: none from the milestone-9 scope. The MQTT/HTTP transports are milestone 10-11 (no
    network yet, as planned), so `Transport` ships as a seam + in-memory fake this milestone.
- 2026-09-27: Milestone 10 complete (`appointments-api`). Telemetry ingestion built and verified:
  - Models + Alembic 0003: `Device` (per-device Argon2 secret + status lifecycle), `TelemetryReading`
    (`(device_id, sequence)` unique idempotency key, **BRIN** on `measured_at`, no TimescaleDB),
    `ThresholdPolicy` (device- or clinic-scoped, exactly-one-scope check), `Excursion` (keyed
    `(device_id, started_at)`, preserves acknowledgement across re-derivation). New enums
    `DeviceStatus`, `ExcursionDirection` (values `low`/`high` via `values_callable`).
  - `services/telemetry/ingestion.py` — one pure service over Protocol seams for BOTH transports:
    idempotent (`INSERT ... ON CONFLICT DO NOTHING`, concurrent-race-safe), order-independent (full
    excursion re-derivation from `measured_at` after each batch, so a late backfill still alarms),
    clock-skew (flag past-skew, reject future). `services/telemetry/excursion.py` is a faithful port
    of the device engine, proved equal on the vendored shared fixtures.
  - API routers: device provisioning + credential rotation, `POST /devices/{id}/telemetry:batch`
    (per-item result array, `X-Device-Secret` auth), time-series `?bucket=&agg=` (`date_bin`), device
    health, excursion list + `:acknowledge`, threshold-policy create, and SSE `/streams/telemetry`
    (Redis Stream, `Last-Event-ID` resume). MQTT worker `workers/telemetry_mqtt.py` (aiomqtt) is the
    primary path; `telemetry_wiring.py` is the shared composition root.
  - Telemetry contract now OWNED by the device repo: `aurora-sensor-agent/contracts/telemetry.schema.json`
    + `telemetry.asyncapi.yaml`, vendored byte-identical into `appointments_api/contracts/telemetry/`,
    validated on every inbound message, N/N-1 versioned, drift-gated by
    `scripts/check_telemetry_contract.py` (checksum + cross-repo compare) — the OpenAPI gate reversed.
    Docs: `docs/TELEMETRY.md` (Mermaid data path, retention/downsampling), ADR 0014, CONTRACT_WORKFLOW
    telemetry section, ERROR_CATALOG + KNOWN_GAPS updates. Retention job `scripts/retention.py`.
  - New deps: `jsonschema`, `aiomqtt` (runtime), `types-jsonschema` (dev). CI `contract` job gained a
    telemetry drift step. Verified green: ruff + ruff format + mypy --strict (139 files); unit+contract
    114, integration 95, property (SSE op skipped) + security (authz matrix extended); coverage gate
    95.14% line / 86.30% branch on services/+api/; OpenAPI + telemetry drift gates pass.
  - Deviations (docs/KNOWN_GAPS.md): full-series re-derivation per batch (bounded window is the
    follow-up); SSE bearer auth (EventSource transport is milestone 12); future reading is a per-item
    `rejected`, not a top-level 422 (bulk endpoint); device-side contract self-test is milestone 11.
- 2026-09-28: Milestone 11 complete (`aurora-sensor-agent`). Device SIL + CI/CD, verified:
  - Real transports behind the `Transport` seam: MqttTransport (paho v2, QoS 1, waits for PUBACK →
    failures surface synchronously so the agent buffers+retries; paho client injected for tests),
    HttpTransport (httpx → `POST /devices/{id}/telemetry:batch` with `X-Device-Secret`; 5xx/429/network
    raise for retry, 4xx raised+logged), FallbackTransport (MQTT primary → HTTP fallback, same
    idempotency key). Unit-tested with a fake paho client + httpx MockTransport (no network).
  - Telemetry-contract self-test (`tests/contract/`, builds a real batch and validates it against the
    owned schema; proves strictness + the N-1 rule) and the owner-side drift gate
    (`scripts/check_contract.py`, checksums + cross-repo compare vs the API's vendored copy) —
    `make contract-check`, wired into `ci-local` and a CI `contract` job.
  - `fleet/`: `fleet.yaml` schema (devices, fault profiles, cohorts), a fleet simulator (real agents
    on a `VirtualClock` + seeded sim sensors + `SimUplink`), and `StagedRollout` (canary → 10% → fleet,
    auto-halt when a cohort's error rate rises past the policy). `ota.py` verifies a signed Ed25519
    manifest (signature → artifact hash/size → version direction) before applying;
    `scripts/{gen_ota_key,build_ota_manifest,derive_ota_pubkey}.py` sign/verify; no keys committed
    (`keys/` gitignored). CLI `aurora-agent fleet|rollout`; `make fleet|rollout|ota-demo`.
  - SIL (`tests/sil/`, marked `sil`): testcontainers → Postgres+Redis+Mosquitto+the appointments-api
    image (HTTP) + a second container running its MQTT worker; the agent's real HTTP and MQTT transports
    drive telemetry end to end, read back via the API time-series. Green against real Docker (2 passed);
    skips cleanly when Docker/image absent. hil (`tests/hil/`) deselected + hardware-guarded, wiring
    documented; nightly hil job gated behind `HIL_ENABLED` on a self-hosted runner.
  - CI: `ci.yml` = lint, typecheck, test matrix (3.12/3.13, excludes hil+sil), contract, sil (builds the
    API image when `API_REPO` set, else the tests skip), package (wheel + .deb + signed OTA manifest,
    uploads artifacts). `nightly.yml` = soak + x3 flake + gated hil. actionlint clean
    (`.github/actionlint.yaml` declares the custom runner label). Packaging: `scripts/build_deb.sh`
    vendors the agent + deps under `/opt/aurora-sensor-agent/lib` (no network at install) + a hardened
    systemd unit; enhanced gateway image (OCI labels, fleet default CMD). ADRs 0005–0007; docs
    CI_CD / PACKAGING / OTA_ROLLOUT / KNOWN_GAPS; HARDWARE_TESTING extended.
  - Verified: ruff + ruff format + mypy --strict clean (98 files); 236 passed / 5 skipped / 4 deselected
    on `pytest -m "not hil and not sil"`; `make sil` = 2 passed against Docker; `make deb` builds
    `dist/aurora-sensor-agent_0.1.0_amd64.deb`; `make ota-demo`, `make fleet`, `make rollout` run green.
    New deps: paho-mqtt, httpx, cryptography, PyYAML (runtime); jsonschema, testcontainers, types-PyYAML,
    types-jsonschema (dev). A real bug surfaced: the local `appointments-api:local` image was stale
    (pre-milestone-10, no MQTT worker module) — rebuilt from current source before SIL passed.
