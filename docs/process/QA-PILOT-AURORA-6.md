# QA stage pilot — AURORA-6 (booking time zone)

The first trial of the QA stage we plan to add to ADLC (`/adlc:qa`). The stage was run **by hand**,
because the command does not exist yet. It used the improved `qa-tester` and `qa-reviewer` agents
from `qa-ai-toolkit` (branch `feat/qa-agents-v2`).

## What was tested

- **Story:** [AURORA-6](../tickets/AURORA-6.md), "Booking times stay in the clinic's time zone for
  every viewer". It has 5 acceptance criteria.
- **The code:** written **by a developer, outside ADLC**, and merged as appointments-web#18. So
  this was the "the dev team already built it" case.
- **Independence:** the QA agents saw only the acceptance criteria and the app. They did not see
  the developer's tests, the fix note, the PR text or the fix diffs. Two small slips are listed
  under lessons.
- **Target:** `main` @ `02551d9`. **Base for the red check:** `98dc338`, the commit before the fix.

## How it ran

| # | Step | Agent | Result | Time |
|---|---|---|---|---|
| 1 | UI tests on the mock backend | qa-tester | 13 tests, all green on `main`; 12 of 13 red on the old code, each on its own assertion; 5 own test mistakes fixed; 0 bugs, 1 question | 23 min |
| 2 | Review of run 1 | qa-reviewer | "0 bugs" became **1 bug**: the question was really a bug against the AC wording. AC5 was **not tested for the product** (only the mock's copy of a server rule). Coverage gaps listed. | ~4 min |
| 3 | Decision | QA manager | BUG-1 approved → filed as [AURORA-7](../tickets/AURORA-7.md) | — |
| 4 | API tests for AC4 and AC5 on the real API (Docker) | qa-tester | 11 tests, all green; no bugs | ~5 min |
| 5 | Review of run 4 | qa-reviewer | 4 test mistakes. The worst: the new file would have **broken CI**, which I confirmed. One test usually **checked nothing**. | ~2 min |
| 6 | Fix round | qa-tester | All 4 fixed; 13 API tests, 0 skipped at run time | ~5 min |
| 7 | Review of run 6 | qa-reviewer | 3 of 4 fixed, 1 partly: the Kiritimati test still checks no started slot from 10:00 to 16:00 UTC, but the new run-time zone test now covers that check at every hour. Both new tests valid. List order: out of scope, not a blocker. | ~2 min |

## Numbers

| | |
|---|---|
| Acceptance criteria | 5 |
| Automated tests written | 26 (13 UI on the mock, 13 API on the real stack) |
| UI tests red on the old code | 12 of 13 (the 13th is the correct "do not hide too early" check) |
| Real bugs found | **1** (AURORA-7: the time slots do not name the zone). The developer's own tests missed it. |
| False bugs reported | **0** |
| Test mistakes found by the tester itself | 6 |
| Test mistakes found **only by the reviewer** | 8 (run 1: 3, including the misclassified bug; run 4: 4; plus 1 wrong claim, below) |
| Wrong claims by the tester | 1 ("`dist-demo/` is not in `.gitignore`" — it is) |
| Product questions left | 2 (exact "now" for a started slot; overlapping slots of different services). List order is out of scope. |
| Total agent time | about 45 minutes, plus waiting time. 3 tester runs and 3 reviewer runs. |

## What we learned

**The approach works, but only with the reviewer.** Both "all green" tester runs had hollow parts.
The reviewer found the only real bug, showed that one criterion was not tested at all, and stopped
a CI break. A tester without a reviewer would have given us false confidence twice.

Lessons, and where each one went:

| Lesson | Applied in |
|---|---|
| A subagent cannot write its report file. The caller must save it, once. | qa-tester; must be in `/adlc:qa` |
| The same report can arrive several times. Take it once. | must be in `/adlc:qa` |
| A UI test on a mock that copies a server rule tests the mock, not the product | qa-tester, qa-reviewer, QA_CONTEXT |
| Compare against fixed expected values, not only against the system's own output | qa-tester, qa-reviewer |
| A loop over an empty list must not pass | qa-tester, qa-reviewer |
| Real-clock tests skip at some hours. The report must name the windows. | qa-tester, qa-reviewer |
| A test that needs a special target must not be collected by the default run (CI) | qa-tester, qa-reviewer, QA_CONTEXT (`*.api.ts`) |
| The composed stack needs `API_DIR` when run from a worktree | QA_CONTEXT |
| The composed seed clinic is UTC, the mock's is Los Angeles | QA_CONTEXT |
| The red check can be fooled by a server already running on the port | qa-tester (stop it, or build the base) |
| A demo server on port 4173 blocked the run. It had to be stopped, with the user's OK. | the port should be configurable in `playwright.config.ts` |
| Independence slips: the tester's grep showed a few lines of a journey test, and the reviewer read parts of the fix diff. Neither took expected values from them. | rule text only; a real block needs a sparse worktree |

## Is it ready to become `/adlc:qa`?

**Yes, as a design.** It found a real bug that people missed, with no false bugs, and every weak
test was caught before anyone trusted it.

**Not yet proven enough to trust alone.** It ran on one story, by hand, and its cost depended on
reviewer rounds. Next:
1. Build `/adlc:qa` with the lessons above: save the report once, tester → reviewer → fix round →
   reviewer, then the bug drafts for approval.
2. Try the bug path on AURORA-7 (`/adlc:refine`, then `/adlc:implement`), then `/adlc:qa` again.
3. Run it on one ADLC-built story (resume AURORA-5) and compare.
