# Agent boundaries

- Work only within this checkout and the task's authorized scope. Do not change original checkouts or running services.
- `core_code/` and all existing root `tests/` files are **read-only for agents**, including fixtures and tracked metadata. Preserve their paths and bytes. Sam owns the human-written mathematics and Sage plotting functions.
- Agents may work on the AI-written UI, presentation, transport/serialization adapters, launcher, UI tests, and supporting documentation under `ui/`. Never implement substitute mathematics or plotting functions; report missing or incompatible core APIs to Sam or other human contributors.
- Portable service tooling and its tests under `deployment/`, dependency specifications, and root setup documentation are also agent-editable within the requested scope. Generated machine-specific files and credentials stay outside Git.
- Keep `.github/CODEOWNERS` unchanged. Never add credentials, local environment files, runtime caches, or machine-specific service state.
- Use agent feature branches and pull requests for review. Never work directly on or push `main`; never merge a PR. Commit/push only when explicitly authorized by the coordinating user/agent.
- See `ui/AGENTS.md` for UI-specific boundaries. Archived design notes are historical, not current setup instructions.
