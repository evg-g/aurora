# Aurora Clinic — Build Plan

Reference-grade learning system: appointment scheduling + medication cold-chain monitoring,
built as three independent repos. Source spec: `CLAUDE_CODE_BOOTSTRAP_PROMPT.md`.

Built inside WSL2 Ubuntu-24.04 at `~/aurora/`. See each repo's `CLAUDE.md` for conventions.

## ▶ RESUME HERE (read this first after /clear)

**Next milestone: 4 — API advanced semantics** (in `appointments-api`).

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
- Milestones 1–3 are done and committed. API working tree clean. Backed up to private GitHub repos
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

What milestone 4 must deliver (from spec §4, §5, §12): Idempotency-Key on create, ETag/If-Match
optimistic concurrency (the `version` column → 412 on stale writes), per-principal rate limiting
(`429` + `Retry-After`), and signed webhooks (HMAC-SHA256) delivered by a background worker with
retry/backoff — each with tests (fakeredis at unit level, real Redis at integration).

First actions on resume: read this PLAN.md, read `appointments-api/CLAUDE.md`, recall memory
`aurora-build-environment`, then start milestone 4. Docker must be running for integration tests.

## Repos

- `appointments-api/` — Python 3.12 + FastAPI backend
- `appointments-web/` — React 19 + TypeScript + Vite frontend
- `aurora-sensor-agent/` — Python IoT cold-chain device agent
- `README.md` — top-level system overview with Mermaid diagram

## Milestones

- [x] 1. Scaffolding: all three repos, git init, tooling configs, Makefiles, compose, CI skeleton that already passes.
- [x] 2. API domain core: models, migrations, exclusion constraint, services, unit tests.
- [x] 3. API surface: auth, RBAC, CRUD, availability, problem+json, pagination; integration tests with testcontainers.
- [ ] 4. API advanced semantics: idempotency, ETag/If-Match, rate limiting, webhooks + worker; tests for each.
- [ ] 5. Property-based and security test suites; coverage and mutation gates wired into CI.
- [ ] 6. Backend CI/CD complete: build, scan, sign, deploy, smoke, nightly.
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
