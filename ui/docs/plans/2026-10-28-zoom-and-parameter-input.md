> **Archived design history:** Preserved from the pre-consolidation UI. Paths, implementation plans, and core-error reports below describe that historical checkout, not current setup or current core behavior. For current instructions see [the UI README](../../README.md).

# Pointer zoom and parameter-expression implementation plan

**Goal:** Implement Sam's approved pointer-centered zoom and single Sage-expression Parameter c field.
**Architecture:** UI-only changes. Reuse world/canvas transforms and the existing `/api/point` Sage evaluator; no core writes or new mathematics. Keep the applied vector configuration until evaluation and rebuild validation succeed.
**Tech stack:** Browser Canvas, ES modules, existing Sage HTTP API, Node tests, Playwright.

## Approved design
- Wheel/trackpad zoom on the left parameter canvas stays centered under the pointer; clicks still select/remove c. Preserve selections, colors, orbit paths, and the right viewport. Reset view restores [-2, 1] × [-1.5, 1.5]. Prevent wheel scrolling only over this canvas. Reject nonfinite or precision-collapsed bounds rather than corrupting the view.
- Replace vector Parameter c real/imaginary numeric controls with one expression field defaulting to `I/4`. Rebuild uses the existing restricted Sage arithmetic endpoint. Expressions stay visible; plotted values and orbits remain numerical. Invalid input preserves the applied plot. Newer submissions supersede older expression responses.
- No panning, new dynamics algorithms, backend formula changes, commits, or pushes.

## Steps
1. Add `tests/parameter_interactions.test.mjs` for pointer anchoring, zoom limits, inverse zoom, shared expression transport. Add `tests/browser_parameter_interactions.py` for actual canvas clicks before/after zoom/reset and vector c expression acceptance/rejection. Run to prove missing behavior.
2. Generalize expression request transport in `code/web/static/point_entry.mjs`; reuse it in `app.js`. Snapshot form inputs before awaiting expression evaluation and guard submission revisions.
3. Add a pure viewport zoom helper beside existing coordinate transforms in `state.mjs`; wire wheel and reset handlers in `explorer.mjs`. Change only parameter bounds; render existing curve geometry unchanged.
4. Update `index.html` with the expression input, help, and Reset view. Document interactions in README.
5. Run `node --test tests/*.test.mjs`, real Sage API tests with discovered Sage, both Playwright suites against the live loopback server, JS syntax checks, and `git diff --check`. Inspect the browser screenshot. Do not restart a user-managed service or claim symbolic orbit propagation.
