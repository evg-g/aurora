# Claude Code Bootstrap Prompt — Three-Repo Reference System (FastAPI + React + IoT agent)

> Paste everything below the line into Claude Code, launched from an **empty** project directory.

---

## 0. Role and mission

You are a staff-level full-stack engineer and platform engineer. You are bootstrapping a **reference-grade learning system** from an empty directory. The person running you wants to master, by reading and extending real code:

1. REST API design and **API testing** (unit → integration → contract → property-based → E2E)
2. **CI/CD** with GitHub Actions, including quality gates, containerization, security scanning, and deploys
3. Modern automated testing practice on both backend and frontend
4. A **genuinely professional UI**, not a bootstrap-template look
5. **Python on the device side**: an IoT sensor agent, and how to test hardware-facing code without hardware

Optimize every decision for **teaching value and realism**, never for speed of delivery. This codebase must look like it came from a good product team, not from a tutorial.

## 1. Non-negotiable operating rules

1. **No placeholders.** No `TODO`, no `pass  # implement later`, no stubbed functions, no fake data layers. Every endpoint, component, workflow, and test must be real and runnable.
2. **Execute what you write.** Install dependencies, run migrations, run the full test suite, start the API, the web app and the device agent against the simulator, and hit the API. Do not claim a milestone is done until you have observed it pass.
3. **Never fabricate results.** If a test fails or a tool is unavailable in this environment, say so explicitly and record it in `docs/KNOWN_GAPS.md` with the exact error and the workaround.
4. **Commit in small, meaningful steps** using Conventional Commits (`feat:`, `fix:`, `test:`, `ci:`, `docs:`, `refactor:`, `chore:`). One milestone may produce several commits. Never one giant commit.
5. **Pin everything.** Lockfiles committed (`uv.lock`, `package-lock.json`), exact GitHub Action SHAs or version tags, exact base image digests where practical.
6. **Explain as you go.** Every non-obvious choice gets a short ADR in `docs/adr/NNNN-title.md` (context → decision → consequences).
7. **Stop and ask** only if a decision is genuinely irreversible or ambiguous in a way this prompt does not cover. Otherwise decide, document the decision in an ADR, and continue.
8. Write a `PLAN.md` at the very start listing the milestones from §12 with checkboxes, and update it as you complete each one.
9. **Talk plainly.** See the rules below — they apply to every message you send and every document you write.

### How to talk to the person running you

They are an experienced software tester moving toward engineering work. They know software, they are new to parts of this stack, and they are learning from what you build. So:

- **Short and to the point.** Answer first, explanation after, and only if it adds something. No preamble, no summary of what you are about to do, no restating the request.
- **Plain human language.** Ordinary words, short sentences. When a technical term is unavoidable, define it once in half a line and then just use it.
- **No hype.** No "excellent question", no congratulating, no adjectives about how great the code is. Say what you did and what happened.
- **Reports after a milestone:** what was built, what was run, what passed, what failed, what is next — a few lines each, not an essay.
- **When something breaks**, lead with the actual error and your best explanation of the cause, in one paragraph. Do not bury it under everything that did work.
- **Analogies are welcome** for genuinely new concepts (what a broker is, why a constraint belongs in the database, what CRC protects against). One good analogy beats three paragraphs.
- **Label every shell command** with where it runs, as described in §2.
- **Tables over prose** for anything comparative.
- Write the repo documentation in the same voice: plain, direct, and aimed at someone learning, not at an auditor.

One thing brevity never applies to: **bad news**. If a test fails, a gate cannot run, a shortcut was taken, or something in this prompt turned out to be wrong, say so explicitly and in full. Short means fewer words, never fewer facts.

## 2. Target environment (important)

- Host: Windows machine, development inside **WSL2 (Ubuntu-24.04)**, VS Code, Docker Desktop with WSL integration. Assume a personal machine with a normal internet connection.
- Work inside the Linux filesystem (`~/...`), never under `/mnt/c`, for Docker and I/O performance.
- **Optional, only if the person says they are behind a TLS-inspecting proxy** (common on managed corporate laptops): support an optional build arg `EXTRA_CA_CERT` in every `Dockerfile` that copies a `.crt` into `/usr/local/share/ca-certificates/`, runs `update-ca-certificates`, and sets `NODE_EXTRA_CA_CERTS` / `REQUESTS_CA_BUNDLE` / `SSL_CERT_FILE`. Keep this off the default path — it must never be required on a clean network. Document it in `docs/CORPORATE_NETWORK.md`.
- In all documentation, **label every shell command with its context**: `# WSL (Ubuntu-24.04)`, `# inside container`, `# PowerShell (Windows)`, `# GitHub Actions runner`.
- Everything must be publishable to a **personal public GitHub account**: MIT licensed, no employer names, internal hostnames, certificates, or private data anywhere in the code, the history, or the docs.

## 3. Repository layout

Create **three independent git repositories** as sibling directories in the current folder. They are separate products with separate pipelines; they are not a monorepo and must not share a lockfile, virtualenv, or `node_modules`.

```
./
├── appointments-api/       # git repo #1 — Python 3.12 + FastAPI
├── appointments-web/       # git repo #2 — React 19 + TypeScript + Vite
├── aurora-sensor-agent/    # git repo #3 — Python IoT device agent (see §7)
└── README.md               # top-level: what this system is, how the three repos relate, start here
```

Each repo gets: its own `git init` + initial commit, `.gitignore`, `.editorconfig`, `README.md`, `LICENSE` (MIT), `CONTRIBUTING.md`, `.github/` (workflows, PR template, issue templates, `CODEOWNERS`, `dependabot.yml`), `docs/`, and a `CLAUDE.md` describing the repo's conventions for future AI sessions.

The top-level `README.md` must include a Mermaid diagram of the system (use **Mermaid, not external image services** — it renders natively on GitHub and never breaks behind a restricted network).

## 4. The product: "Aurora Clinic — appointment scheduling and cold-chain monitoring"

A multi-clinic appointment scheduling system **with medication cold-chain monitoring**. This domain is chosen deliberately: it forces real API-testing problems instead of a toy CRUD list, and the cold-chain half gives the IoT device repo (§7) a genuine reason to exist.

### Entities

- **User** — roles: `PATIENT`, `CLINICIAN`, `CLINIC_ADMIN`, `PLATFORM_ADMIN`
- **Clinic** — name, timezone (IANA), address
- **Clinician** — belongs to a clinic, specialty, working hours per weekday, buffer minutes
- **Service** — name, duration minutes, price, active flag
- **Appointment** — clinic, clinician, patient, service, `starts_at` (UTC), `ends_at`, status, `version` (for optimistic locking), `cancellation_reason`
- **AvailabilitySlot** — derived, not stored: computed from working hours − existing appointments − blackout dates
- **WebhookSubscription** — target URL, secret, event types
- **AuditLogEntry** — actor, action, entity, before/after, timestamp
- **Device** — a temperature sensor node: clinic, location label (e.g. "Vaccine fridge A"), hardware/firmware version, status, last-seen, credentials
- **TelemetryReading** — device, `measured_at` (UTC, device clock), `received_at` (server clock), temperature, humidity, battery, sequence number
- **ThresholdPolicy** — per device or per clinic: min/max temperature, `dwell_minutes`, `recovery_minutes`
- **Excursion** — an open/closed cold-chain breach: device, started_at, ended_at, peak value, acknowledged_by

### Business rules that tests must prove

1. Appointment status machine: `REQUESTED → CONFIRMED → COMPLETED`, plus `CANCELLED` (from `REQUESTED`/`CONFIRMED`) and `NO_SHOW` (from `CONFIRMED` only). Any illegal transition → `409`.
2. **No double-booking**: enforced at the database level with a PostgreSQL exclusion constraint on `(clinician_id, tstzrange(starts_at, ends_at))`, *and* checked in the service layer. A test must prove the DB constraint holds under concurrent inserts.
3. Appointments must fall inside the clinician's working hours, in the **clinic's timezone**, with DST handled correctly. Include an explicit DST-transition test case.
4. Cancellation later than the clinic's cutoff window (e.g. 24h) is rejected for `PATIENT` but allowed for `CLINIC_ADMIN` — an authorization rule that is also a business rule.
5. Patients may only read/modify their own appointments; clinicians only their clinic's; platform admins everything. Every endpoint has a test for `401`, `403`, and the happy path.
6. Creating an appointment accepts an `Idempotency-Key` header; replaying the same key returns the original resource, not a duplicate.
7. Updates require `If-Match` with the current `ETag`; a stale ETag returns `412`.
8. State changes emit webhooks signed with HMAC-SHA256 (`X-Signature: sha256=...`, plus timestamp for replay protection), delivered by a background worker with retry and exponential backoff.
9. Telemetry ingestion is **idempotent and order-independent**: a device may retry a batch after a network failure, deliver batches out of order, or backfill hours of buffered readings after coming back online. Duplicates by `(device_id, sequence)` are dropped silently; a late batch must still be evaluated for excursions. Tests must prove all three.
10. A reading whose `measured_at` is further than the allowed skew from `received_at` is flagged, not silently trusted; a reading from the future is rejected with `422`.
11. Excursions are detected server-side from the stored series using the same dwell/recovery rule the device applies locally, and the two must agree — a shared fixture set runs against both implementations.

## 5. Backend — `appointments-api`

### Stack

Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) · Alembic · PostgreSQL 16 · Redis (rate limiting, idempotency keys, job queue) · **uv** for dependency and venv management · `ruff` (lint + format) · `mypy --strict` · `structlog` JSON logging · OpenTelemetry traces/metrics · Docker (multi-stage, non-root user, distroless or slim runtime).

### Architecture

Layered and testable — `api/` (routers, dependencies, schemas) → `services/` (business logic, pure, no FastAPI imports) → `repositories/` (SQLAlchemy) → `models/`. Dependency injection through FastAPI `Depends` so every layer is substitutable in tests. Settings via `pydantic-settings`, 12-factor, validated at startup.

### API surface

- `/api/v1` prefix; OpenAPI 3.1 generated with **complete** descriptions, examples, and response models for every status code.
- Errors follow **RFC 9457 `application/problem+json`** with a stable `type` URI, `title`, `status`, `detail`, `instance`, and a machine-readable `errors[]` for validation failures. Build a central error catalog in `docs/ERROR_CATALOG.md`.
- **Cursor-based pagination** (`?limit=&cursor=`) returning `{ data, page: { next_cursor, has_more } }`. Include a test proving stability when rows are inserted mid-pagination.
- Filtering, sorting, sparse fieldsets on list endpoints.
- Auth: JWT access (short TTL) + refresh token rotation with reuse detection; password hashing with Argon2; `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`.
- Rate limiting per principal with `RateLimit-*` response headers; returns `429` with `Retry-After`.
- `/health/live`, `/health/ready` (checks DB + Redis), `/metrics` (Prometheus).
- Request ID middleware; correlation ID propagated to logs and to webhook deliveries.
- **Device and telemetry endpoints**: device provisioning and credential rotation, `POST /api/v1/devices/{id}/telemetry:batch` (idempotent, bulk, partial-success semantics with a per-item result array), time-series queries with downsampling (`?bucket=5m&agg=avg|min|max`), device health, and excursion list/acknowledge. Store telemetry in plain PostgreSQL with a BRIN index on `measured_at` and a documented retention/downsampling job — no TimescaleDB dependency.
- An **MQTT ingestion worker** subscribing to the broker as the primary path, with the HTTP batch endpoint as fallback; both funnel into the same service layer so one test suite covers both.
- **Server-Sent Events** (`/api/v1/streams/telemetry`) so the web dashboard shows live readings; include a test for reconnect and `Last-Event-ID` resumption.

### Backend test suite

Use `pytest`, `pytest-asyncio`, `httpx.AsyncClient` with ASGI transport, **testcontainers** for real Postgres and Redis (no SQLite substitution — the exclusion constraint requires real Postgres), `polyfactory` for test data factories, `freezegun` or an injected clock for deterministic time, `respx` for outbound HTTP.

#### Test doubles and mocking (must be demonstrated explicitly)

Unit tests run **without any I/O**, so the architecture must make substitution trivial: services depend on protocols (`typing.Protocol`), never on concrete SQLAlchemy sessions or HTTP clients. Use `pytest-mock` (`mocker` fixture) on top of `unittest.mock`, and demonstrate each kind of double at least once, with a comment in the test naming the technique:

| Technique | Where to demonstrate it | Tooling |
|---|---|---|
| **Fake** (working in-memory implementation) | `InMemoryAppointmentRepository` implementing the repository protocol; used by all service unit tests | hand-written, in `tests/fakes/` |
| **Stub** (canned return value) | Clinic settings provider returning a fixed cutoff window | `mocker.patch` / simple class |
| **Mock with assertions** (interaction test) | Confirming that cancelling an appointment calls the webhook dispatcher exactly once with the right payload | `mocker.patch` + `assert_awaited_once_with` |
| **Spy** (wrap the real object) | Counting repository calls to prove there is no N+1 in the availability service | `mocker.spy` |
| **Fake clock** | DST and cutoff-window logic | injected `Clock` protocol + `freezegun` as the cross-check |
| **HTTP mocking** | Webhook delivery: success, 500 with retry, timeout, connection error | `respx` |
| **Fake Redis** | Idempotency and rate limiting at unit level | `fakeredis` (integration level still uses the real container) |
| **DI override** | Replacing `get_current_user` / a whole service in router tests | `app.dependency_overrides` |
| **Async mocks** | Any awaited collaborator | `unittest.mock.AsyncMock` — never a plain `MagicMock` on an async call |

Rules for doubles: mock **only what you own** — never patch third-party internals; never mock the object under test; prefer fakes over mocks for state, mocks only for verifying outgoing interactions; always use `autospec=True`/`create_autospec` so a signature change breaks the test instead of silently passing. Add a section to `docs/TESTING.md` explaining mock vs stub vs fake vs spy with the concrete examples from this repo, and explaining why the integration layer deliberately uses **no** doubles.

Required layers, each in its own directory with a `README.md` explaining what belongs there and why:

| Layer | Location | What it proves |
|---|---|---|
| Unit | `tests/unit/` | Pure business rules: slot computation, state machine, DST math. No I/O, milliseconds. |
| Integration | `tests/integration/` | Router + service + real DB/Redis via testcontainers. Auth, pagination, idempotency, ETag, constraints. |
| Contract | `tests/contract/` | The served OpenAPI schema matches the committed `openapi.json`; fails CI on undocumented drift. |
| Property-based / fuzz | `tests/property/` | **Schemathesis** driven by the OpenAPI spec: no 500s, responses conform to schema, stateful test sequences. Plus `hypothesis` for slot-computation invariants. |
| Load (smoke-level) | `tests/load/` | A small **k6** or **Locust** scenario with latency thresholds, runnable locally and nightly in CI. |
| Security | `tests/security/` | Authz matrix tests (every role × every endpoint), JWT tampering, SQL-injection-shaped inputs, mass-assignment attempts. |

Gates: line coverage ≥ 90% and branch coverage ≥ 85% on `services/` and `api/`, enforced in CI. Add `mutmut` (or `cosmic-ray`) configured for the `services/` package with a documented baseline score, and explain in `docs/TESTING.md` why coverage alone is a weak signal.

Rules for tests: AAA structure, one behavior per test, descriptive names (`test_cancel_within_cutoff_window_is_rejected_for_patient`), no `sleep()`, no inter-test order dependence, parallel-safe (`pytest-xdist` must pass), and every test must be able to fail for the right reason — verify this by temporarily breaking the code during development.

## 6. Frontend — `appointments-web`

### Stack

React 19 + TypeScript (`strict: true`, no `any`, no non-null `!` without comment) · Vite · **TanStack Query v5** for server state · TanStack Router or React Router (file-based routes) · React Hook Form + **Zod** · Tailwind CSS with a real design-token layer · Radix UI primitives (or shadcn/ui built on them) · `openapi-typescript` + `openapi-fetch` (or `orval`) generating the API client **from the backend's `openapi.json`** — hand-written request types are forbidden.

### Product surface

Authenticated app with: login, role-aware navigation, calendar/week view of clinician availability, booking flow (service → clinician → slot → confirm) with optimistic updates and rollback, appointment detail with state transitions, admin views for clinics/clinicians/services, an audit log table with server-side pagination and filters, a settings page, and a **cold-chain monitoring dashboard**: live temperature charts per device (SSE-driven), device health tiles (online, last seen, buffer depth, firmware version), an excursion timeline with acknowledge flow, and a threshold editor.

### UI quality bar — this is where most generated apps fail

- Define **design tokens first** (`src/styles/tokens.css`): a restrained palette with a single accent, a type scale, an 8px spacing scale, radii, elevation, motion durations/easings. Every component consumes tokens; **no hardcoded hex values or arbitrary pixel values in components**.
- Choose a deliberate typographic voice (e.g. Inter or Geist for UI, tabular figures for numeric columns). Set line-height, measure, and letter-spacing intentionally.
- Light and dark themes via CSS custom properties, respecting `prefers-color-scheme` and a user override.
- Every async surface has four designed states: **loading (skeleton, not a spinner-only), empty (with a next action), error (with retry), success**. No dead ends.
- Full keyboard operability, visible focus rings, correct ARIA for dialogs/menus/comboboxes, `prefers-reduced-motion` respected. Target **WCAG 2.2 AA** and prove it with automated axe checks.
- Responsive from 360px up; calendar degrades to an agenda list on small screens.
- Form errors from the API's `problem+json` map to the correct fields, inline, with server and client validation sharing the same Zod schemas where possible.
- Storybook for every primitive and every composite component, including all four states above.

### Frontend test suite

| Layer | Tooling | Scope |
|---|---|---|
| Unit | Vitest | Hooks, formatters, timezone helpers, Zod schemas |
| Component | Vitest + Testing Library + **MSW** | User-visible behavior, not implementation; query by role/label |
| Contract | `openapi-typescript` drift check + MSW handlers generated from the same spec | FE breaks loudly when the API changes |
| E2E | **Playwright** | Critical journeys against the real stack in Docker Compose: login, book, reschedule, cancel, authz denial, error path |
| Accessibility | `@axe-core/playwright` + Storybook a11y addon | Zero serious/critical violations, enforced |
| Visual regression | Playwright screenshots | Key pages, light + dark |
| Performance budget | Lighthouse CI | Budgets on LCP/CLS/TBT and bundle size, enforced in CI |

#### Frontend mocking

- **Network is mocked at the network layer, not the module layer**: MSW handlers in `src/mocks/`, shared between Vitest, Storybook, and the dev server. Handlers are typed against the generated OpenAPI types, so an API change breaks the mocks too — a hand-rolled `fetch` mock that can drift from the contract is forbidden.
- Demonstrate MSW handlers for success, empty, `422` validation error, `409` conflict, `401`, and network failure, and assert the UI's four states for each.
- Use `vi.fn()` for callback spies, `vi.mock()` only for genuinely untestable modules (analytics, router internals), `vi.useFakeTimers()` for debounce/polling, and a fixed `TZ` environment variable plus an injected clock for timezone-dependent rendering.
- In Playwright, use `page.route()` interception to force server errors and slow responses on the critical flow, so error and loading states are covered by E2E as well, while the happy path runs against the real API.

Rules: no testing of implementation details, no snapshot-everything, deterministic time and seeded data, traces and videos retained on failure as CI artifacts, zero flakiness tolerated (`--repeat-each=3` on the critical spec in nightly CI).

## 7. Device — `aurora-sensor-agent` (Python, IoT cold-chain monitor)

This third repo exists to practice **Python on the device side and hardware testing without owning hardware**. It is a real product component, not a toy: clinics store vaccines and temperature-sensitive medication, and a cold-chain breach must be detected, buffered, reported, and alerted on.

### The device

A **smart temperature sensor node** for a clinic's medical refrigerator:

- Host board: Raspberry Pi Zero 2 W running the agent as a `systemd` service (primary target).
- Sensor: **Sensirion SHT4x** temperature + humidity over **I²C** (real chip semantics: command words, measurement delay, 16-bit words each followed by a **CRC-8**, poly `0x31`, init `0xFF`).
- A second, legacy probe over **UART/serial** with a simple ASCII framed protocol — deliberately included so serial testing is practiced too.
- GPIO: status LED (green/amber/red) and a buzzer for a local excursion alarm.
- Optional second target: **MicroPython on ESP32**, documented but not required.

### Agent behaviour

Sample on a fixed interval → validate CRC → apply calibration offset and a median-of-N filter → evaluate the local excursion state machine → drive LED/buzzer → append to a local **SQLite store-and-forward buffer** → batch-publish to the backend over **MQTT** (Mosquitto), with an HTTP fallback endpoint. Plus: device identity and per-device credentials (token or mTLS), at-least-once delivery with a **device-generated idempotency key per batch**, exponential backoff with jitter, a watchdog, clock-skew detection against the server's time, remote configuration (thresholds, interval) delivered over MQTT and applied without restart, a periodic health beacon (uptime, buffer depth, RSSI, firmware version), and structured JSON logging.

Excursion rule to test hard: temperature outside `[min, max]` continuously for longer than `dwell_minutes` raises an excursion; it clears only after the value is back in range for `recovery_minutes`. Short spikes (door opened) must **not** alert. This state machine is the unit-test centrepiece.

### Architecture — substitutability is the whole point

Every hardware touchpoint sits behind a `typing.Protocol`: `I2CBus`, `SerialPort`, `GpioPin`, `Clock`, `Transport`, `BufferStore`. Provide **three** implementations of the sensor stack:

1. `real/` — `smbus2` + `pyserial` + `gpiozero`. These imports must be lazy, inside a factory, so the package imports cleanly on any laptop with no hardware present.
2. `sim/` — a physics-flavoured simulator: fridge thermal model, door-open events, sensor noise, slow drift, and **injectable faults** (bad CRC, NACK, stuck value, NaN, I²C timeout, power loss mid-write, disk full, clock jump). Seeded RNG, fully deterministic.
3. `replay/` — replays recorded traces from CSV/`.jsonl` fixtures captured from the simulator, so regression cases are reproducible byte for byte.

A **driver contract test suite** (an abstract `pytest` base class) runs unchanged against all three, proving they are interchangeable — this is the lesson that makes hardware code testable.

### Hardware test pyramid

| Tier | Location | What it proves | Tooling |
|---|---|---|---|
| Register-level unit | `tests/unit/protocol/` | Command encoding, measurement delay, 16-bit word parsing, **CRC-8 verification and rejection**, raw→°C/%RH conversion, endianness, out-of-range raw values | fake `I2CBus` with a recorded register map, `pytest.mark.parametrize`, `hypothesis` for conversion round-trips |
| Logic unit | `tests/unit/logic/` | Excursion state machine, median filter, debounce, backoff math, buffer eviction policy, batch splitting | fakes + injected `Clock`, zero I/O |
| Driver contract | `tests/driver_contract/` | `real`, `sim`, and `replay` satisfy the same protocol and the same behavioural suite | abstract test class parametrized over implementations |
| GPIO | `tests/unit/gpio/` | LED colour and buzzer pattern per state | `gpiozero` `MockFactory` / `MockPin` |
| Serial | `tests/unit/serial/` | Framing, partial reads, timeouts, garbage bytes, checksum failure, reconnect | `pyserial` `loop://` URL and `pty` pseudo-terminal pairs |
| Fault injection | `tests/faults/` | Every simulator fault mode produces the right retry, log, health flag, and never data loss or duplicate-on-server | parametrized over the fault catalogue |
| Integration (software-in-the-loop) | `tests/sil/` | The whole agent against a real Mosquitto broker and the real API, end to end | **testcontainers** (Mosquitto + Postgres + the API image) |
| Soak / time | `tests/soak/` | Seven simulated days compressed into seconds: no memory growth, no buffer leak, no clock drift, correct behaviour across a **DST change** | fake clock + `tracemalloc` |
| Hardware-in-the-loop (optional) | `tests/hil/` | The same suite against a real Pi + SHT4x | marked `@pytest.mark.hil`, deselected by default, run only on a self-hosted runner; document the wiring and how to enable it |

Determinism rules: no real `sleep` (inject an awaitable delay), no real wall clock, seeded RNG everywhere, every test able to run on a laptop with no hardware, no network, and no Docker except the SIL tier.

### Fleet simulator

Ship a `device-simulator` container that runs **N virtual devices** across several clinics with configurable fault profiles. The backend and frontend repos use it for E2E and ingestion load tests, so the three repos are genuinely coupled at the seams.

### Device repo CI/CD

Matrix over Python 3.12 and 3.13; lint (`ruff`), `mypy --strict`, unit + contract + fault tiers on every PR; SIL tier with testcontainers; nightly soak and the `hil` job gated behind a repo variable so it skips cleanly without hardware. Release: build a wheel **and** a `.deb` (or a Docker image for the gateway), semantic version, signed artifacts, and an **OTA update manifest** (version, checksum, signature) that the agent verifies before applying. Simulate a **staged rollout** — canary → 10% → fleet — driven by a `fleet.yaml` cohort file, with automatic halt on a rising error-rate metric from the simulated fleet. Document the rollback path.

## 8. Cross-repo contract (the part most projects get wrong)

1. `appointments-api` CI publishes `openapi.json` as a build artifact and commits it to the repo at `contracts/openapi.json`.
2. A backend CI job runs **`oasdiff`** against the previous version and **fails the PR on breaking changes** unless the PR is labeled `breaking-change` and the version is bumped.
3. `appointments-web` vendors `contracts/openapi.json`, regenerates types in CI, and fails if generated output differs from the committed output (drift check).
4. The device repo owns the **telemetry contract**: an **AsyncAPI 3** document plus a JSON Schema for the payload, committed at `contracts/telemetry.schema.json`, describing the MQTT topic scheme `aurora/v1/clinic/{clinic_id}/device/{device_id}/telemetry` and the health/config topics. The API repo vendors that schema, validates every inbound message against it, and its CI fails on drift — the same gate as OpenAPI, in the opposite direction.
5. Payload versioning: every message carries a schema version; the API must accept version N−1 and prove it with a test, so device and server can be deployed independently.
6. Document the whole flow, including how a breaking change is rolled out across three independently deployed repos, in `docs/CONTRACT_WORKFLOW.md` with a Mermaid sequence diagram.

## 9. CI/CD — GitHub Actions

All three repos follow the same shape; workflows live in `.github/workflows/` with `concurrency` groups, `permissions:` minimized per job, dependency caching, and path filters.

### `ci.yml` — on pull request

Jobs run in parallel where possible and all are **required checks**:

- `lint` — ruff / eslint + prettier, commitlint on PR title
  *(the device repo runs its own tiers here too: unit, driver-contract, GPIO, serial, fault injection — see §7)*
- `typecheck` — mypy --strict / tsc --noEmit
- `test-unit` — with coverage upload
- `test-integration` — testcontainers (API) / Vitest + MSW (web)
- `test-contract` — schema drift gates from §8
- `build` — Docker image build (BuildKit cache), plus `npm run build` bundle-size check for web
- `security` — `pip-audit`/`npm audit`, **Trivy** filesystem + image scan (fail on HIGH/CRITICAL), **gitleaks**, **CodeQL**, SBOM generation (CycloneDX) uploaded as an artifact
- `e2e` — (web repo) Docker Compose brings up API + Postgres + Redis + web, then Playwright runs; artifacts uploaded on failure

### `cd.yml` — on push to `main`

`build → sign → deploy staging → smoke tests → manual approval (GitHub Environments) → deploy production`, with:

- Semantic versioning and auto-generated changelog (`semantic-release` or `release-please`)
- Images pushed to **GHCR**, tagged with semver + commit SHA, **signed with cosign**, provenance attestation
- **OIDC** for cloud auth — no long-lived secrets anywhere; document the trust policy
- Alembic migrations run as a separate pre-deploy step with an explicit rollback plan; document expand/contract migration strategy
- Post-deploy smoke tests hitting `/health/ready` and one real business flow; automatic rollback on failure
- Deployment target: document Azure Container Apps (primary, IaC in Bicep or Terraform) **and** provide a working `docker-compose.prod.yml` fallback so the pipeline is runnable without a cloud account. Any step requiring real cloud credentials must be gated behind a repo variable and skip cleanly when absent.

### `nightly.yml`

Full E2E repeated for flake detection, mutation testing, load smoke test, dependency freshness report.

### Runner requirements and job hygiene

- Target `ubuntu-latest` GitHub-hosted runners, which have Docker available — this is what makes **testcontainers** work in CI. Provide `services:` containers for Postgres and Redis as a documented alternative, and explain in `docs/CI_CD.md` the trade-off between the two approaches.
- Every job sets `timeout-minutes`, an explicit `permissions:` block, and `strategy.fail-fast: false` where a matrix is used. Run the backend test matrix over Python 3.12 and 3.13, and Playwright over Chromium plus one WebKit shard.
- Cache `uv`/`pip`, `npm`, Playwright browsers, and Docker layers, with cache keys derived from lockfile hashes.
- Publish results to the **job summary** (`$GITHUB_STEP_SUMMARY`): test counts per layer, coverage delta, bundle size delta, Trivy findings. Upload JUnit XML, coverage HTML, Playwright traces/videos, and the SBOM as artifacts with an explicit retention period.
- Add `workflow_dispatch` to every workflow so it can be run manually, and `paths-ignore` for docs-only changes.
- Note in the docs that GitHub-hosted runners have a clean TLS path, so the corporate-CA handling from §2 applies to local runs only.

### Verifying the pipelines without a cloud account

Be explicit and honest about what can be verified where:

1. **Statically**: `actionlint` on every workflow file, plus `yamllint`. Wire this into `make ci-local`.
2. **Locally**: reproduce each PR gate as a `make` target so the exact same commands run locally and in CI; where practical, also verify with **`act`** (`act pull_request -j lint`), and document in `docs/CI_CD.md` which jobs cannot run under `act` (container-signing, OIDC, GHCR push) and why.
3. **On GitHub**: if a remote exists, push a branch and confirm the checks run; if no remote is configured, say so in the final report and provide `docs/FIRST_PUSH.md` with the exact steps to create all three repos, push, enable branch protection, and configure environments and secrets.
4. **Deploy steps**: every job needing real credentials must be guarded (e.g. `if: vars.DEPLOY_ENABLED == 'true'`) and skip cleanly, so the pipeline is green end-to-end on a fresh fork with zero secrets configured. Verify this condition.

Also include: `dependabot.yml` (or Renovate), PR template with a testing checklist, `CODEOWNERS`, a documented branch-protection ruleset in `docs/BRANCH_PROTECTION.md`, and reusable composite actions in `.github/actions/` to avoid copy-paste between jobs.

## 10. Local developer experience

Per repo: a `Makefile` (or `Taskfile.yml`) with `make setup`, `make dev`, `make test`, `make test-integration`, `make e2e`, `make lint`, `make fix`, `make ci-local` (runs the exact PR gates locally). The device repo adds `make sim` (run the agent against the simulator), `make fleet` (start N virtual devices), and `make soak`. `docker-compose.yml` for the full stack, `.env.example` with every variable documented, a `seed` command producing a realistic demo dataset (multiple clinics, timezones, a DST-crossing week), and pre-commit hooks (`pre-commit` / `husky` + `lint-staged`) that run fast checks only.

Bootstrapping must be **one command per repo** from a clean WSL shell, and you must verify it by testing in a clean state before declaring completion.

## 11. Documentation for learning

All documentation follows the plain-language rules in §1: short sentences, ordinary words, examples over abstractions, and a concrete answer to "why does this exist" at the top of every file.

Beyond ADRs and READMEs, each repo needs:

- `docs/TESTING.md` — the test pyramid as implemented here, what each layer catches, what it misses, how to choose a layer for a new feature, and how to debug a failing pipeline.
- `docs/CI_CD.md` — an annotated walkthrough of every workflow file, line group by line group, explaining *why* each gate exists and what real-world failure it prevents.
- `docs/API_TESTING_GUIDE.md` — how to test auth, pagination, idempotency, concurrency, time/DST, webhooks, and error contracts; includes a Postman/Bruno collection or `.http` files mirroring the automated tests.
- `docs/HARDWARE_TESTING.md` (device repo) — how to test hardware-facing code with no hardware: protocols and fakes, simulator vs replay, register-level testing, CRC failures, GPIO and serial doubles, fault injection, soak with a fake clock, and when hardware-in-the-loop is actually required.
- `docs/EXERCISES.md` — at least **20 hands-on exercises** that intentionally break something (remove the DB constraint, widen a type, skip the ETag check, drop a required label, introduce a flaky test, skip CRC validation, make the excursion dwell timer use the real clock, drop the duplicate-sequence guard) and ask the reader to predict which gate fails and why, each with a solution section.
- Mermaid diagrams for architecture, the appointment state machine, the **excursion state machine**, the auth flow, the **telemetry data path (sensor → agent → buffer → MQTT → API → SSE → UI)**, the CI/CD pipeline, and the contract workflow.

## 12. Build order (milestones — commit and verify after each)

1. Scaffolding: all three repos, git init, tooling configs, Makefiles, compose, CI skeleton that already passes.
2. API domain core: models, migrations, exclusion constraint, services, unit tests.
3. API surface: auth, RBAC, CRUD, availability, problem+json, pagination; integration tests with testcontainers.
4. API advanced semantics: idempotency, ETag/If-Match, rate limiting, webhooks + worker; tests for each.
5. Property-based and security test suites; coverage and mutation gates wired into CI.
6. Backend CI/CD complete: build, scan, sign, deploy, smoke, nightly.
7. Contract publication + `oasdiff` gate.
8. **Device foundation**: protocols (`I2CBus`, `SerialPort`, `GpioPin`, `Clock`, `Transport`, `BufferStore`), the SHT4x register-level driver, CRC handling, the simulator, and the driver contract suite. No network yet — everything provable on a bare laptop.
9. **Device behaviour**: excursion state machine, filtering, SQLite store-and-forward buffer, batching, backoff, GPIO and serial tiers, full fault-injection catalogue, soak tests with a fake clock.
10. **Telemetry ingestion in the API**: MQTT worker + HTTP batch endpoint, idempotency by `(device_id, sequence)`, out-of-order and backfill handling, clock-skew rules, server-side excursion engine sharing fixtures with the device, SSE stream, telemetry contract published.
11. **Device SIL + CI/CD**: agent against Mosquitto and the API in testcontainers, fleet simulator container, matrix CI, packaging, signed OTA manifest, staged rollout, nightly soak, `hil` job gated off.
12. Web foundation: design tokens, layout shell, generated API client, auth flow, four-state primitives, Storybook.
13. Web features: calendar, booking flow, admin views, audit log, settings, cold-chain dashboard with live charts and excursion acknowledge.
14. Web test suites: unit, component+MSW, Playwright E2E, axe, visual, Lighthouse budgets.
15. Web CI/CD complete, including E2E against the composed stack plus the fleet simulator.
16. Documentation, exercises, diagrams, final polish.

## 13. Self-verification before you report completion

Run this checklist explicitly and paste the evidence (commands and their output summaries) into your final message. Do not skip a line; if something cannot pass in this environment, mark it and explain.

- [ ] Clean clone of each repo bootstraps with a single command and starts successfully.
- [ ] `make ci-local` passes in **all three** repos, from a clean state.
- [ ] Every test suite in §5, §6 and §7 exists, runs, and passes; report counts per layer.
- [ ] Coverage and mutation thresholds are met and enforced, not merely reported.
- [ ] Deliberately break four things (remove the exclusion constraint, change a response field name, remove a required ARIA label, disable CRC validation in the sensor driver) and confirm **which specific gate fails** in each case; then restore. Record this in `docs/GATES_VERIFIED.md`.
- [ ] `grep -rn "TODO\|FIXME\|placeholder\|lorem ipsum"` returns nothing meaningful in any of the three repos.
- [ ] `tsc --noEmit` and `mypy --strict` are clean; no suppressed errors without a justifying comment.
- [ ] Playwright E2E passes three consecutive runs (no flakes).
- [ ] axe reports zero serious/critical violations on every route, light and dark.
- [ ] The UI has been reviewed against §6's quality bar screen by screen; no hardcoded colors or spacing values remain in components.
- [ ] Unit tests run with the database and network fully unavailable (prove it: disable Docker/network and run `make test-unit`), and every test-double technique in the §5 table appears at least once, with `autospec` enforced.
- [ ] MSW handlers cover success, empty, `422`, `409`, `401`, and network failure, and are typed from the generated OpenAPI types.
- [ ] The device repo's full unit, contract, GPIO, serial and fault tiers pass on a machine with **no hardware, no network and no Docker** — prove it by running them with Docker stopped.
- [ ] The `real` driver module imports cleanly without `smbus2`/`gpiozero` hardware present (lazy imports verified).
- [ ] Every fault mode in the simulator's catalogue has a test, and none of them causes data loss or a duplicate row on the server.
- [ ] The soak test covers at least seven simulated days including a DST change, with no memory or buffer growth.
- [ ] Device and server excursion engines agree on the shared fixture set.
- [ ] The `hil` tier exists, is deselected by default, and its wiring is documented.
- [ ] All workflow YAML is valid (`actionlint`) and every job's `permissions` is minimal.
- [ ] Every PR gate is reproducible locally through a `make` target; report which jobs were verified with `act` and which could not be.
- [ ] The full pipeline is green on a repo with **no secrets configured** — all credential-dependent jobs skip cleanly.
- [ ] Every ADR, README, and docs file referenced in this prompt exists and is non-trivial.
- [ ] Git history is clean, conventional, and tells the story of the build.

Then produce a final report containing: what was built, the verification evidence above, a table of every technology used and what it teaches, and `docs/KNOWN_GAPS.md` listing anything that could not be completed in this environment with the exact reason.

Begin by writing `PLAN.md`, then start milestone 1.
