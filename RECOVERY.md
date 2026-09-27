# Recovery — continue the build on a new/formatted machine

This restores the whole Aurora project from the private GitHub backups and lets you pick up at the
next milestone. Everything is under the personal account **evg-g**.

## 0. Prerequisites — install the toolchain (not in git)

Work inside the WSL2 Linux filesystem (`~/`), never `/mnt/c` or OneDrive — Docker and
testcontainers need it. Matching major versions are enough (Python 3.12, Node 20); `uv.lock` and
`package-lock.json` pin the actual dependencies.

**On Windows (PowerShell, once):**

```powershell
wsl --install -d Ubuntu-24.04
```

Then install **Docker Desktop for Windows** and turn on
**Settings → Resources → WSL integration → Ubuntu-24.04**.

**Inside Ubuntu-24.04 (bash):**

```bash
# make/gcc, git, curl
sudo apt update && sudo apt install -y build-essential git curl

# uv (Python package + venv manager) -> installs into ~/.local/bin
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc                       # or open a new shell, so ~/.local/bin is on PATH

# Python 3.12 (uv manages it; system Ubuntu-24.04 also ships 3.12)
uv python install 3.12

# Node 20 via nvm (check github.com/nvm-sh/nvm for the current install line)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.bashrc
nvm install 20 && nvm alias default 20

# git identity
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# verify everything is present
uv --version && node --version && python3 --version && git --version \
  && make --version && docker info | head -1
```

## 1. Authenticate to GitHub (needed before cloning — the repos are private)

Create a Personal Access Token on **evg-g** with `repo` + `workflow` scope, then store it so git
uses it over HTTPS:

```bash
# WSL, token read silently
read -s T && printf 'https://evg-g:%s@github.com\n' "$T" > ~/.gh_personal && chmod 600 ~/.gh_personal && unset T
git config --global credential.helper "store --file ~/.gh_personal"
```

(Or set up an SSH key on evg-g and use the SSH clone URLs instead.)

## 2. Clone the meta repo AS the project folder, then the code repos inside it

```bash
cd ~
git clone https://github.com/evg-g/aurora.git aurora      # restores PLAN.md, HANDOVER, this file
cd ~/aurora
git clone https://github.com/evg-g/appointments-api.git
git clone https://github.com/evg-g/appointments-web.git
git clone https://github.com/evg-g/aurora-sensor-agent.git
```

The meta repo's `.gitignore` already excludes the three code dirs, so it stays clean.

## 3. Restore dependencies

```bash
cd ~/aurora/appointments-api && make setup     # uv sync from uv.lock
cd ~/aurora/appointments-web && npm ci         # from package-lock.json
cd ~/aurora/aurora-sensor-agent && make setup  # (or: uv sync --extra dev)
```

## 4. Verify, then continue

```bash
# Start Docker first (integration tests use real Postgres + Redis via testcontainers).
cd ~/aurora/appointments-api
make ci-local          # ruff + mypy + unit tests, should be green
make test-integration  # spins up Postgres + Redis containers
```

Then open Claude Code from `~/aurora` and say:

> Read HANDOVER.md and PLAN.md, then continue from the next unchecked milestone.

## Notes

- **Pushing backups again:** the three code repos and this meta repo already have `origin` set to
  `evg-g` in the pushed history, but a fresh clone sets `origin` for you. After each milestone,
  `git push` in the changed code repo AND `git -C ~/aurora push` (so PLAN.md's progress is backed
  up).
- **Not restored (and not needed):** Claude Code's auto-memory. It only held environment notes,
  which this file and HANDOVER already cover.
