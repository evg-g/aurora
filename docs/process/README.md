# How this project was built

These are the working files behind the build, kept in the open on purpose. The project was built
end to end with [Claude Code](https://claude.com/claude-code) as the working environment; these files
show the process — the spec it started from, how progress was tracked, and how the work is carried
between sessions and machines.

| File | What it is |
|---|---|
| [`CLAUDE_CODE_BOOTSTRAP_PROMPT.md`](CLAUDE_CODE_BOOTSTRAP_PROMPT.md) | The original spec: the product, the three repos, the test tiers, CI/CD, and the milestone order. |
| [`PLAN.md`](PLAN.md) | The build plan and progress log — all 16 milestones, what each delivered, and what was verified. |
| [`HANDOVER.md`](HANDOVER.md) | Project context for picking the work up in a new session: goals, why this domain, the decisions already settled, and the bar the project was held to before publishing. |
| [`RECOVERY.md`](RECOVERY.md) | How to restore the whole project on a new machine: toolchain, GitHub auth, clone layout, and setup. |
| [`ADLC-SETUP.md`](ADLC-SETUP.md) | The build order for ADLC, the `/refine` → `/implement` proof loop now used for new work on Aurora. Written as instructions to an agent. |

For the project itself, start at the [top-level README](../../README.md).
