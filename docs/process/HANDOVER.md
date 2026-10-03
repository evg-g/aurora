# Aurora Clinic — Project Handover

A build-time context file, kept as a record. It was written so a new Claude Code session could pick the
project up with no prior memory: what the project is, which decisions were already settled, and how far
the build had got. It is published as part of the build log, not as current documentation — for the state
of the project today, start at the [top-level README](../../README.md).

---

## 1. What this project is

A portfolio project showing test automation and CI/CD across a full system: an API, a web app, and an IoT device agent, with every automated test tier gated in CI. The one exception is the hardware-in-the-loop tier, which needs a real sensor attached and is deselected by default.

**Product:** *Aurora Clinic* — appointment scheduling for a network of clinics, plus cold-chain monitoring of the medication/vaccine fridge in each clinic.

**Three independent GitHub repositories**, each with its own pipeline:

| Repo | Stack | Role |
|---|---|---|
| `appointments-api` | Python 3.12, FastAPI, PostgreSQL, Redis | REST API, telemetry ingestion, alerting engine |
| `appointments-web` | React 19, TypeScript, Vite | Booking UI, admin, live cold-chain dashboard |
| `aurora-sensor-agent` | Python (IoT agent) | Smart temperature sensor node: sampling, buffering, MQTT publishing |

The build instructions live in **`CLAUDE_CODE_BOOTSTRAP_PROMPT.md`** — that file is the authoritative spec. This file is only the context around it.

## 2. Why this domain was chosen

Not for the subject matter — for the problems it forces:

- Timezones per clinic and DST transitions
- Concurrency and double-booking, enforced by a PostgreSQL exclusion constraint
- A real state machine (appointments) and a second one (temperature excursions)
- Role-based authorization as a business rule, not just a decorator
- Idempotency, ETag/If-Match, cursor pagination, signed webhooks
- Telemetry that arrives late, out of order, or twice — the hardest ingestion cases
- Hardware-facing code that must be fully testable with no hardware

## 3. Key decisions already made (don't relitigate without a reason)

1. **Three separate repos, not a monorepo** — the goal is practising independent pipelines and cross-repo contracts.
2. **Contract-driven**: the API publishes `openapi.json`; the web app generates its client from it; the device owns an AsyncAPI + JSON Schema for MQTT. Each side commits its copy of the other's contract, and a CI gate fails the build if that copy drifts — in both directions.
3. **Real Postgres in integration tests** via testcontainers — no SQLite substitute, because the exclusion constraint is the point.
4. **Unit tests use fakes over mocks**; mocks only for verifying outgoing interactions; `autospec` always.
5. **Device hardware sits behind `typing.Protocol`** with three implementations: `real`, `sim` (with injectable faults), `replay`. One contract suite runs against all three.
6. **Hardware-in-the-loop is optional** and deselected by default — no physical device required.
7. **Deploy target**: Azure Container Apps documented, but every credential-dependent job skips cleanly so the pipeline is green with zero secrets configured.
8. **Mermaid for all diagrams** — no external image services.
9. **Plain-language rule**: Claude Code answers short, direct, without hype, and writes the docs in the same voice — but never shortens bad news. This is set in §1 of the bootstrap prompt.

## 4. Environment

- Windows + WSL2 (Ubuntu-24.04), VS Code, Docker Desktop with WSL integration.
- Work inside the Linux filesystem (`~/aurora`), not under `/mnt/c`.
- Needed: Docker running inside WSL, `uv`, Node LTS, `git`, and Claude Code.
- Claude Code must be launched from the project root — it can only read files below where it starts.

## 5. How to run the build

```bash
# WSL (Ubuntu-24.04)
mkdir -p ~/aurora && cd ~/aurora
# place CLAUDE_CODE_BOOTSTRAP_PROMPT.md and HANDOVER.md in this folder
claude
```

Then, inside Claude Code:

```
Read CLAUDE_CODE_BOOTSTRAP_PROMPT.md and follow it.
Start with PLAN.md, then milestone 1 only. Stop and report.
```

Work in batches of one or two milestones. Commit after each. Keep `PLAN.md` updated — it is how a new session picks up where the last one stopped. The full build will not fit in one session.

## 6. Progress log

Update this section as you go, so any future session (or account) knows the state.

- [x] Milestone 1 — scaffolding, three repos, CI skeleton
- [x] Milestone 2–7 — API: domain, surface, advanced semantics, tests, CI/CD, contract
      (2 done: domain core; 3 done: API surface — auth+RBAC+CRUD+availability, problem+json,
      cursor pagination, 20 integration tests on testcontainers; 4 done: idempotency, ETag/If-Match,
      rate limiting, signed webhooks + retrying worker — 83 unit + 36 integration green;
      5 done: property tier (hypothesis + Schemathesis) + security tier (authz matrix, JWT tampering,
      injection, mass-assignment) + coverage gate (96.6% line / 92.4% branch on services+api) +
      mutation baseline (mutmut, ~81.6% kill rate, gate ≥78%) + docs/TESTING.md — 281 tests green,
      gates wired into CI)
- [x] Milestone 8 — device foundation: six Protocol seams, SHT4x register-level driver + CRC,
      real/sim/replay I²C buses, seeded fridge simulator with fault injection, driver-contract
      suite. 78 tests + 5 hardware-skipped, ruff + mypy --strict clean, 95% coverage. ADR 0002.
- [x] Milestone 9 — device behaviour: excursion state machine, calibration + median filter,
      SQLite store-and-forward buffer (bounded), batching + backoff, GPIO (gpiozero MockFactory) and
      serial (pyserial loop://+pty) tiers, full fault catalogue (NaN/disk-full/clock-jump), agent run
      loop, seven-day soak (fake clock + tracemalloc, DST crossing). 173 tests + 5 hardware-skipped,
      ruff + mypy --strict clean, 97% coverage. ADRs 0003–0004.
- [x] Milestone 10 — API telemetry ingestion: MQTT worker + HTTP batch, idempotency by
      (device_id, sequence), out-of-order/backfill, clock-skew, server-side excursion engine sharing
      fixtures with the device, SSE stream, device-owned telemetry contract vendored + drift-gated.
- [x] Milestone 11 — device SIL + CI/CD: real MQTT (QoS 1) + HTTP-fallback transports; device-side
      telemetry-contract self-test + drift gate; fleet simulator + fleet.yaml; signed Ed25519 OTA
      manifest verified before apply; staged rollout (canary→10%→fleet) with auto-halt; SIL tier
      (agent vs Mosquitto + the API image in testcontainers — green against Docker); .deb packaging +
      gateway image; matrix CI + nightly (soak, flake) + hil gated off. ADRs 0005–0007.
- [x] Milestone 12 — web foundation (`appointments-web`): design tokens + theming (Tailwind v4
      `@theme`, light/dark via CSS vars), generated API client (openapi-typescript + openapi-fetch,
      refresh-on-401, drift gate), auth flow (RHF+Zod, protected + role-guarded routes, TanStack
      Query), four-state primitives + `QueryBoundary`, layout shell, typed MSW mocks, 33 tests,
      Storybook 9 + a11y. ADRs 0002–0004. Verified green; pushed to `evg-g/appointments-web`.
- [x] Milestone 13–15 — web: features (calendar, booking, admin, audit, cold-chain dashboard),
      test tiers (Vitest+MSW, Playwright E2E, axe, visual, Lighthouse/bundle budgets), and CI/CD
      (composed-stack E2E + delivery pipeline). Pushed to `evg-g/appointments-web`.
- [x] Milestone 16 — docs, exercises, diagrams, polish. EXERCISES.md in all three repos (26
      break-it exercises); appointments-api API_TESTING_GUIDE.md + runnable requests/*.http; the
      missing Mermaid diagrams (appointment & excursion state machines, auth flow) in
      appointments-api/docs/DIAGRAMS.md + device HARDWARE_TESTING.md; the §13 "break four things" run
      for real and recorded in docs/GATES_VERIFIED.md; dead ComingSoon.tsx removed; top-level README
      rewritten as the portfolio front door with real screenshots. **Build complete — all 16 done.**

The full build log, milestone by milestone, is in [`PLAN.md`](PLAN.md).

Notes / deviations from the spec:

- Milestone 2 used **psycopg 3** (`postgresql+psycopg://`) as the single DB driver for both the
  async app and synchronous Alembic, instead of asyncpg + a separate sync driver. Reason: one
  driver, one dialect. Recorded in ADR 0004.
- The double-booking **exclusion constraint** was written by hand in the Alembic migration (not
  autogenerated) because autogenerate cannot express the `tstzrange`/`btree_gist` EXCLUDE. The
  concurrency test for it is deferred to milestone 3's integration tier (testcontainers), as the
  build order intends.

## 7. What was done before publishing

The bar the project was held to before it went public, and how each item was met:

- **Personal account, MIT license, public repos.** All four repos are public under one MIT license.
- **Nothing private in the code or the history.** No employer name, internal hostnames, certificates,
  proxy config, or credentials — checked across tracked files and the full history.
  `appointments-api/docs/CORPORATE_NETWORK.md` and the proxy notes in `RECOVERY.md` are written
  generically, with placeholder hosts and paths.
- **A front page a stranger can read.** The top-level `README.md` carries the architecture diagram and
  real screenshots captured by Playwright from the production build (`docs/screenshots/`).
- **Green CI on all three repos**, with the badges in the README pointing at the real workflows.
- **Clean, conventional commit history.**
- **ADRs present and readable** — the decisions are the portfolio, more than the code.
- **The use of Claude Code stated openly** in the top-level README, along with what was delegated and
  what was reviewed.
- **The gates broken on purpose.** Each of the three code repos ships a `docs/EXERCISES.md`; four of those breaks were run
  for real and the failing gate recorded in [`docs/GATES_VERIFIED.md`](../GATES_VERIFIED.md), including
  a finding against the project's own tests.

## 8. How this file was used

Each new Claude Code session in the project folder was opened with the same instruction, which is
how the build survived being spread across many sessions with no shared memory:

> Read docs/process/HANDOVER.md and docs/process/PLAN.md, then continue from the next unchecked milestone.

All 16 milestones are now done, so there is no next one; the prompt is recorded here as part of the
method, not as a step to run.
