> **Archived design history:** Preserved from the pre-consolidation UI. Paths, implementation plans, and core-error reports below describe that historical checkout, not current setup or current core behavior. For current instructions see [the UI README](../../README.md).

# Migration verification — 2026-10-26

## Agent-run results
- New `launch.sh` started the local server at http://127.0.0.1:8124.
- `/api/health` returned status ok, engine sage, live sibling `mandalbrot_core/core_code` path.
- Six real Sage/HTTP integration tests passed (`sage -python tests/test_api.py`). They check live source provenance, serialized Graphics curves, exact agreement with live get_path outputs, frontend entrypoint, input/origin safety, vector output and explicit core-error reporting.
- Existing frontend-state tests passed; two new explorer-state tests passed.
- JavaScript syntax checks passed.
- Actual headless Chrome acceptance passed: page loaded, two c selections produced matching paths, mode switch worked, selections survived switching, clear worked, no browser JavaScript errors.
- Browser screenshot inspected: both planes and two source curves visible, selections and paths match colors.
- Hash comparison showed all six live core `.sage` source files unchanged.
- Design-only commit pushed and verified against origin/main. UI implementation is intentionally not pushed by this design-files authorization.

## Remaining core blocker (not repaired by UI)
`../mandalbrot_core/core_code/math_functions.sage`, `classify_paths`, line 96 uses `distnaces` rather than `distances`. The vector layer renders, but classification reports this NameError. No substitute classification is implemented.

## Operational caveats
- Source changes require server restart.
- Main-thread Sage calls are serialized; large grid rebuilds briefly block other requests. Grid maximum is 2,500 points.
- Left curves are the user's known-region boundaries, not a computed full Mandelbrot set.
- Right view is fixed to −2…2; off-view geometry is clipped only for display.
- Paths preserve the user's stopping behavior, including stopping before a repeated iterate. The UI does not infer period or append synthetic iterates.

## Sam's validation
Try selections in the cardioid and period-two disk. Confirm matching colors and path presentation are helpful for comparing the dynamics. Visual correctness and API tests do not establish a proof about attracting regions.
