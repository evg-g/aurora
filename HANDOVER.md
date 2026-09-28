# Aurora Clinic — Project Handover

Portable context file. Upload this at the start of a new chat in a fresh Claude account, or keep it at the root of the project folder so Claude Code can read it. It replaces everything a previous account would have remembered.

---

## 1. What this project is

A self-directed learning project built to reach professional level in API testing, CI/CD, automated testing, and Python on the device side — and to serve as a portfolio piece.

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
2. **Contract-driven**: the API publishes `openapi.json`; the web app generates its client from it; the device owns an AsyncAPI + JSON Schema for MQTT. CI fails on drift in both directions.
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
cp /mnt/c/Users/<user>/Downloads/CLAUDE_CODE_BOOTSTRAP_PROMPT.md .
cp /mnt/c/Users/<user>/Downloads/HANDOVER.md .
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
- [~] Milestone 2–7 — API: domain, surface, advanced semantics, tests, CI/CD, contract
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
- [ ] Milestone 12–15 — web: foundation, features, tests, CI/CD (next)
- [ ] Milestone 16 — docs, exercises, diagrams, polish

The authoritative, up-to-date state lives in `~/aurora/PLAN.md` (in WSL). Read that first.

Notes / deviations from the spec:

> _(record anything that had to change, and why)_

- Milestone 2 used **psycopg 3** (`postgresql+psycopg://`) as the single DB driver for both the
  async app and synchronous Alembic, instead of asyncpg + a separate sync driver. Reason: one
  driver, one dialect. Recorded in ADR 0004.
- The double-booking **exclusion constraint** was written by hand in the Alembic migration (not
  autogenerated) because autogenerate cannot express the `tstzrange`/`btree_gist` EXCLUDE. The
  concurrency test for it is deferred to milestone 3's integration tier (testcontainers), as the
  build order intends.

## 7. Portfolio checklist

Before publishing to a personal GitHub account:

- [ ] Personal account, MIT license, public repos
- [ ] No employer name, internal hostnames, certificates, proxy config, or private data — in the code **or** in the git history
- [ ] Top-level `README.md` with an architecture diagram, screenshots, and a short GIF of the live dashboard
- [ ] CI badges green on all three repos
- [ ] Clean, conventional commit history
- [ ] ADRs present and readable — the decisions are the portfolio, more than the code
- [ ] Stated openly that the project was built using Claude Code as the working environment
- [ ] You can personally explain, without notes: why the exclusion constraint lives in the database, why fakes instead of mocks, what breaks when the OpenAPI contract drifts, and why the excursion timer must not use the real clock

Work through `docs/EXERCISES.md` and break things on purpose before publishing. If you can predict which gate fails and why, the project is genuinely yours.

## 8. Starting a new chat with this file

Open a new chat, attach this file, and say:

> This is a project I'm building. Read the handover, then help me with <the specific task>.

For a new Claude Code session in an existing project folder, just say:

> Read HANDOVER.md and PLAN.md, then continue from the next unchecked milestone.
