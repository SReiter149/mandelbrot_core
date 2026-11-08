> **Archived design history:** Preserved from the pre-consolidation UI. Paths, implementation plans, and core-error reports below describe that historical checkout, not current setup or current core behavior. For current instructions see [the UI README](../../README.md).

# Live-core migration implementation plan

Scope approved in the conversation: preserve Vector field, add simple two-plane Mandelbrot explorer, load Sam's live math/plot helpers, write only UI repository files.

1. Validate sibling `mandalbrot_core/core_code` location at startup and accept an explicit override. Keep Sage loading in a dedicated namespace to avoid accidental helper overrides.
2. Migrate HTTP service and launcher without copying mathematical implementations. Translate existing frontend requests to current live helper signatures. Serialize only finite results; bound computational inputs.
3. Use Sam's existing Graphics primitives for the left boundary geometry. Use his existing quadratic/get_path helpers for each selected c's orbit of zero. Do not create a replacement mathematical sampler, iterator, classifier, or plotting helper.
4. Preserve Vector field controls and selection behavior; obtain underlying vectors from live core. If classification fails, report that core error while retaining already rendered layers. Do not repair or monkey-patch core.
5. Add mode menu and two-plane presentation with stable matching selection colors. Support removal and clear. Iteration limit remains finite. No animation or automatic period labels.
6. Test source provenance, API validation and errors, curves/orbits, frontend state and syntax. Test real Sage execution, not only generated Python syntax.
7. Launch at `127.0.0.1:8124`. Verify health and actual browser interactions when supported. Report the exact launch command, URL, and any core blockers.
8. Stage and push only design documentation as explicitly requested. Leave implementation uncommitted unless separately authorized. Verify the remote branch SHA after push.

## Acceptance checklist
- [x] Server starts from new repository without old Hermes project files.
- [x] Loads live core without copying or writing there.
- [x] Both modes selectable.
- [x] Left boundary curves come from Sam's function.
- [x] Multiple c selections correspond to matching-colored right paths.
- [x] Source errors appear honestly, not substituted math.
- [x] Real Sage and browser/API verification recorded.
- [x] Design documents available on GitHub.
