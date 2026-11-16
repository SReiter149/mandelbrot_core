# Mandelbrot Explorer

An interactive tool for exploring complex quadratic dynamics with SageMath. Explore parameter values, follow forward orbits and pullbacks, inspect vector fields, and visualize external rays through a browser interface.

**[Open the explorer at samreiter.com](https://samreiter.com)** — no local installation required to use the hosted version.

> **Human-written mathematics, AI-written interface:** The mathematics and Sage plotting functions in `core/` are written by Sam Reiter. The browser interface and supporting HTTP server in `ui/` are AI-written and kept separate from the mathematical core.

## Mathematical sources

The following sources informed the development of the mathematics used in this site:

- B. Bielefeld, Y. Fisher, and F. v. Haeseler. “Computing the Laurent Series of the Map $\Psi : \mathbb{C} - \overline{\mathbb{D}} \to \mathbb{C} - M$.” *Advances in Applied Mathematics* **14**, 25–38 (1993).
- Robert L. Devaney. *An Introduction to Chaotic Dynamical Systems*. 3rd ed., CRC Press, 2022. [DOI: 10.1201/9780429280801](https://doi.org/10.1201/9780429280801).
- Robert L. Devaney. “The Mandelbrot Set and The Farey Tree.” December 29, 1997.
- Adrien Douady and John H. Hubbard. *Exploring the Mandelbrot Set: The Orsay Notes* (1984?).
- Davide Legacci. “Parabolic Fixed Points: The Leau-Fatou Flower.” March 18, 2021.
- Roland K. W. Roeder. *Around the Boundary of Complex Dynamics*. Notes for the 2015 Thematic Program on Boundaries and Dynamics, Notre Dame University.

## What you can explore

- **Mandelbrot explorer:** select complex parameters and compare the resulting orbits of zero alongside curves drawn by the mathematical core.
- **Vector field:** inspect sampled dynamics for a chosen parameter, add forward orbits or pullback points, and pan and zoom through the results.
- **External rays:** plot parameterized curves and their images using the core's external-ray functions and saved coefficients.
- **Sage expressions:** enter values such as `-3/4`, `1/3 + sqrt(2)*I`, or `e^(I*pi)` rather than only decimal coordinates.

This is an exploratory project, not a complete Mandelbrot-set renderer or a proof-producing classification tool. Plots reflect the current core implementation; iteration limits and numerical tolerances affect the results. Fine grids and long computations can take time.

See the [interface guide](ui/README.md#using-the-ui) for controls, expression syntax, and mode-specific behavior.

## Run locally

### Requirements

- [Miniforge](https://github.com/conda-forge/miniforge) or another conda-compatible installation.
- A SageMath-enabled Python environment. The included environment specification targets SageMath 10.9 and Python 3.14.
- Bash and a modern browser. Node.js is optional, for frontend tests only.

### Installation

```bash
git clone https://github.com/SReiter149/mandelbrot_core.git
cd mandelbrot_core
conda env create -f environment.yml
conda activate mandelbrot
SAGE_PYTHON="$CONDA_PREFIX/bin/python" bash ui/launch.sh
```

Open **http://127.0.0.1:8124**. Keep the terminal running and press **Ctrl+C** to stop the server.

If SageMath is already installed, you can select it explicitly instead:

```bash
SAGE=/absolute/path/to/sage bash ui/launch.sh
```

The selected Sage executable must support `-python`. Ordinary Python without SageMath cannot run the server. No npm install, frontend build, or separate UI checkout is required.

To choose another port:

```bash
PORT=8126 SAGE_PYTHON="$CONDA_PREFIX/bin/python" bash ui/launch.sh
```

The local launcher binds to `127.0.0.1` and keeps caches in `ui/.runtime/`. Restart the server after changing core or server code, then refresh the browser.

### External-ray coefficients

External-ray mode requires trusted, precomputed `psi_coefficients_<digits>.sobj` files in the root `saves/` directory, or in a directory selected with `PSI_SAVES_DIR`. The server does not generate missing coefficients. Explorer and vector-field modes remain available without them.

Only load Sage `.sobj` files you trust: they are executable serialized objects. See the [coefficient-loading guide](ui/README.md#saved-coefficients-and-page-refresh) for configuration and refresh behavior.

## Repository structure

```text
core/       Human-written mathematics and Sage plotting functions
tests/           Core mathematics tests
ui/              Browser interface, HTTP server, launcher, and UI tests
deployment/      macOS service and Cloudflare Tunnel setup
environment.yml SageMath environment specification
```

The interface loads the core functions directly rather than maintaining a second implementation of the mathematics.

## Loading the core in Sage scripts

Load the shared entry point rather than repeating individual filenames:

```python
from pathlib import Path

root = Path(__file__).resolve().parent  # a script at the repository root
load(str(root / "load_core.sage"))
```

For scripts in the sibling `run_code/` directory, use
`root = Path(__file__).resolve().parent.parent` and
`load(str(root / "mandelbrot_core" / "load_core.sage"))`.
The loader handles dependency order for all seven core files and preserves the
caller's `root` and `__file__`, so later image/save paths keep their meaning.
It loads definitions; it does not run analyses or generate coefficients.

Python callers running inside Sage use `sage.repl.load.load(path, namespace)`;
see `tests/math/conftest.py` for a shared, isolated pytest fixture. Notebook
callers should set an explicit repository path before loading the entry point.

## Testing

See [UI tests](ui/README.md#tests) for Sage-backed API, streaming, and frontend test commands, and the [deployment guide](deployment/README.md) for service configuration checks. Sage-backed tests require the real core and a working SageMath environment; Node.js is needed for the JavaScript tests.

## Self-hosting

The [deployment guide](deployment/README.md) covers macOS login services, Cloudflare Tunnel configuration, and start/stop/restart commands. Hosting requires a running SageMath backend; GitHub Pages alone cannot run this application. Keep machine-specific settings and tunnel credentials outside the repository.

## Development

Mathematical functions and Sage plotting code live in `core/`; interface and transport changes belong in `ui/`. See [AGENTS.md](AGENTS.md) for AI-assistant contribution boundaries. Documents under `ui/docs/` are archived design history, not current setup instructions.
