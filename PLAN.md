# Aurora Clinic — Build Plan

Reference-grade learning system: appointment scheduling + medication cold-chain monitoring,
built as three independent repos. Source spec: `CLAUDE_CODE_BOOTSTRAP_PROMPT.md`.

Built inside WSL2 Ubuntu-24.04 at `~/aurora/`. See each repo's `CLAUDE.md` for conventions.

## ▶ RESUME HERE (read this first after /clear)

**Next milestone: 7 — contract publication + `oasdiff` gate** (in `appointments-api`).
Milestones 1–6 are done and committed.

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
- Milestones 1–6 are done and committed. API working tree clean. Backed up to private GitHub repos
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

First actions on resume: read this PLAN.md, read `appointments-api/CLAUDE.md`, recall memory
`aurora-build-environment`, then start milestone 7. Docker must be running for integration tests.

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
- [ ] 7. Contract publication + `oasdiff` gate.
- [ ] 8. Device foundation: protocols, SHT4x register-level driver, CRC, simulator, driver contract suite.
- [ ] 9. Device behaviour: excursion state machine, filtering, store-and-forward buffer, batching, backoff, GPIO/serial tiers, fault injection, soak tests.
- [ ] 10. Telemetry ingestion in the API: MQTT worker + HTTP batch, idempotency, out-of-order/backfill, clock-skew, server-side excursion engine, SSE, telemetry contract.
- [ ] 11. Device SIL + CI/CD: agent vs Mosquitto+API in testcontainers, fleet simulator, matrix CI, packaging, signed OTA manifest, staged rollout, nightly soak, hil gated off.
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
