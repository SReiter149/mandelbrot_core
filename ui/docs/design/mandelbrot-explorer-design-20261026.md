> **Archived design history:** Preserved from the pre-consolidation UI. Paths, implementation plans, and core-error reports below describe that historical checkout, not current setup or current core behavior. For current instructions see [the UI README](../../README.md).

# Design: live-core quadratic-map UI

Mode: /office-hours Builder
Date: 2026-10-26
Repository: SReiter149/mandalbrot_UI
Status: User-approved scope; local Sage/API/browser verification completed (core classification blocker documented)

## Problem
Sam wants to feel how choosing a parameter changes the orbit of zero, while retaining the existing vector-field interface. This is a local learning/research companion, not a new mathematical implementation or fractal-art renderer.

## Approved premises
- Sam implements all mathematics and plotting functions.
- All assistant project writes are confined to this repository.
- The UI loads saved, live Sage helpers read-only; no copied mathematical backend.
- The existing Vector field mode remains available.
- New Mandelbrot explorer: two known boundary curves on the left, colored selected parameters, matching paths of zero on the right.
- No animation, automatic period detection, or full Mandelbrot rendering.

## Existing capabilities and dependencies
The live source has moved from `../code/core_code` to `../mandalbrot_core/core_code`. Resolve that sibling directory at startup. An environment override is deferred; the current checkout assumes these sibling repositories. Load `.sage` sources using Sage `load`, not Python imports. Core changes become visible after a server restart.

`addMandelBrotSoFar(Graphics())` supplies the two curves. `get_path(0, func, ...)` supplies the orbit, with `func` calling Sam's `quadratic`. Existing core supplies fixed points, vector sampling, and classification helpers. The UI must respect their actual signatures and return contracts, including early stopping before a repeated point. It must not invent further iterates or mathematical labels.

## Alternatives considered
### A. Live-core adapters and existing browser frontend (selected)
Small migration: retain browser controls and rendering, use thin validation/serialization around live core, add the parameter/orbit view. Lowest disruption; signature changes in core may require adapter updates. Errors remain visible.

### B. Server-rendered complete Sage plots
Use Sam's plotting functions for every view and selection. Fewer client drawing responsibilities, but each interaction needs a new rendered image and coordinate alignment becomes more cumbersome. Can be used selectively for the left boundary plot if simpler.

### C. Separate standalone viewer
Would duplicate navigation and server plumbing without helping Sam's stated goal. Rejected.

## Interaction
A menu selects Vector field or Mandelbrot explorer. Preserve the vector-field controls and behavior when supported by the current core. The new mode displays parameter and dynamical planes side by side on wide screens and stacked on narrow screens. Both use equal horizontal and vertical scaling.

Clicking the left plot selects a parameter and stable color. Each corresponding orbit starts at zero and has the same color on the right. Support removing a selection and clearing selections. A small iteration-limit control bounds requests; pressing Update paths recalculates all existing selections without changing their colors. No playback controls. The adapter only serializes Sam-generated geometry, including the points already sampled by his Graphics primitives; neither server nor browser reconstructs or samples the boundary formulas. Draw points/paths as browser presentation only, never recompute dynamics in JavaScript. Distinguish the source parameter from the starting point zero. Show failures without removing successful selections or silently labeling unresolved behavior as convergence.

## Ownership
- Core mathematics, classifications, Sage plot construction: Sam, outside this repository, read-only.
- Local HTTP service, input validation, source loading, serialization, stale-response rejection: UI repository.
- Canvas coordinate transforms, selection colors, labels and menus: UI repository.

No missing core function may be replaced by assistant-written mathematics or plotting algorithms. Report bugs and missing APIs with exact locations and ask Sam to implement or agree on a workaround. Temporary backend errors must not disable the other mode.

## Runtime and distribution
Run locally with SageMath in the `math` environment using Python's standard-library HTTP server; no extra web dependency installation is needed. Sage calls run serially on the main thread because Sage plotting initializes thread-sensitive native libraries. Grid work is capped at 2,500 samples; it can briefly block orbit clicks. This is an explicit migration trade-off versus the old separate-worker implementation. Bind to loopback only, default new port 8124. Source is distributed in the existing GitHub repository; this task authorizes pushing design documents, not automatic publication of implementation code. No public deployment or new CI publishing pipeline is needed for this local application.

Computational POST endpoints validate finite inputs, bounded iterations, loopback Host, JSON content type, and same-origin requests. Avoid unbounded background work. Clip only display geometry and report stopped/failed calculations honestly.

## Verification
- JavaScript syntax and existing frontend-state tests.
- Sage startup against the live source, not copied helpers.
- API tests for two curves, zero orbit, multiple selected parameters, invalid inputs and core errors.
- Preserve vector-field endpoints or surface explicit missing-core blockers.
- HTTP health and both mode assets on port 8124.
- Browser interaction when an available automation runtime supports it; otherwise explicitly distinguish API verification from Sam's visual validation.
- Verify GitHub remote design commit after push.

## Sam's validation
Choose parameters in the cardioid and period-two disk. Confirm that selection colors match their paths and that the view supports the comparisons Sam wants. This validates the learning experience, not a new mathematical theorem.

## Next steps
Wire live helpers, migrate server/launcher, add mode UI, run tests, launch on the verified local port, and record blockers without modifying core.
