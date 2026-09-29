# Aurora Clinic

[![api ci](https://github.com/evg-g/appointments-api/actions/workflows/ci.yml/badge.svg)](https://github.com/evg-g/appointments-api/actions/workflows/ci.yml)
[![web ci](https://github.com/evg-g/appointments-web/actions/workflows/ci.yml/badge.svg)](https://github.com/evg-g/appointments-web/actions/workflows/ci.yml)
[![device ci](https://github.com/evg-g/aurora-sensor-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/evg-g/aurora-sensor-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)

A clinic booking system with live monitoring of medication fridges, built as **three repos** — a
FastAPI backend, a React web app, and a Python IoT sensor agent — to show **test automation and
CI/CD** at a professional level. Every test tier below runs in CI and fails the build when it breaks.

**Try it in the browser:** [live demo](https://evg-g.github.io/appointments-web/) (sign in as `admin@aurora.test` / `password123`;
no real backend, the app runs on its mock API) · [latest Playwright test report](https://evg-g.github.io/appointments-web/report/)

**Two-minute tour:** the [test tiers table](#test-automation-at-a-glance) → the
[bugs the gates caught](#bugs-the-gates-caught) → one deep dive:
[API testing](https://github.com/evg-g/appointments-api/blob/main/docs/TESTING.md),
[browser testing](https://github.com/evg-g/appointments-web/blob/main/docs/BROWSER_TESTING.md), or
[hardware-free device testing](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/HARDWARE_TESTING.md).

## Test automation at a glance

| Layer | Tools | Where | Gate in CI |
|---|---|---|---|
| Unit | pytest, Vitest + Testing Library | all three repos | ✅ |
| Integration, real Postgres + Redis | pytest + testcontainers | [api `tests/integration`](https://github.com/evg-g/appointments-api/tree/main/tests/integration) | ✅ |
| Contract (OpenAPI + telemetry schema) | drift tests, `oasdiff` breaking-change check | [api `tests/contract`](https://github.com/evg-g/appointments-api/tree/main/tests/contract) | ✅ |
| Property-based / API fuzzing | Hypothesis, Schemathesis | [api `tests/property`](https://github.com/evg-g/appointments-api/tree/main/tests/property) | ✅ |
| Mutation testing | mutmut, kill rate ≥ 78% | [api `docs/TESTING.md`](https://github.com/evg-g/appointments-api/blob/main/docs/TESTING.md) | ✅ nightly |
| Security | authz matrix, JWT, injection tests; Trivy, gitleaks, pip/npm audit, CodeQL | [api `tests/security`](https://github.com/evg-g/appointments-api/tree/main/tests/security) | ✅ |
| End-to-end | Playwright, Chromium + WebKit, network mocked with MSW | [web `e2e/journeys`](https://github.com/evg-g/appointments-web/tree/main/e2e/journeys) | ✅ |
| Accessibility (WCAG 2.2 AA) | axe, every route, light + dark | [web `e2e/a11y`](https://github.com/evg-g/appointments-web/tree/main/e2e/a11y) | ✅ |
| Visual regression + layout rules | Playwright screenshots, layout assertions | [web `e2e/visual`](https://github.com/evg-g/appointments-web/tree/main/e2e/visual) | ✅ |
| Performance | Lighthouse (LCP/CLS/TBT), bundle-size budget | [web `docs/BROWSER_TESTING.md`](https://github.com/evg-g/appointments-web/blob/main/docs/BROWSER_TESTING.md) | ✅ |
| Load | Locust, p95 latency gate | [api `tests/load`](https://github.com/evg-g/appointments-api/tree/main/tests/load) | ✅ nightly |
| Device without hardware | simulator, trace replay, fault injection, 7-day soak on a fake clock | [device `docs/HARDWARE_TESTING.md`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/HARDWARE_TESTING.md) | ✅ |

Current numbers: API 386 tests, 91% coverage, 79% mutation kill rate · web 76 unit/component
tests, 44 browser tests on Chromium and 34 on WebKit · device 236 tests.

## Bugs the gates caught

Real failures, each fixed with a test or gate that now stops it from coming back:

| What broke | Caught by | Fix |
|---|---|---|
| 43 HIGH/CRITICAL CVEs: Starlette (3) and the nginx base image (40) | Trivy in CI | [api](https://github.com/evg-g/appointments-api/commit/25d1c77) · [web](https://github.com/evg-g/appointments-web/commit/cd1b6db) |
| New telemetry code lowered test strength: mutation kill rate 77.97% (< 78%) | nightly mutation gate | [tests that pin the excursion rules → 79.19%](https://github.com/evg-g/appointments-api/commit/a23249d) |
| Header labels wrapped onto two lines at 1280px — and the visual baselines had recorded it as correct | a new layout test (failed at 1024/1280/1440px) | [layout fix + test](https://github.com/evg-g/appointments-web/commit/41299b2) |
| Dashboard listed the latest booking first, not the soonest | review of the demo screenshots | [fix + unit tests](https://github.com/evg-g/appointments-web/commit/87850cc) |
| Component tests failed only when the machine was busy | reproduced by saturating every CPU core | [timeouts fixed; 4/4 green under load](https://github.com/evg-g/appointments-web/commit/1c63e53) |
| The secret scan failed on every pull request (missing token permission) | CI on Dependabot PRs | [api](https://github.com/evg-g/appointments-api/commit/f71293a) · [web](https://github.com/evg-g/appointments-web/commit/e065eee) |
| Audit-log text failed WCAG AA contrast (4.08:1) | axe accessibility sweep | [ADR 0006](https://github.com/evg-g/appointments-web/blob/main/docs/adr/0006-browser-test-tiers.md) |

Plus four deliberate "break it" checks — each break applied, the failing gate recorded, then reverted —
in [`docs/GATES_VERIFIED.md`](docs/GATES_VERIFIED.md), including an honest finding: the concurrent
double-booking integration test does not actually depend on the database constraint.

## How it is built

**Three independent products**, each its own git repo with its own pipeline, coupled only at their
contracts (an OpenAPI schema and a telemetry schema), so each can be built, tested, and deployed on
its own. The design decisions are written up as ADRs in each repo.

> Built with [Claude Code](https://claude.com/claude-code) as the working environment. The spec it
> started from and the build log are public in [`docs/process/`](docs/process/).

## What it looks like

![Cold-chain dashboard: live fridge temperature with an excursion above the safe band](docs/screenshots/cold-chain.png)

| Dashboard | Appointments |
|---|---|
| ![Dashboard](docs/screenshots/dashboard.png) | ![Appointments](docs/screenshots/appointments.png) |
| **Booking — pick a time** | **Admin — audit log** |
| ![Booking](docs/screenshots/booking.png) | ![Audit log](docs/screenshots/admin.png) |

<sub>Real rendered pages from the production build with its mock backend and a demo dataset,
captured by Playwright (`npm run screenshots` in appointments-web). Dark theme:
[cold chain (dark)](docs/screenshots/cold-chain-dark.png).</sub>

## The three repos

| Repo | What it is | Stack |
|---|---|---|
| [`appointments-api`](https://github.com/evg-g/appointments-api) | The backend: scheduling + telemetry ingestion | Python 3.12, FastAPI, PostgreSQL, Redis |
| [`appointments-web`](https://github.com/evg-g/appointments-web) | The web app: booking, admin, cold-chain dashboard | React 19, TypeScript, Vite |
| [`aurora-sensor-agent`](https://github.com/evg-g/aurora-sensor-agent) | The device agent on a fridge sensor node | Python 3.12, MQTT, SQLite buffer |

Start with each repo's `README.md` and `CLAUDE.md`. Build history lives in [`docs/process/PLAN.md`](./docs/process/PLAN.md).

## What is in it

**v1.0.0**, feature-complete ([api release](https://github.com/evg-g/appointments-api/releases/tag/v1.0.0) · [web release](https://github.com/evg-g/appointments-web/releases/tag/v1.0.0)). Highlights:

- **Backend** — full `/api/v1` surface with auth (JWT + refresh rotation), RBAC, RFC 9457 errors,
  cursor pagination, idempotency, ETag/If-Match, rate limiting, signed webhooks, and telemetry
  ingestion (MQTT + HTTP, idempotent and order-independent) with a server-side excursion engine and an
  SSE stream. Unit / integration (testcontainers) / contract / property / security / load tiers, with
  enforced coverage and mutation gates.
- **Web** — design-token UI (light/dark), a client generated from the OpenAPI schema, the booking flow,
  admin, audit log, and a live cold-chain dashboard. Vitest + MSW, Playwright E2E (MSW and the fully
  composed real stack), axe a11y, visual regression, and Lighthouse/bundle budgets.
- **Device** — the SHT4x driver with CRC, real/sim/replay hardware seams behind Protocols, the
  excursion state machine, a store-and-forward buffer, the full fault catalogue, a compressed seven-day
  soak, software-in-the-loop against a real broker + the API, a fleet simulator, and a signed OTA rollout.
- **CI/CD** — all three repos build, scan (Trivy/gitleaks/CodeQL/SBOM), sign (cosign), and deploy
  (Azure Container Apps via OIDC), with every cloud step gated so a fork stays green with zero secrets.

## How they fit together

```mermaid
flowchart LR
    subgraph clinic["Clinic site"]
        sensor["SHT4x sensor<br/>(I2C + serial)"]
        agent["aurora-sensor-agent<br/>sample - validate CRC - detect<br/>excursion - buffer (SQLite)"]
        sensor -->|readings| agent
    end

    broker["MQTT broker<br/>(Mosquitto)"]
    agent -->|"telemetry batches<br/>(MQTT, HTTP fallback)"| broker

    subgraph backend["appointments-api"]
        ingest["MQTT worker +<br/>HTTP batch endpoint"]
        svc["services<br/>(scheduling, excursions)"]
        db[("PostgreSQL")]
        redis[("Redis")]
        ingest --> svc
        svc --> db
        svc --> redis
    end

    broker -->|subscribe| ingest
    agent -.->|"HTTP fallback"| ingest

    web["appointments-web<br/>(React dashboard)"]
    web -->|"REST /api/v1"| svc
    svc -->|"Server-Sent Events<br/>(live readings)"| web

    hooks["Webhook subscribers"]
    svc -->|"signed webhooks<br/>(HMAC-SHA256)"| hooks
```

More diagrams — the appointment and excursion state machines, the auth flow, the telemetry data path,
the CI/CD pipeline, and the contract flow — are collected in
[`appointments-api/docs/DIAGRAMS.md`](https://github.com/evg-g/appointments-api/blob/main/docs/DIAGRAMS.md).

## Contracts (how the repos stay in sync)

- `appointments-api` publishes `contracts/openapi.json`. A CI job (`oasdiff`) fails a PR on a
  breaking change unless it is labelled and the version is bumped.
- `appointments-web` vendors that schema and **generates** its API client from it; CI fails on
  drift, so a backend change that affects the front end breaks loudly.
- `aurora-sensor-agent` owns the telemetry contract (`contracts/telemetry.schema.json` +
  AsyncAPI). The API vendors it and validates every inbound message; its CI fails on drift.

See [`appointments-api/docs/CONTRACT_WORKFLOW.md`](https://github.com/evg-g/appointments-api/blob/main/docs/CONTRACT_WORKFLOW.md).

## Deep dives by topic

| Area | Where | What it covers |
|---|---|---|
| REST API design | [`appointments-api`](https://github.com/evg-g/appointments-api) | resource modelling, RFC 9457 errors, cursor pagination, idempotency, ETag/If-Match |
| API testing pyramid | [`appointments-api/docs/TESTING.md`](https://github.com/evg-g/appointments-api/blob/main/docs/TESTING.md) | unit vs integration vs contract vs property vs security; fakes vs mocks vs stubs vs spies; why coverage is a weak signal |
| Testing by topic | [`appointments-api/docs/API_TESTING_GUIDE.md`](https://github.com/evg-g/appointments-api/blob/main/docs/API_TESTING_GUIDE.md) + [`requests/*.http`](https://github.com/evg-g/appointments-api/tree/main/requests) | how to test auth, pagination, idempotency, concurrency, DST, webhooks, errors — with hand-runnable requests |
| Try the API by hand | [`appointments-api/README.md` → *Try the API by hand*](https://github.com/evg-g/appointments-api#try-the-api-by-hand) | Swagger UI (`/docs`), ReDoc, `.http` files in VS Code, and importing the OpenAPI spec into Postman |
| Concurrency in the DB | [`appointments-api`](https://github.com/evg-g/appointments-api) | why the no-double-booking rule lives in a Postgres exclusion constraint, not the app |
| Time & DST | [`appointments-api`](https://github.com/evg-g/appointments-api) | booking in a clinic's timezone with an injected clock |
| CI/CD | [`api`](https://github.com/evg-g/appointments-api/blob/main/docs/CI_CD.md) · [`web`](https://github.com/evg-g/appointments-web/blob/main/docs/CI_CD.md) · [`device`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/CI_CD.md) | quality gates, containerization, scanning, signing, OIDC deploys that skip cleanly without secrets |
| Contract-driven repos | [`appointments-api/docs/CONTRACT_WORKFLOW.md`](https://github.com/evg-g/appointments-api/blob/main/docs/CONTRACT_WORKFLOW.md) | OpenAPI + telemetry schemas as the seam; drift and breaking-change gates in both directions |
| Professional UI | [`appointments-web`](https://github.com/evg-g/appointments-web) | design tokens, four async states, WCAG 2.2 AA, performance budgets |
| Frontend testing | [`appointments-web/docs/BROWSER_TESTING.md`](https://github.com/evg-g/appointments-web/blob/main/docs/BROWSER_TESTING.md) | MSW at the network layer, Playwright E2E, axe, visual regression, Lighthouse |
| Hardware without hardware | [`aurora-sensor-agent/docs/HARDWARE_TESTING.md`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/HARDWARE_TESTING.md) | Protocol seams, register-level + CRC tests, sim/replay, fault injection, soak with a fake clock |
| Device delivery | [`PACKAGING.md`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/PACKAGING.md) · [`OTA_ROLLOUT.md`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/OTA_ROLLOUT.md) | .deb packaging, a signed OTA manifest, and a staged rollout with auto-halt |

## Break it on purpose

The fastest way to trust a safety net is to cut a hole in it and watch the alarm. Each repo has a
`docs/EXERCISES.md` with break-it-on-purpose exercises (26 in total) — make the change, predict which
gate fails, run it, confirm:

- [`appointments-api/docs/EXERCISES.md`](https://github.com/evg-g/appointments-api/blob/main/docs/EXERCISES.md)
- [`appointments-web/docs/EXERCISES.md`](https://github.com/evg-g/appointments-web/blob/main/docs/EXERCISES.md)
- [`aurora-sensor-agent/docs/EXERCISES.md`](https://github.com/evg-g/aurora-sensor-agent/blob/main/docs/EXERCISES.md)

Four of them were run for real and the failing gates recorded in
[`docs/GATES_VERIFIED.md`](./docs/GATES_VERIFIED.md).

## Running it

Each repo bootstraps with one command from a clean shell:

```bash
# WSL (Ubuntu-24.04) — clone the three repos side by side
git clone https://github.com/evg-g/appointments-api.git
git clone https://github.com/evg-g/appointments-web.git
git clone https://github.com/evg-g/aurora-sensor-agent.git

cd appointments-api      && make setup && make dev        # backend on :8000
cd appointments-web      && make setup && make dev        # web on :5173
cd aurora-sensor-agent   && make setup && make ci-local   # device: lint + types + contract + tests
```

Full stacks:

```bash
# appointments-api: Postgres + Redis + API + migrations
make stack-up && make seed

# appointments-web: the composed real stack (API + Postgres + Redis behind nginx), then E2E
make e2e-composed-all

# aurora-sensor-agent: the whole agent against the simulated sensor, or a virtual fleet
make run
make fleet
```

Behind a TLS-inspecting corporate proxy, see each repo's `docs/CORPORATE_NETWORK.md` /
`docs/BROWSER_TESTING.md`. On a clean network none of that is needed.

Restoring the whole project on a new or formatted machine (toolchain, auth, clone layout, proxy and
test-tier setup): [`docs/process/RECOVERY.md`](./docs/process/RECOVERY.md).

## License

MIT — see [`LICENSE`](./LICENSE); each code repo carries its own copy.
