# Build ADLC in This Project

> **What this is.** The build order that set ADLC up in Aurora — the `/refine` → `/implement`
> proof loop described in the [top-level README](../../README.md). It is written as instructions
> *to an agent*, not as prose for a human reader, which is why it reads the way it does. It is
> published because the method is the point: it is reusable in any project, and the
> [qa-ai-toolkit](https://github.com/evg-g/qa-ai-toolkit) ships it as a plugin.

**Audience: Claude Code, running in a project that does not yet have ADLC.**

This document is a build order, not background reading. Work through the phases in sequence.
Each phase names the files to create and ends with an acceptance check you must run before
moving on. Do not skip ahead, and do not scaffold anything before Phase 0 is answered.

ADLC — Agentic Development LifeCycle — is a framework for turning a ticket into merged,
proven code without a human watching each step. It has been in production use on another
codebase for over a hundred releases. This document carries its transferable logic. It
carries no dependency on that codebase, its issue tracker, or its plugin marketplace.

**Scope of this build: the core loop only.**

```
/refine  →  a Ready-for-Agent ticket  →  /implement  →  one PR per repo, with proof
```

That is the walking skeleton — the thinnest path that closes the whole loop on a real
ticket. The origin framework was built this way and grew outward from it. Section 11 lists
what was deliberately left out and the order to add it in.

---

## 1. What you are building, and the five rules that make it work

You are building a project-local Claude Code plugin with two commands.

`/refine` takes one ticket written for a human and turns it into a ticket written for both a
human and an agent. `/implement` takes that ticket and proves every acceptance criterion with
a durable test, then opens a pull request carrying the evidence.

Everything else in this document exists to serve five rules. Each one is here because its
absence caused a real failure. Read them now; every later phase enforces one of them.

### Rule 1 — The ticket has two zones, and the machine zone is sealed

A refined ticket carries human prose and a machine-readable block. The prose is the source;
the block is derived from it. The block is emitted by `/refine`, read by `/implement`, and
never hand-edited. It ends with a `sha256` seal over its own content.

`/implement` recomputes that seal before it does anything else. If the block was edited after
emission, the seal does not match and the run stops. Without this, a human "just fixing" an
acceptance criterion silently changes what the agent proves, and nothing catches it.

### Rule 2 — Every criterion names how it is verified, and that name maps to a real command

Each acceptance criterion carries a surface tag — `[api]`, `[data]`, `[logic]`,
`[component]`, `[ui]`, `[design]` — and a binding that resolves to an actual test command in
this project. A criterion whose verification method is unknown is not ready; it is flagged at
refine time, not discovered at implement time.

### Rule 3 — A test must be seen failing before its pass counts

This is the rule that makes the output trustworthy, and it is the one most often softened.
Do not soften it.

- A green with no prior observed red for that test is **not** proof. It is recorded as
  `green-no-red-observed`, a separate verdict.
- A test that failed and then passed at the same unchanged tree is **not** proof. The code
  did not change, so the green is noise. This is no-retry-to-green.
- A build failure is not a red. A test that never ran is not a red. Neither counts toward
  non-vacuity.
- Every verdict is appended to a log that lives **outside** the worktree, so a `git clean`
  or a branch switch cannot erase the evidence.

An agent that can retry until green will retry until green. The log and the tree hash are
what make that impossible rather than merely discouraged.

### Rule 4 — An unprovable criterion is flagged, never skipped

If a criterion cannot be proven, the run says so, in the report and on the PR. It does not
drop it, does not quietly rewrite it, and does not mark it done. The only thing that stops
the whole run is a false claim — a criterion reported proven that has no verdict behind it.

### Rule 5 — Deterministic work stays in bash

Seal computation, structural lint, branch naming, verdict classification, and log appending
are scripts. They are not model instructions. A model asked to "check the seal" will
sometimes check it and sometimes say it checked it. A script either exits 0 or it does not.

Put the judgment in the model. Put the gates in bash.

---

## 2. Phase 0 — Interview the engineer

**Stop here. Ask before you build.** The answers decide the shape of every file below, and
guessing produces a framework that looks right and binds to nothing.

Ask these one at a time, in plain prose. Number each question. State your recommendation
after the options, never before — a recommendation read first becomes the answer.

1. **Issue tracker.** Jira, GitHub Issues, Linear, or Markdown files committed in the repo?
   This decides where the machine zone lives and how a ticket is claimed and transitioned.
   If there is no tracker, recommend Markdown files under `docs/tickets/` — the loop works
   fine and there is no integration to maintain.

2. **Repo layout.** One repository, or several that ship together? If several, get their
   local paths. One PR per repo is the rule; a feature spanning three repos opens three PRs
   on a shared branch name.

3. **Test harness per surface.** For each surface this project actually has, the exact
   command that runs **one** named test. Not the whole suite — one test. For example:
   - `[api]` / `[logic]` — `pytest tests/ -k <name>`, `go test -run <name> ./...`,
     `dotnet test --filter FullyQualifiedName~<name>`
   - `[component]` / `[ui]` — `npx playwright test --grep <title>`,
     `npx vitest run -t <name>`
   A surface with no harness is not supported yet. Record that and move on; do not invent one.

4. **Proof test isolation.** How will agent-authored proof tests be selected and kept apart
   from the existing suite? Recommend a tag or marker the runner filters on — a pytest
   marker, a Go build tag, a Playwright `@agent-trusted` grep tag. This matters: a proof
   runner that can select any test can be pointed at a test that was already passing.

5. **Base branch and CI.** What is the default branch, and what must pass before a PR can
   merge?

Write the answers into `.claude/adlc-config.md`. Every later phase reads from it. Do not
proceed until all five are answered.

---

## 3. Phase 1 — Scaffold the plugin

Create a project-local plugin. No marketplace, no external install.

```
.claude/plugins/adlc-local/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── refine/SKILL.md
│   └── implement/SKILL.md
├── agents/
│   ├── implement-repo.md
│   ├── implement-prover.md
│   ├── test-review.md
│   └── code-review.md
├── scripts/
│   ├── adlc-seal.sh
│   ├── adlc-lint.sh
│   ├── adlc-proof.sh
│   ├── adlc-story-branch.sh
│   └── lib/proof-adapters/<one per harness>.sh
└── shared/
    └── acceptance-schema.md
```

`plugin.json`:

```json
{
  "name": "adlc-local",
  "version": "0.1.0",
  "description": "Project-local ADLC — the /refine to /implement proof loop."
}
```

Enable it in `.claude/settings.json`:

```json
{
  "enabledPlugins": { "adlc-local": true }
}
```

Scripts reference themselves through `${CLAUDE_PLUGIN_ROOT}`. Never hard-code the plugin path.

**Acceptance check.** Restart the session. `/refine` and `/implement` appear in the skill
list. Both are stubs at this point; that is expected.

---

## 4. Phase 2 — The ticket contract

This is the seam between the two commands. Build it before either of them.

### The two zones

**The human zone** is the ticket description. One acceptance criterion per line, numbered
from 1, no tags and no verification markers. A human wrote it and a human owns it.

**The machine zone** is a single fenced block. Where it lives depends on the tracker:
a dedicated comment on the ticket (Jira, GitHub Issues, Linear), or a fenced block in the
ticket file (Markdown). One block per ticket. The fence marks it; nothing else may sit
beside it.

The relationship is one-way. The prose is the source. `/refine` regenerates the block every
run and never rewrites the prose. It may only append to the prose — a links section, an open
decisions section — or amend a defective criterion in place with a visible marker saying it
did so.

### The block format

Strict, flat, line-oriented YAML. Two-space indent, block style only, no flow `{}` or `[]`,
double-quoted strings. Strictness is the point: it lets the lint parse it deterministically
with no YAML runtime.

```yaml
feature: "<ticket title or key>"
repos:
  - <repo-name>
acceptance:
  - id: "AC1.api"
    surface: api
    repo: <repo-name>
    assertion: "A newly created user has notifications disabled."
    enum_boundary: "default-state partition {unset->off, on->on, off->off}; auth failures out of scope."
    irreversible: false
    binding:
      method: <method-from-surface-bindings>
    examples:
      - scenario: "Create a user, set no preference"
        outcome: "GET /preferences returns notificationsEnabled == false"
seal: "sha256:<hex>"
```

Field rules:

| field | required | meaning |
|---|---|---|
| `id` | yes | Unique. `AC<n>.<surface>` — one product criterion crossing three surfaces becomes `AC1.data`, `AC1.api`, `AC1.ui`. |
| `surface` | yes | One of the six tags. Bare word. |
| `repo` | yes | Must appear in top-level `repos`. |
| `assertion` | yes | Self-contained restatement. A reader who has not seen the prose must understand it. |
| `enum_boundary` | yes | Which partition this criterion covers, and what is out of scope. |
| `irreversible` | yes | `true` when a wrong result escapes the system boundary — sends mail, charges, notifies, writes to a third party. Default `true` when unsure. `/implement` reads it as a safety constraint: prove against a stub, never fire the real effect. |
| `binding.method` | yes | A key from `.claude/surface-bindings.json` (Phase 3). |
| `examples` | yes | At least one `{scenario, outcome}`. |

**A data field carries data. It never argues for itself.** An example is a scenario and an
outcome, nothing else — not why it was chosen, not what it demonstrates. `enum_boundary`
names the boundary; it does not restate the assertion or justify the scope. This is a rule
about content, not length. Do not infer a character budget from it; a stated cap becomes a
target, and the fix for a bloated block is deleting what does not belong in it.

### `scripts/adlc-seal.sh`

Computes `sha256` over the block body between the fences, **with the `seal:` line removed**.
Two subcommands:

- `write <file>` — compute and set the seal line.
- `check <file>` — recompute and compare. Exit 0 on match, 1 on mismatch.

### `scripts/adlc-lint.sh`

Structural validation of the block. Pure bash — no `jq`, no `yq`, no node. It runs on
whatever machine the loop runs on, including one with no toolchain installed.

It must block on:

- A malformed block — bad indent, flow style, unquoted string where one is required.
- A missing required field on any entry.
- A `surface` outside the six tags.
- A `repo` not listed in top-level `repos`.
- A duplicate `id`.
- An entry with zero examples.
- A `binding.method` absent from `surface-bindings.json`.
- A seal that does not verify.

Exit 0 clean, 1 with a specific message naming the entry and the field. Never a generic
"validation failed" — the message is read by an agent that must fix it.

**Acceptance check.** Write a valid block by hand and lint it: exit 0. Then corrupt it four
ways — delete a required field, duplicate an id, use an unknown surface, change one character
in an assertion without resealing. Each must exit 1 with a message naming what is wrong.

---

## 5. Phase 3 — Surface tags and bindings

The six tags, and what each asserts:

| tag | asserts | typical proof |
|---|---|---|
| `[api]` | A request produces a response | integration test against a running service |
| `[data]` | State persists correctly | assertion against the real database |
| `[logic]` | A pure function or rule is correct | unit test |
| `[component]` | A component renders and behaves | component test in a real browser |
| `[ui]` | A user journey works end to end | browser test against the live app |
| `[design]` | The rendered structure matches an approved design | rendered capture, judged against the reference |

`[component]` and `[ui]` must run in a real browser. A DOM-only environment neither lays out
nor paints, so it can prove what is in the DOM but never what the user sees. If this project
has no browser harness, do not fake it — record `[ui]` as unsupported and route those
criteria to `[api]` plus a manual check.

`[design]` only exists where an approved design reference exists. Omit it from this build
unless the project ships designs; it is the most involved surface and it earns its keep only
once a designer is in the loop.

### `.claude/surface-bindings.json`

One per repository, committed. It maps a binding method to a real command.

```json
{
  "repo": "<repo-name>",
  "bindings": {
    "pytest-integration": {
      "surface": ["api", "data"],
      "runner": "pytest",
      "location": "tests/integration",
      "selector": "-k <TEST_NAME> -m agent_trusted"
    },
    "playwright": {
      "surface": ["ui", "component"],
      "runner": "playwright",
      "location": "e2e",
      "selector": "--grep \"(?=.*@agent-trusted)(?=.*<TITLE>)\""
    }
  }
}
```

The selector carries the **isolation filter** from Phase 0 question 4. Note how the
Playwright example requires both the tag and the title: a test that is not tagged
`@agent-trusted` cannot be selected as a proof, by construction. Build the same property into
every binding you write. It is what stops a proof run from selecting a pre-existing passing
test.

**Acceptance check.** For each binding, run its command by hand against one existing test.
It must select exactly that test, and exit non-zero when the test fails.

---

## 6. Phase 4 — `/refine`

A user-invoked skill. Set `disable-model-invocation: true` in its frontmatter — this must
never fire on its own.

### What it does

It is an interview, not a form. It reads the ticket and the code, asks the engineer what it
cannot determine, and emits the sealed block.

**Steps:**

1. **Intake.** Fetch the ticket. Claim it — assign it to the engineer running the session.
   Record the description verbatim as a baseline before anything edits it. Confirm the repo
   scope and the base ref per repo. Read each repo's existing context: `CONTEXT.md`,
   `docs/adr/`, `.claude/surface-bindings.json`.

2. **Product pass.** Turn each abstract criterion into worked examples. Enumerate the
   scenarios, set the expected outcome for each, and record the enumeration boundary.

   Ration the questions with the **knob razor**: a question earns an interactive turn only
   when a wrong answer cannot later be fixed by changing a value. A default that is wrong and
   adjustable is a knob — set it, pin it in a worked example, and record it as `defaulted:`.
   A default that is wrong and ships something irreversible is not a knob — ask.

   The pass closes when every criterion has a confirmed example ledger. It does not close
   because the question list emptied. The initial list is a floor, never a ceiling.

3. **Design pass.** Settle the technical decisions an implementing agent would otherwise
   have to stop and ask about. **No razor applies here** — grill every flagged decision.
   Technical judgment is the scarce input, and this is where it belongs. The pass closes on
   the engineer's own judgment that nothing is left open.

4. **Tag and bind.** Assign a surface tag to each criterion. Decompose a criterion that
   crosses surfaces into one entry per surface. Bind each to a method from
   `surface-bindings.json`. A criterion that binds to nothing is flagged now, not later.

5. **Deposit.** Write the decisions into the repo as ADRs under `docs/adr/`, and update
   `CONTEXT.md`. Commit them to the shared branch from `adlc-story-branch.sh` — not to a
   separate design branch. That is what lets one PR carry both the design and the code.

6. **Emit, seal, lint.** Generate the whole block, compute the seal, run the lint. A lint
   failure is fixed before the ticket is marked ready, never after.

7. **Mark ready.** Only now does the ticket become Ready-for-Agent.

### How it talks to the engineer

This matters more than it sounds. A badly-run interview produces a ticket that looks refined
and is not.

- Plain, direct English. Short sentences, one idea each.
- **One question per message.** Ask, wait, then ask the next. Two questions in one message
  gets a worse answer to the second than it would have got alone.
- Number every question across the whole session. Never restart the count, never reuse a
  number.
- **Options before the recommendation.** Letter the candidates `A`, `B`, `C` on their own
  lines, each with its cost and benefit. Then open the recommendation with the letter it
  picks. A recommendation read before the alternatives is a nudge, not a decision — in the
  origin framework, a run that recommended in prose with no letters got three answers back as
  verbatim copy-pastes of its own recommendation.
- Drop the letters only where one candidate genuinely exists, or it is a plain yes or no.
  A second option invented to fill the list is as bad as hiding the first.

### `scripts/adlc-story-branch.sh`

One job: print the shared branch name for a ticket key.

```bash
#!/usr/bin/env bash
# The ONE home for the shared feature-branch name. /refine pushes this branch,
# /implement continues it. Two prose-driven skills deriving the name separately
# would silently split the work across two branches.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "usage: adlc-story-branch.sh <ticket-key>" >&2; exit 2; }
KEY="$1"
[[ -n "${KEY// /}" ]] || { echo "usage: adlc-story-branch.sh <ticket-key>" >&2; exit 2; }
[[ "$KEY" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "ref-unsafe ticket key: $KEY" >&2; exit 2; }
printf 'story/%s\n' "$KEY"
```

Both skills call it. Neither builds the name itself.

**Acceptance check.** Refine one real ticket. The emitted block lints clean, the seal
verifies, and every criterion has a binding that resolves to a command you ran in Phase 3.

---

## 7. Phase 5 — The proof runner

`scripts/adlc-proof.sh` is the only way a test becomes a verdict. This is the heart of the
framework. Build it carefully.

### Invocation

```
adlc-proof.sh --runner <adapter> --repo <worktree> --ac <AC-id> [options] -- <adapter args>
```

A bash core owns the tree hash, the log, no-retry-to-green, non-vacuity, and classification.
A per-harness adapter under `lib/proof-adapters/` knows only how to run one selected test and
how to tell an environment fault from a real failure. Adding a harness means adding an
adapter, never touching the core.

`--ac` is required. The runner refuses to dispatch without it — exit 2. Without it, the
verdict cannot be attributed and the mapping has to be guessed from test names.

### What the core records per dispatch

| field | meaning |
|---|---|
| `worktree_hash` | `git add -A` + `write-tree` over the whole working tree. A tripwire: it moves on **any** change, including uncommitted edits and untracked files. That is exactly what makes it the right key for no-retry-to-green. It is not comparable to a commit's tree — never compare the two. |
| `head_tree` | `git rev-parse HEAD^{tree}` — the committed tree. This is the commit-comparable anchor. |
| `tree_dirty` | Whether the two differed, i.e. whether the proof ran against uncommitted content. |
| `ac` | The criterion this dispatch proves. |
| `test_id` | The selected test. |
| `break_note` | On a deliberate red: what was made false to earn it. |

### The verdict tokens

Print `RESULT=<token>` on stdout and append one JSON line to the log.

| token | meaning | exit |
|---|---|---|
| `proven` | Green at this tree hash, with a prior genuine red for this test somewhere in the log. Non-vacuity shown. | 0 |
| `green-no-red-observed` | Green, but this test never logged a genuine red at any hash. Non-vacuity **not** shown. | 0 |
| `red` | The test ran and failed. | 1 |
| `flaky-refused` | A green refused because the same test went red at this same hash earlier. No-retry-to-green. | 1 |
| `build-error` | The runner failed to compile or load. Never red, never proven, and **never counts as a prior red**. | 1 |
| `infra-exempt` | The harness demonstrably did not run — environment fault. | 0 |
| `timed-out` | The dispatch exceeded its bound and was killed. Never red, never proven, never a prior red: a run that did not finish said nothing about the code. | 1 |

Only `proven` counts. `green-no-red-observed` is a distinct state on purpose — it is what a
test written after the code looks like, and it must be visible rather than rounded up.

### The log

```
${ADLC_LOG_HOME:-$HOME/.adlc}/<sanitized-repo-path>/proof-log.jsonl
```

Append-only. **Outside the worktree.** This is not a detail. A log inside the worktree is
erased by a `git clean`, a branch switch, or a fresh worktree — and every one of those
happens during a normal run.

### The overrides

Three escape hatches. Each takes required prose, is logged, and is surfaced in the report.
Each is single-dispatch only — blanket prose over a batch is not an audit trail.

- `--no-red-reason "<prose>"` — promotes `green-no-red-observed` to `proven`. Use when
  non-vacuity is argued some other way, for example the test provably fails against the
  pre-change tree you already saw.
- `--accept-green "<prose>"` — accepts a green that no-retry-to-green refused.
- `--infra-exempt "<prose>"` — forces a red to `infra-exempt`.

Make them awkward enough to be deliberate and visible enough to be audited. An override with
no prose is not an override; it is a bypass.

### The wall-clock bound

Every dispatch runs under a hard timeout — `--timeout-secs`, defaulting to 1800. The bound
lives in the process the runner starts, not in the calling harness. In the origin framework a
smoke test described as taking about nine seconds hung on a failing bootstrap and returned
thirteen hours later, blocking three levels of agents for the whole run. On expiry: TERM,
then KILL after 30 seconds, stamp `timed-out`, exit 1. The leg reads a failed check and
carries on.

**Acceptance check.** Four tests against a real test in this project:

1. Dispatch a test that fails → `RESULT=red`, exit 1, one log line.
2. Fix the code, dispatch again → `RESULT=proven`, exit 0.
3. Dispatch a test that has always passed, no prior red → `RESULT=green-no-red-observed`.
4. Dispatch a red, then without changing one byte dispatch it again as green →
   `RESULT=flaky-refused`.

If test 4 returns `proven`, the tree hash is wrong. Fix it before going further. That check
is the whole guard.

---

## 8. Phase 6 — `/implement` and the agent hierarchy

A user-invoked skill, `disable-model-invocation: true`, run unattended.

### The loop

1. **Claim — the only hard gate.** Fetch the ticket. Verify it is Ready-for-Agent, extract
   the block, run the lint, verify the seal. Any failure stops the run here with a clear
   message. Everything downstream trusts this gate, so nothing downstream re-checks it.

2. **Group by repo.** Split the criteria by their `repo` field. Derive the shared branch with
   `adlc-story-branch.sh`.

3. **Dispatch one repo agent per repo**, concurrently.

4. **Build the report** from the proof log — the log is the source of truth, not the agents'
   summaries.

5. **Open one PR per repo**, carrying the report.

6. **Transition the ticket** and hand off.

### The hierarchy, and why it has four levels

This is the part most likely to be dismissed as over-engineering. It is not. It is a context
budget made structural.

```
depth 0  orchestrator          claims, gates, reports, opens PRs
depth 1  implement-repo        one per repo, owns a worktree and a branch
depth 2  implement-prover      one per slice of criteria, serial
depth 2  review agents         fresh context, read the accumulated work
depth 3  proof-investigator    spawned only on a stubborn red
```

The rule at every level: **a child returns a verdict, never a transcript.**

A prover writes a test, watches it fail, implements, watches it pass, debugs the three reds
in between, and returns one line per criterion: proven or flagged. The reds, the stack
traces, the browser snapshots, the half-written implementations — all of that dies with the
child's context. The repo agent never sees it.

This is why the repo agent does not prove criteria inline. A context window cannot be
monitored at runtime, so you cannot react when it fills. You bound it structurally instead:
hold only a compact map, push every author-fail-fix cycle into a child.

Each agent needs an explicit `tools:` list. The repo agent needs `Agent` in its list or it
cannot spawn provers — losing that line is a common and confusing failure.

### What the repo agent owns

Its worktree, its branch, its slice sizing, its review dispatch, and its push. It does **not**
open PRs and does **not** touch the tracker — the orchestrator does both, from the log.

Give it a heartbeat: one line appended to a file outside the worktree at the start of each
step, naming the phase. During a long silent stretch it is the only way a human can tell a
working run from a hung one. Best-effort — if the write fails, keep working. A missing
heartbeat never flags a criterion.

**Acceptance check.** Run `/implement` on the ticket refined in Phase 4. It must claim,
split by repo, prove each criterion through the runner, and open a PR. Every criterion in the
report must have a matching line in the proof log. A criterion reported proven with no log
line is the failure this whole design exists to prevent.

---

## 9. Phase 7 — Review gates and the PR rule

After proving, before pushing, the repo agent spawns review agents with fresh context. Fresh
matters: an agent that watched the code being written cannot judge it cold.

| agent | reads | asks |
|---|---|---|
| `standards-review` | The changed diff against the project's written standards | Does this violate a rule the project wrote down? Run it **first**, so its fixes land before the others judge the tree. |
| `test-review` | The changed proof tests and the code they exercise | **Would this test fail if the behavior broke?** |
| `code-review` | The changed source, not the tests | Is there behavior reachable in its default state that is wrong? An error swallowed into a benign empty state? A silent write failure? |

`test-review` is the most valuable of the three. A test that passes and would also pass if
the feature were deleted is worse than no test, because it reports success. Give it the
`break_note` from the proof log so it can judge whether the observed red showed the assertion
biting, or merely that the endpoint did not exist yet.

### The PR rule

Review findings are **advisory to the build loop** — they never block the agent from
finishing. But a confirmed defect **forces that repo's PR to draft**.

That is the whole mechanism. The run always completes and always produces something to look
at. A clean run opens a ready PR. A run with a real finding opens a draft one, so a human
looks before merge. Nothing is silently dropped and nothing is silently merged.

A `test-review` flag additionally downgrades that criterion's verdict. It does not read
proven until a human has looked.

**Acceptance check.** Introduce a deliberate defect — swallow an error into an empty success
response. Run `/implement`. The PR must open as a draft, and the finding must name the defect.

---

## 10. Phase 8 — Verify the loop end to end

Take one real ticket through both commands. Then check the things that distinguish a working
loop from a loop that merely ran:

1. **The seal is load-bearing.** Edit one character in the emitted block. `/implement` must
   refuse to start.
2. **Non-vacuity is real.** Pick a criterion reported `proven`. Find its red in the proof log
   and confirm the red came before the green at a different tree hash.
3. **The report matches the log.** Every criterion in the PR body has a log line. No
   exceptions — this is the check that catches a run reporting work it did not do.
4. **A flagged criterion survives.** Refine a ticket with one criterion that cannot be
   proven. The run must complete, open a PR, and name the flagged criterion in the report.
5. **A defect drafts the PR.** The Phase 7 check, run as part of the whole loop.

If check 2 or check 3 fails, stop and fix the runner. Those two are the difference between a
proof framework and a framework-shaped set of prompts.

---

## 11. What was left out, and the order to add it

This build is the core loop. The origin framework has about twenty skills. Most of them only
pay off once a team, a product manager, and a backlog are in the loop. Added too early, they
sit unused and bury the two commands that matter.

Add them in this order, each only when its absence actually hurts:

1. **`/drift-report`** — after a run, cold-read the diff for structural decisions the agent
   made that no specification dictated. Route each to promote, accept, or overrule. Add this
   first. It is how the architecture stays yours rather than drifting into whatever the model
   found convenient.

2. **`/repo-map-update`** — carry the durable machinery lessons from a run into a tracked
   `docs/agents/repo-map.md`, so the next run does not rediscover how to boot the stack.

3. **`visual-review`** — judges captured screenshots against an approved design. Add it when
   the project ships designs and `[design]` becomes a real surface.

4. **Epic-level skills** — `/prd`, `/to-epics`, `/to-stories`, `/tech-design`. These serve a
   product manager and a backlog. Add them when more than one person is filling the queue.

5. **`/work-queue`** — a pull-based queue for the product decisions `/refine` flagged. Add it
   when a product manager is answering those asynchronously.

### Two things to resist

**Do not soften Rule 3.** The first time a run is blocked by `flaky-refused`, there will be a
strong temptation to make the guard advisory. Use the override with prose instead. The
override is logged and visible; a weakened guard is neither.

**Do not let the model do what bash should.** Every time a gate gets rewritten as an
instruction — "verify the seal before proceeding" instead of `adlc-seal.sh check` — the loop
gets less trustworthy in a way that will not show up until a run quietly reports work it did
not do.