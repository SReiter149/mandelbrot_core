# UI boundaries

- This directory contains the AI-written UI and supporting HTTP transport, not the mathematics.
- The repository root is `..`; load its `core_code/` read-only using `ROOT.parent / 'core_code'`, where `ROOT` is `ui/`. No external sibling checkout or copied core implementation is a runtime dependency.
- Root `core_code/` and existing root `tests/` are read-only. Sam owns all mathematics and Sage plotting functions. If compatibility requires a math change, report the problem rather than editing core code or implementing a substitute.
- UI controls, browser presentation, transport/serialization adapters, launcher, and UI tests belong here. Preserve existing modes unless explicitly asked otherwise.
- Keep runtime/cache files under `ui/.runtime/`, ignored by Git. Never add credentials or machine-specific deployment state.
- Follow the root AGENTS.md feature-branch/PR rules: no direct main work, main pushes, or PR merges; commit/push only with authorization.
- Current setup is in README.md. Files under docs/ are archived design history, not current setup or evidence about the present core.
