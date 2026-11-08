# Mandelbrot: mathematics and browser UI

One checkout contains Sam's **human-written mathematics and Sage plotting functions** in `core_code/`, existing core tests in `tests/`, and the **AI-written UI and HTTP adapter** in `ui/`. The UI loads the core directly and does not maintain alternate mathematics. Agents must treat core code and existing core tests as read-only; see [AGENTS.md](AGENTS.md).

## Local setup

Install SageMath (including the core's dependencies), Bash, and a modern browser. Ordinary Python cannot run the server. The consolidated API and streaming tests pass locally with SageMath 10.9; the source UI also documented testing with 10.7. Other platforms/versions are not verified. Node.js is optional for frontend tests. No npm build or separate core checkout is required.

```bash
git clone https://github.com/SReiter149/mandelbrot_core.git
cd mandelbrot_core
bash ui/launch.sh
# Or choose a Sage executable explicitly:
# SAGE=/absolute/path/to/sage bash ui/launch.sh
```

Open **http://127.0.0.1:8124**; stop with **Ctrl+C**. Use `PORT=8126` for another port. The server is loopback-only; this baseline does not install hosting or background services. Restart after saved core changes. Core incompatibilities must be reported, not patched by UI agents.

See [ui/README.md](ui/README.md) for controls, discovery, troubleshooting, and tests. Runtime/cache files stay in `ui/.runtime/` and are ignored. When running tests directly, set cache environment variables as documented there.

## Import provenance

The baseline UI was imported using `git archive HEAD` from `SReiter149/mandalbrot_UI`, commit **`3deaccd4611c0d245b7a507e7e7c33531b3446b4`**, not from its dirty working tree. Minimal combined-checkout path and documentation adaptations follow the import. Original nested agent instructions were replaced with current boundaries. Historical test screenshots (`browser-mandelbrot.png`, `browser-vector.png`) and the obsolete external-core hash inventory (`core-source-baseline.json`) were omitted. `ui/docs/` is archived design history, not current setup guidance. Existing core files, core tests, and `.github/CODEOWNERS` are preserved unchanged.
