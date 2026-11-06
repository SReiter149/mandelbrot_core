# Mandelbrot: mathematics and browser UI

One checkout contains Sam's **human-written mathematics and Sage plotting functions** in `core_code/`, existing core tests in `tests/`, and the **AI-written UI and HTTP adapter** in `ui/`. Agents treat core code and existing core tests as read-only; see [AGENTS.md](AGENTS.md). Agent changes go through feature branches and Sam-reviewed PRs, not direct pushes to `main`.

```text
mandelbrot_core/
├── core_code/          # human-written mathematics and plotting; agent read-only
├── tests/              # existing core tests; agent read-only
├── ui/                 # browser UI, server, launcher, UI tests, archived design notes
├── deployment/         # portable Mac service setup and tests (no credentials)
├── environment.yml     # conda-forge Sage environment specification
└── .github/CODEOWNERS  # Sam reviews all files
```

## Local setup

Install [Miniforge](https://github.com/conda-forge/miniforge) for your machine architecture. Sage supports Intel and Apple Silicon via conda-forge; the full Intel/Ventura deployment still needs validation on that machine. Do not copy this Mac's installed environment to another architecture.

```bash
git clone https://github.com/SReiter149/mandelbrot_core.git
cd mandelbrot_core
conda env create -f environment.yml
conda activate mandelbrot
SAGE_PYTHON="$CONDA_PREFIX/bin/python" bash ui/launch.sh
```

Open **http://127.0.0.1:8124**; stop a foreground run with **Ctrl+C**. `PORT=8126` selects another port. Existing `SAGE=/absolute/path/to/sage` discovery is retained for Sage CLIs supporting `-python`. Ordinary Python cannot run the server. No npm build or separate core/UI checkout is required.

See [ui/README.md](ui/README.md) for controls and tests. Local-launch caches stay in `ui/.runtime/`.

## Public hosting on the old Mac

Follow [deployment/README.md](deployment/README.md) for Intel/Ventura setup, Cloudflare authorization, generated login services, start/stop/restart, and safe hostname cutover. Install dependencies and machine-specific service settings once; credentials remain outside the repository. Setup does not automatically move the live domain or alter existing services.

After setup, use a separate hosting checkout tracking approved `main`:

```bash
git pull --ff-only
python3 deployment/macos_service.py restart app
```

This reloads saved core/server changes. The tunnel normally stays running. Dependency changes require `conda env update -f environment.yml`; generated plist changes require unloading/reloading the affected service as documented. Keep the host awake, online, and logged in. `status` reports launchd state, not application health; also check `curl -f http://127.0.0.1:8124/api/health` and test the browser.

## Verification

The combined API/streaming tests run locally with SageMath 10.9, with real core helpers rather than replacement math. Frontend, launcher, layout, and deployment configuration tests are included. This is not a claim of Intel/Ventura validation or GitHub CI coverage. Service tests do not activate real LaunchAgents.

## Import provenance

The baseline UI was imported from committed `SReiter149/mandalbrot_UI` commit **`3deaccd4611c0d245b7a507e7e7c33531b3446b4`**, with combined-checkout path adaptations. Historical test screenshots and the obsolete external-core hash inventory were omitted. The follow-up brings over the locally developed signed pullbacks, minimap, rendering changes, public HTTP origin support, and portable hosting tools. Existing core math, root tests, and `CODEOWNERS` are unchanged; Sam's uncommitted math changes are not bundled.

`ui/docs/` is archived design history, not current setup guidance. Use this README, `ui/README.md`, and `deployment/README.md` for current commands.
