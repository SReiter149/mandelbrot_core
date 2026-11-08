> **Archived design history:** Preserved from the pre-consolidation UI. Paths, implementation plans, and core-error reports below describe that historical checkout, not current setup or current core behavior. For current instructions see [the UI README](../../README.md).

# Orbit and vector viewport zoom

## Approved design
Sam approved pointer-centered scroll/trackpad zoom on the orbit and vector plots, independent Reset view buttons, and display-only redraws. Existing selections, paths, samples and live Sage functions remain unchanged. No automatic resampling or rebuild. Reuse zoomBoundsAt and existing wheel normalization. Orbit reset restores -2…2; vector reset restores the applied build bounds. Accepted rebuilds reset the vector viewport to their bounds; invalid rebuilds retain the viewport. Resize and mode switching retain zoom. Click selection uses the visible viewport transform.

## Approved gesture update
Sam subsequently approved two-finger trackpad dragging (ordinary two-axis wheel events) to pan all three plots, with pinch/Ctrl+wheel for zoom. A shared wheelBoundsAt adapter normalizes deltas, reuses zoomBoundsAt for pinch, and translates viewport bounds for ordinary scroll. Existing reset, cached redraw, selection and calculation boundaries are unchanged. Verified with tests/viewport_pan.test.mjs and tests/browser_plot_pan.py plus both prior zoom browser regressions. Physical trackpad feel remains Sam's validation.

## Implementation plan
1. Add tests/browser_all_plot_zoom.py using real browser Canvas instrumentation and real backend requests. Verify rendered orbit magnification and reset, independent left view, vector pointer anchoring and changed click scale, no calculation requests on wheel/reset, preservation on resize/mode switch, accepted rebuild reset. Run before implementation and confirm missing behavior fails.
2. In code/web/static/explorer.mjs, generalize existing wheel/reset wiring to both canvases with independent mutable bounds. Keep curve styles and paths intact.
3. In code/web/static/app.js, import zoomBoundsAt, retain separate viewBounds from appliedConfig.bounds, use viewBounds on resize and update only the transform on wheel/reset. Reset viewBounds only on accepted rebuild. Redraw all layers from retained samples.
4. In code/web/static/index.html add reset-orbit-view and reset-vector-view buttons and accurate help text.
5. Run new browser regression, existing browser_parameter_interactions.py and browser_acceptance.py, node --test tests/*.test.mjs, git diff --check. Inspect browser screenshots. No core edits, commits, process termination or server restart.
