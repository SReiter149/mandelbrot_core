# Pullback and parameter minimap implementation plan

Approved by Sam in chat: negative Orbit steps invoke live get_pullback_paths(c, target, iterations=abs(steps)); positive steps preserve forward orbits. Iterations remains strictly positive. Remove the artificial 1000-step limits; retain integer validation. Zero Orbit steps displays the target only. No performance guards. Pullbacks render as unordered dots, with target marker independently anchored. Core remains read-only.

**Goal:** Wire existing math and parameter curves into the vector UI.
**Architecture:** Thin Sage transport returns point geometry and direction; browser reuses existing coordinate transforms and parameter rendering, and single-selection c uses existing rebuild pipeline.
**Tech stack:** Sage Python HTTP server, ES modules, canvas, unittest, node:test, Playwright.

## Task 1 — transport (TDD)
- tests/test_api.py: first add failing tests comparing negative steps directly to live get_pullback_paths sets, plus steps=0, steps=1001, negative and >1000 classification validation. Do not request huge inverse trees in tests.
- code/web/server.py: generalize existing integer validator with explicit bounds; no app-imposed iteration maximum; trajectory branches on sign, labels pullback geometry, preserves request identity; classification stays positive.
- Run Sage tests and node tests. Do not edit core or commit.

## Task 2 — browser (TDD)
- Add browser regression tests for signed Orbit steps, >1000 input, pullback dots without connecting lines, zero, minimap single selection and exact-c synchronization, clearing stale orbits on c changes, explorer multi-selection unchanged.
- code/web/static/app.js: allow signed integer Orbit steps and positive Iterations without 1000 cap; render pullbacks as dots, target independently; synchronize minimap on accepted rebuild.
- Reuse/extract setup and drawPath from explorer.mjs into a shared presentation module if necessary; preserve styles. Small bottom-right minimap inside vector plot; use existing /api/mandelbrot geometry, no mathematical formulas. Click replaces c and invokes existing rebuild with stale-request safeguards. Update HTML/CSS and brief README instructions. Leave unrelated screenshots untouched; new screenshots under .runtime.
- Run new test RED first, then implement, then GREEN and existing browser suites.

## Task 3 — verification
- Run Sage HTTP tests, streaming, node tests, browser acceptance/regressions.
- Inspect screenshot and diff; confirm core source hashes unchanged from start, no git commits/pushes.
- Existing local server may need restart; identify exact project-owned process before stopping. Serve verified app on 8124 if feasible.
