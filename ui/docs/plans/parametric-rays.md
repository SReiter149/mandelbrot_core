# Parametric curves and external rays implementation plan

**Goal:** Add a minimal External rays mode with paired source and psi-image plots using Sam's core helpers, without changing mathematics.

**Architecture:** Extend existing Sage HTTP transport and browser presentation. Read live core helpers, serialize their Graphics primitives, and reuse existing canvas/style/viewport infrastructure. Coefficient selection is a page-session snapshot: numeric maximum filename suffix, actual loaded list length for display; no polling or rescan when adding curves.

**Tech stack:** Existing Sage Python stdlib HTTP server, JS/canvas, unittest/Node/browser tests.

## Authorized scope and boundaries
- Base: Sam's pushed `feat/parametric-rays` at bbfa20b. Implementation branch: `agent/parametric-rays-ui`.
- Work locally only. No commits, pushes, PRs, merges, deployments, service restarts, or changes to other repositories.
- `core_code/`, root `tests/`, `.github/CODEOWNERS` are read-only. Changes only under `ui/`.
- Sam will add colors tomorrow. Preserve core styles; no color controls or invented palette, no matching-color adapter for now.
- Reuse `plot_parametric`, `plot_external_rays`, `load_psi`. Do not write alternative sampling, psi evaluation, or mathematical plotting algorithms.
- Do not impose new work/sample-count caps. Validate finite numeric ranges, positive step size, increasing range, and safe expression syntax. Explain expensive requests honestly.

## Acceptance criteria
1. A new mode has source curve on the left, its image under psi on the right. Multiple curves can be added/removed/cleared with expression, parameter variable/range, and step-size controls, following current UI conventions.
2. Input is allowlisted mathematical arithmetic, not arbitrary Python/Sage code; support a symbolic parameter and current constants/functions. Extend existing parser rather than duplicating unsafe eval.
3. On page load/full refresh, choose `psi_coefficients_<n>.sobj` with maximum numeric n, not mtime/lexicographic order. Load only the winner. Keep the same selected coefficients for all curves in that page session, even if new files appear; another page session may select a newer save.
4. Label actual list length: `Using <count> coefficients`, not an n counter. Handle missing saves/corrupt chosen save without breaking existing modes or generating coefficients automatically.
5. Local development saves currently live at `/Users/sam/Documents/academic/carleton/math/comps/code/saves/` (outside repo), while core test fixtures also exist. Do not silently use root tests' fixtures as production saves. Inspect existing configuration first; if needed provide a documented environment setting for saves directory with a portable repo-root `saves/` default and set the explicit local path only in test/run commands. Never commit machine-specific paths or copy coefficient blobs into git.
6. Preserve core points as points, not invented connecting paths; use existing Graphics serialization conventions and styles. Pan/zoom/reset via existing presentation helpers.
7. Existing explorer and vector-field modes continue to pass tests.

## Task 1: Baseline and compatibility
- Read AGENTS.md, ui/AGENTS.md, ui/README.md and existing server/frontend modules/tests before implementing.
- Record clean baseline test output. Use `/Users/sam/micromamba/envs/math/bin/python` for Sage tests. Keep runtime under ignored ui/.runtime/.
- Smoke-test current core plotting functions read-only using real saved coefficients. Do not run root tests that write tracked outputs.

## Task 2: Coefficient page-session snapshot (TDD)
- Add focused ui/tests tests: numeric suffix ordering (including 9 vs 10), ignore unnumbered/nonmatching files, only load selected save, exact coefficient count, stable page-session selection on added curves, new session sees new file, missing/corrupt behavior.
- Observe intended failures, implement minimal server-side snapshot/configuration support, rerun tests.
- Avoid global coefficient changes that mix independent browsers' sessions. Use an explicit selection token/identity and verify it rather than trusting arbitrary client paths.

## Task 3: Expression and core adapter (TDD)
- Write failing tests for symbolic curve parsing, rejection of attributes/imports/unknown symbols, finite/increasing range and positive step validation, paired output and repeated curves.
- Extend existing allowlisted expression machinery and load external_rays.sage into shared CORE namespace.
- Call source and mapped core plotters with identical variable/range/step settings and selected psi. Serialize actual core primitives for each plane. Do not change core files.
- Check real Sage rendering and numeric outputs against the core helpers, not substitute math.

## Task 4: Browser mode (TDD)
- Add Node state tests for multiple curves, removal/clear, request revisions/stale replies, coefficient session stability, mode persistence.
- Reuse existing mode controls/canvas/viewport presentation. Add minimal form, two plots, coefficient-count label, visible loading/error state.
- Preserve earlier successful curves on invalid input. Preserve existing modes and core style semantics. No color feature work.

## Task 5: Verification and handoff
- Run Sage API/streaming and new integration tests, Node tests, launcher/layout tests as applicable; report preexisting failures separately.
- Start an isolated test server on an unused loopback port, not the live site. Verify health + real HTTP curve request and a browser smoke test for paired plots/add/remove/error behavior. Stop only the temporary server you started.
- Check `git diff --check`, review changes for unsafe eval/scope creep, and verify `git diff --exit-code bbfa20b -- core_code tests .github/CODEOWNERS`.
- Update ui/README.md with exact usage, saves configuration, page-refresh selection semantics and tests.
- Write ignored ui/.runtime/parametric-rays-handoff.md with implemented behavior, exact verification commands/results, remaining blockers, files changed, branch, and validation Sam must do. Do not claim success without execution evidence.
