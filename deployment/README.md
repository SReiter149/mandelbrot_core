# macOS hosting (one checkout)

For an Intel Mac on Ventura: one combined repository, a conda-forge Sage Python,
and a locally managed Cloudflare Tunnel. No Docker, root daemon, external core
checkout, or Homebrew requirement. **Intel/Ventura end-to-end operation has not
been tested here**; verify the package solve, Sage import, local app, and downloaded
binary on that Mac before moving production traffic. Runtime is intentionally
uncapped: slow math may take a long time; this setup adds no queue or limits.

## 1. Sage and the checkout

Install [Miniforge](https://github.com/conda-forge/miniforge#install) using the
**Darwin-x86_64** installer (not arm64). Follow upstream checksum verification
and shell initialization instructions. Git must also be available. Example:

```sh
curl -fLO https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Darwin-x86_64.sh
# Verify the installer against the checksums on the official release page first.
bash Miniforge3-Darwin-x86_64.sh
# Open a new terminal after shell initialization.
git clone https://github.com/SReiter149/mandelbrot_core.git
cd mandelbrot_core
# Use approved main AFTER the consolidation/hosting PRs have merged.
conda env create -f environment.yml
conda activate mandelbrot
export SAGE_PYTHON="$CONDA_PREFIX/bin/python"
"$SAGE_PYTHON" -c 'import sage.all'
bash ui/launch.sh --port 8124
```

Open `http://127.0.0.1:8124` and exercise the app before continuing. Stop the
foreground app with Ctrl-C before starting the LaunchAgent on that port. Do not
force an Apple Silicon build or override conda's macOS compatibility checks if
an Intel/Ventura solve fails. The environment spec intentionally has no exported
platform-specific build pins; record a working package set separately if desired.

Treat this old-Mac hosting checkout as **read-only approved-main deployment**:
no local code edits, commits, feature work, or force resets. Its only writes
should be ignored `.runtime/` files. Develop and review changes elsewhere; pull
approved main here. Existing Git agent authentication is separate from Cloudflare.

## 2. Cloudflare Tunnel

Use the [official macOS downloads](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/#macos):
choose [Darwin amd64](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz)
for Intel. Verify release checksums, extract the executable, put it at a stable
user-owned path (for example `$HOME/.local/bin/cloudflared`), make it executable,
and run `--version`. Homebrew is optional; its current Ventura support must not
be assumed. Do not use `cloudflared service install` alongside these agents.

Follow the [locally managed tunnel guide](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/local-management/create-local-tunnel/).
Replace placeholders below; keep credentials outside the repository:

```sh
CLOUDFLARED="$HOME/.local/bin/cloudflared"
"$CLOUDFLARED" --version
"$CLOUDFLARED" tunnel login
"$CLOUDFLARED" tunnel create '<TUNNEL_NAME>'
# Record its UUID and the generated ~/.cloudflared/<UUID>.json path privately.
```

**Existing-domain cutover:** `samreiter.com` may already serve the current Mac.
Inspect current DNS, tunnel connectors, LaunchAgents, and local port usage first.
Do NOT blindly route that hostname to a new tunnel or use a DNS overwrite flag.
Test a separate hostname/new tunnel first; schedule an explicit DNS cutover with
a rollback plan only after local and tunnel checks succeed. Route a hostname
only after confirming it is unused or its migration has been approved:

```sh
"$CLOUDFLARED" tunnel route dns '<TUNNEL_UUID>' '<APPROVED_HOSTNAME>'
```

Alternatively, reusing the same tunnel credentials on both Macs creates replicas;
this is optional, not required. Cloudflare may send traffic to either connector:
keep app versions/configuration compatible, and retire the old connector only
after verification. Replica setup does not require rewriting existing DNS.
Never commit or paste tunnel JSON, tokens, or the login certificate into Git.

## 3. Write configs, then explicitly start

**If migrating a machine that already has the earlier setup:** the old agents
are named `com.samreiter.mandelbrot.app` and `com.samreiter.mandelbrot.tunnel`;
this tooling manages the new `org.mandelbrot.*` agents only. It does not stop the
old agents. Before installing/starting replacements, explicitly unload the old
ones and preserve their plists/config for rollback. Do not run both app services
on port 8124. In particular, `install` replaces `~/.cloudflared/mandelbrot.yml`,
which the earlier tunnel also uses; do not install over an active old setup.
On a fresh old-Mac setup these earlier agents normally do not exist.

Run inside the one combined checkout with the Sage environment activated:

```sh
python deployment/macos_service.py install \
  --python "$CONDA_PREFIX/bin/python" \
  --cloudflared "$CLOUDFLARED" \
  --tunnel-id '<TUNNEL_UUID>' \
  --credentials-file "$HOME/.cloudflared/<TUNNEL_UUID>.json" \
  --hostname samreiter.com --port 8124
plutil -lint "$HOME/Library/LaunchAgents/org.mandelbrot.app.plist" \
  "$HOME/Library/LaunchAgents/org.mandelbrot.tunnel.plist"
python deployment/macos_service.py start
python deployment/macos_service.py status
```

Use your approved test hostname instead of `samreiter.com` before cutover.
`install` checks executable paths and `import sage.all`, writes both plists and
`~/.cloudflared/mandelbrot.yml`, and **does not load/restart services or alter DNS**.
It replaces these three files if they already exist; back up relevant configs
before changing them. The YAML file uses JSON syntax (a YAML subset) for safe
quoting. It references the credentials path but never reads credentials or uses
a token. The app runs the supplied Python directly, with `PUBLIC_ORIGIN=https://<hostname>`.
Caches/logs live in ignored root `.runtime/`; logs are not automatically rotated.

LaunchAgents belong to the logged-in user (`gui/<uid>`), with KeepAlive and
RunAtLoad. They may start at **future GUI logins even if install was not followed
by start**; they are not boot-time system daemons. Keep the hosting user logged
in and the Mac awake/online; sleep/logout interrupts availability. FileVault may
require an interactive login after reboot. Never use sudo for these commands.

`start|stop|restart|status [app|tunnel|all]` default to both services. `status`
prints launchd details and returns nonzero for unloaded agents; it is not an HTTP
health probe. `stop` unloads the agents for this session (not permanent removal
from future logins). Before moving/deleting the checkout, stop both and remove
their two plist files if permanent removal is intended. No other agents are touched.
`--help` and each subcommand's `--help` describe arguments. Pure `generate_config`
can preview configuration without writes; `install --home <temporary-directory>`
is an isolated output option for tests, **not** a launchd sandbox. Do not run
lifecycle commands for a test home: they still address the real user's GUI domain.

Verify `curl -f http://127.0.0.1:8124/` and `curl -f https://<APPROVED_HOSTNAME>/`,
then exercise real math in the browser. Check `.runtime/logs/` if either fails.
A running tunnel alone does not prove that Sage or the app works.

## 4. Updates

From the unchanged approved-main checkout:

```sh
git pull --ff-only
python deployment/macos_service.py restart app
python deployment/macos_service.py status app
curl -f http://127.0.0.1:8124/
```

The tunnel normally stays running. If environment dependencies changed, activate
`mandelbrot`, run `conda env update -f environment.yml`, verify Sage import, then
restart the app. If paths, port, hostname, or generated plist settings changed,
rerun install, then `stop app` and `start app` to reload its plist (kickstart alone
does not reload plist changes); reload the tunnel only when its settings change.
Do not pull with local modifications or bypass a failed fast-forward.

## Tests (no live service activation)

```sh
python3 -m unittest discover -s deployment/tests -v
```

Tests use temporary roots/homes, plistlib roundtrips and macOS `plutil -lint`.
Sage verification and launchctl are mocked in lifecycle/install unit tests;
actual Sage startup and Intel/Ventura compatibility still need target-Mac checks.
