# Recovery — continue the build on a new/formatted machine

This restores the whole Aurora project from the private GitHub backups and lets you pick up at the
next milestone. Everything is under the personal account **evg-g**.

## At a glance

1. **Install the toolchain** — VS Code, Claude Code, WSL2 Ubuntu-24.04, Docker Desktop, and inside WSL
   `git`, `uv`, Node 20, Python 3.12, `make`/`gcc` (§0).
2. **Authenticate to GitHub** — a PAT or an SSH key, **before** cloning; the repos are private and will
   not clone without it (§1).
3. **Clone** the meta repo and the three code repos inside it (§2).
4. **Restore dependencies** — `make setup` / `npm ci` (§3).
5. **Verify** — `make ci-local`, then `make test-integration` (§4).
6. Behind a corporate proxy, add the CA and set the cert env vars (§5); for the full test tiers, build
   the API image and install Playwright (§6).

Then launch Claude Code from `~/aurora` and say:
*"Read RECOVERY.md, HANDOVER.md and PLAN.md, then set up this machine."*

## One-prompt restore with Claude Code

If Claude Code is already installed and running inside WSL, you can hand it the whole clone + setup in a
single prompt instead of doing steps 1–4 by hand.

Prerequisites Claude **cannot** do for you (its own runtime and anything needing `sudo`): WSL2
Ubuntu-24.04, Docker Desktop, Claude Code, and `git` in WSL must already exist. Launch `claude` inside
the WSL shell, then paste the prompt below with your token in place.

Token safety: give the PAT **`repo` scope only**, and **revoke/rotate it after** the restore. To avoid
pasting the token into the session at all, run `gh auth login` yourself first (`! gh auth login`) and
drop step 1 from the prompt.

> I'm restoring a project on a freshly formatted machine. Here is a GitHub Personal Access Token for my
> private account **evg-g**: `<PASTE_TOKEN>`. Do this:
> 1. Configure git to use it over HTTPS (store it in `~/.gh_personal` with the credential helper; do not
>    echo the token back).
> 2. Clone `evg-g/aurora` into `~/aurora`, then clone `evg-g/appointments-api`,
>    `evg-g/appointments-web`, and `evg-g/aurora-sensor-agent` inside `~/aurora`.
> 3. Read `RECOVERY.md`, `HANDOVER.md`, and `PLAN.md`, then follow RECOVERY.md to set this machine up —
>    run `make setup` in each repo and `make ci-local` to verify. Hand me any `sudo`/manual steps to run
>    myself, and stop if a prerequisite (Docker, uv, Node, Python) is missing.

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

**Do §1 (GitHub auth) first** — these are private repos and the clone fails without credentials.

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

**Run Claude Code from inside the WSL shell** (launch `claude` in the Ubuntu terminal at `~/aurora`),
so it operates directly on the Linux filesystem. If you instead run Claude Code on the Windows side
driving WSL, be aware of the execution quirks in the last section.

## 5. If you are behind a corporate TLS-inspecting proxy

The build was done behind such a proxy. On a **clean home network you can skip this whole section** —
nothing here is needed. Behind a corporate proxy, HTTPS is re-signed with a private CA that the tools
do not trust by default, so package installs and browser downloads fail with certificate errors.

**Add the corporate root CA to the system store (once):**

```bash
# WSL — copy your corp root CA (.crt, PEM) in, then:
sudo cp corp-root-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates          # adds it to /etc/ssl/certs/ca-certificates.crt
```

**Then point each tool at the system store** (these belong in your shell, e.g. `~/.bashrc`, never in
the repo):

```bash
export SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
export REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
export NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt   # npm + Playwright download
export UV_SYSTEM_CERTS=1   # uv's rustls ignores SSL_CERT_FILE; this makes it use the OS store
                           # (older uv: UV_NATIVE_TLS=1, now deprecated)
```

Without `UV_SYSTEM_CERTS=1`, `make setup` (`uv sync`) fails with `invalid peer certificate:
UnknownIssuer`. Details per repo: `appointments-api/docs/CORPORATE_NETWORK.md` (uv/pip + the Docker
`EXTRA_CA_CERT` build arg) and `appointments-web/docs/BROWSER_TESTING.md` (Playwright).

## 6. Extra setup for the full test tiers

The core gate (`make ci-local`) needs none of this, but the heavier tiers do:

- **Docker images** — the integration/SIL tiers pull `postgres:16`, `redis:7`, and
  `eclipse-mosquitto:2` automatically via testcontainers (first run is slow).
- **The `appointments-api:local` image** is needed by the device **SIL** tier and the web
  **composed-stack E2E**. Build it from current source, and rebuild it whenever the API changes — a
  stale image is a real gotcha (a pre-telemetry image has no MQTT worker and the SIL worker container
  dies):
  ```bash
  docker build -t appointments-api:local ~/aurora/appointments-api
  # behind the proxy: add --build-arg EXTRA_CA_CERT="$(cat corp-root-ca.crt)"
  ```
- **Playwright browsers** (web browser tiers — E2E, a11y, visual, Lighthouse):
  ```bash
  cd ~/aurora/appointments-web && make setup-e2e     # npx playwright install chromium
  ```
  Behind the proxy, Chromium also needs three system libs. Either
  `sudo apt-get install -y libnss3 libnspr4 libasound2t64`, or the no-sudo route: `apt-get download`
  those three, `dpkg -x` each into `~/pwlibs`, then
  `export LD_LIBRARY_PATH=~/pwlibs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH`. See
  `appointments-web/docs/BROWSER_TESTING.md`.
- **sudo** in WSL needs your password — run the `apt`/`update-ca-certificates` lines yourself.

## Notes

- **Pushing backups again:** the three code repos and this meta repo already have `origin` set to
  `evg-g` in the pushed history, but a fresh clone sets `origin` for you. After each milestone,
  `git push` in the changed code repo AND `git -C ~/aurora push` (so PLAN.md's progress is backed
  up).
- **Claude Code's auto-memory is NOT in git** and is wiped by a format. Its useful content — the
  toolchain versions, the corporate-CA env above, the `appointments-api:local` staleness gotcha, and
  the Playwright system-lib workaround — is now captured in this file and the per-repo docs, so a fresh
  clone is self-sufficient. If a future session adds new environment knowledge to memory, fold it back
  into this file so it survives the next format.
- **Driving WSL from a Windows-hosted Claude Code** (only if you don't run `claude` inside WSL): call
  WSL via `MSYS_NO_PATHCONV=1 wsl -d Ubuntu-24.04 bash /home/<user>/script.sh`; write commands to a
  script file rather than inlining them (PowerShell mangles `$VAR`/quotes/heredocs on the way through);
  edit WSL files via the `\\wsl.localhost\Ubuntu-24.04\home\<user>\...` path; and in non-login scripts
  `export HOME=/home/<user>` and source nvm, because `$HOME` is unset there.
