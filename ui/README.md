# Mandelbrot UI

A local browser UI for the SageMath functions in this checkout’s `../core_code/`. The core owns all mathematics and Sage plotting functions; this repository supplies controls, browser presentation, and HTTP transport. Core sources are loaded directly, not copied.

> **AI-written UI / human-written mathematics:** This package contains the AI-written interface and supporting server. Sam’s human-written mathematics and Sage plotting functions remain separately organized in the root `core_code/` directory of the same checkout.

## Requirements

- This combined checkout, including `../core_code/` and its dependencies.
- SageMath with Python 3.9 or later. The consolidated API and streaming tests pass locally with SageMath 10.9; the source UI also documented testing with 10.7. Other platforms/versions are not verified.
- Bash and a modern browser.
- Node.js only if you want to run the frontend tests.

Ordinary Python is **not** enough: the server imports Sage and must run through Sage's Python. No FastAPI, Uvicorn, npm install, or separate frontend build is required.

## Combined checkout layout

```text
mandelbrot_core/
├── core_code/          # human-written mathematics; read-only for agents
├── tests/              # existing core tests; read-only for agents
└── ui/
    ├── launch.sh
    └── code/web/server.py
```

No separate sibling repository is required. With `ROOT` set to `ui/`, the server uses `CORE_DIR = ROOT.parent / 'core_code'`. There is no core-path override.

## Choose SageMath and start

On macOS with Homebrew, from the combined repository root:

```bash
brew install --cask sage
bash ui/launch.sh
```

If Sage is already installed, skip the Homebrew command. The launcher discovers a working installation and prints its executable, version, and local URL. It does not install software itself. Homebrew may require the usual macOS installer approval.

You can still choose an installation explicitly:

```bash
SAGE=/absolute/path/to/sage bash ui/launch.sh
```

Open **http://127.0.0.1:8124** and keep the terminal running. Stop with **Ctrl+C**.

### How Sage is selected

`launch.sh` searches in this order:

1. Explicit `SAGE` override (an executable path or command name). If invalid, it stops with an error rather than silently using another installation.
2. `SAGE_ROOT`, then active `CONDA_PREFIX` and `VIRTUAL_ENV` directories.
3. `sage` executables on PATH.
4. Common global binary locations: `/opt/homebrew/bin`, `/usr/local/bin`, `/usr/bin`.
5. SageMath application bundles in `/Applications` and `~/Applications`, including the current Homebrew macOS bundle layout.
6. Common user environment roots: `$MAMBA_ROOT_PREFIX` (or `~/micromamba`), `~/miniforge3`, `~/miniconda3`, and `~/anaconda3`, including their `envs/*/bin/sage` executables.

Each candidate must successfully run `-python -c 'import sage.all'`. Broken automatically discovered candidates are skipped. There is no machine-specific fallback or recursive disk scan. The first working candidate wins, not necessarily the newest version; use `SAGE` to select among multiple installations. If nothing works, the launcher prints installation instructions.

The selected executable determines the Sage version and dependencies. To inspect an installation:

```bash
/path/to/sage --version
/path/to/sage -python -c 'import sage.all; print("Sage imports successfully")'
```

For the remaining commands, change into `ui/` from the repository root:

```bash
cd ui
```

For a micromamba/conda installation, point `SAGE` at the environment's `bin/sage`. After activating that environment, `SAGE="$(command -v sage)" bash launch.sh` is also suitable.

To avoid specifying it each launch, export it in your terminal session:

```bash
export SAGE=/absolute/path/to/sage
bash launch.sh
```

### Port and runtime files

Use a different port if needed:

```bash
SAGE=/absolute/path/to/sage PORT=8126 bash launch.sh
```

Then open http://127.0.0.1:8126. The server binds to **127.0.0.1 only**; this is a local application, not a public deployment.

The launcher resolves the UI root from its own location, sets the working directory there, and places new Sage/Matplotlib/cache files in `.runtime/` inside `ui/`. That directory is ignored by Git. It disables Python bytecode generation and runs `sage -python code/web/server.py`.

## Updating core functions

Save your core changes, stop the server with Ctrl+C, run the launcher again, then refresh the browser. Sources are loaded at startup; there is no automatic hot reload. The UI does not edit core files.

The UI expects the current core function names and return shapes. Changing those APIs may require updating the UI adapter. Core errors are reported rather than silently replaced with alternate mathematics.

## Using the UI

Choose a mode from the menu:

### Mandelbrot explorer

- Left: curves generated only by the core's `addMandelBrotSoFar(Graphics())`, including whatever plotting helpers it currently calls. Sage colors, line styles, markers, sizes, thickness, and opacity are preserved. This is not a full Mandelbrot-set rendering.
- Click to select multiple parameters `c`; matching-colored paths of zero appear on the right using the core's `get_path` and `quadratic`.
- On either plot, two-finger trackpad scrolling pans horizontally and vertically; pinch or Ctrl+scroll zooms around the pointer. Each **Reset view** restores its own original bounds without clearing selections or changing the other plot.
- Click a selected marker or its Remove button to remove it. Clear all removes all selections.
- **Exact parameter c → Plot c** adds a parameter using Sage arithmetic, just like clicking the parameter plane. Examples: `sqrt(2) * I / pi`, `3*I + 4`, `-1/2`, or `e^(I*pi)`.
- **Maximum path steps** is applied to existing selections by **Update paths**.
- In **Vector field** mode, **Exact starting point z → Plot z** adds an orbit at that starting point using the currently applied `c`.
- Inputs accept arithmetic, parentheses, `^`/`**`, `I`/`i`, `pi`, `e`, `golden_ratio`, and `sqrt`, `sin`, `cos`, `tan`, `exp`, `log`, `abs`. They are evaluated by Sage, then converted to the same numerical complex coordinates used by clicked points. They are not arbitrary Sage/Python code. Invalid input leaves existing selections intact; off-view points are retained, but entering a point does not automatically change the current view bounds.
- Core stopping rules may end paths early. The UI does not infer periods or append synthetic iterates.
- The right display starts at −2…2 bounds; pan and zoom to inspect other regions. Off-view geometry is clipped for display.

### Vector field

- Enter `c` as one Sage expression, such as `1/3 + sqrt(2)*I`, `-3/4`, or `I/4`; set view bounds, spacing, convergence threshold, and iteration counts, then select **Rebuild**. The expression is evaluated with Sage and converted to numerical coordinates for plotting and orbits; this is not exact symbolic orbit propagation. Invalid expressions leave the applied view unchanged.
- **Iterations** controls each grid point's classification calculation. **Orbit steps** controls click-selected paths drawn over the grid. Both are maximum counts; core stopping rules still apply.
- Click the plane to add a path; click near its starting marker again to remove it.
- Two-finger trackpad scrolling pans; pinch or Ctrl+scroll zooms. These only redraw cached samples and paths, without resampling or changing the applied calculation bounds. **Reset view** returns to the applied build bounds. Accepted rebuilds reset the viewport; resizing or switching modes preserves it.
- Rebuild sends fixed points first, then batches of arrows, then batches of classifications. Each batch is flushed immediately so the plot fills progressively.
- Colors/categories come from the core classifier; an unresolved result is not a proof of escape or absence of an attracting cycle.

**There is no grid point-count limit.** The 128-point processing batch size controls update frequency, not the total grid size. Very small spacing can consume substantial memory/CPU or make the process unresponsive. The grid's points are currently materialized before streaming begins, and Sage requests are processed serially, so a rebuild can delay other clicks. Use Ctrl+C to stop an expensive run; if necessary stop it from another terminal. No background service or automatic restart is installed.

## Troubleshooting

- **Sage executable not found:** install Sage (on macOS, `brew install --cask sage`) and rerun. For a nonstandard location, set `SAGE` explicitly.
- **Missing core file:** check that `../core_code/` exists in this combined checkout.
- **Address already in use:** stop the existing server or choose another `PORT`.
- **Core traceback / partial plot:** inspect the named core function. A plotting or classification error may leave earlier successfully rendered layers visible. Restart after fixing saved core code.
- **Old behavior after edits:** restart the server and refresh the page.
- **Verify server availability:** visit `/api/health`, e.g. http://127.0.0.1:8124/api/health. It reports the live core path.

## Tests

From `ui/`, using the same Sage installation as the server:

```bash
mkdir -p .runtime/{sage,matplotlib,cache}
export DOT_SAGE="$PWD/.runtime/sage"
export MPLCONFIGDIR="$PWD/.runtime/matplotlib"
export XDG_CACHE_HOME="$PWD/.runtime/cache"
export PYTHONDONTWRITEBYTECODE=1
/path/to/sage -python tests/test_api.py
/path/to/sage -python tests/test_streaming.py
node --test tests/*.test.mjs
python3 tests/test_sage_discovery.py
python3 tests/test_layout.py
bash -n launch.sh scripts/find_sage.sh
```

The API tests require the real core in this checkout, not mock math. Streaming tests check both real-core batching and delivery before the full computation finishes. These tests were run locally; they are not a claim of cross-platform validation or GitHub CI coverage.

Optional browser acceptance uses `tests/browser_acceptance.py`, Playwright, and a running server. That script currently hard-codes the macOS Google Chrome executable; adjust it for other platforms. Historical screenshots were omitted from this import. Older migration notes are archived evidence, not current runtime state or setup instructions.

## Design and ownership

See `../README.md` for import provenance and `docs/design/` for archived design history and `AGENTS.md` for assistant write boundaries. Sam owns all mathematical and Sage plotting functions; missing capabilities require a core implementation or an agreed plan, not duplicate mathematics in this repository.
