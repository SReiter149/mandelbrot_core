#!/bin/bash
# Sourced by launch.sh. Discovery only; no installation or math implementation.
SAGE_SYSTEM_DIRS=(/opt/homebrew/bin /usr/local/bin /usr/bin)
SAGE_APP_DIRS=(/Applications "$HOME/Applications")

sage_works() {
  [[ -f "$1" && -x "$1" ]] && "$1" -python -c 'import sage.all' >/dev/null 2>&1
}

try_sage() {
  local candidate="$1"
  if sage_works "$candidate"; then
    printf '%s\n' "$candidate"
    return 0
  fi
  return 1
}

discover_sage() {
  local candidate directory app prefix
  # Explicit overrides must not silently launch an unintended installation.
  if [[ -n "${SAGE:-}" ]]; then
    candidate="$SAGE"
    if [[ "$candidate" != */* ]]; then
      candidate="$(command -v "$candidate" || true)"
    fi
    if try_sage "$candidate"; then return 0; fi
    printf 'SAGE=%s is not a working Sage executable (import sage.all failed).\n' "$SAGE" >&2
    return 1
  fi
  for prefix in "${SAGE_ROOT:-}" "${CONDA_PREFIX:-}" "${VIRTUAL_ENV:-}"; do
    [[ -n "$prefix" ]] || continue
    for candidate in "$prefix/sage" "$prefix/bin/sage" "$prefix/local/bin/sage"; do
      if try_sage "$candidate"; then return 0; fi
    done
  done
  # type -a enumerates PATH executables; no recursive home/disk search.
  while IFS= read -r candidate; do
    if try_sage "$candidate"; then return 0; fi
  done < <(type -a -p sage 2>/dev/null || true)
  for directory in "${SAGE_SYSTEM_DIRS[@]}"; do
    if try_sage "$directory/sage"; then return 0; fi
  done
  for directory in "${SAGE_APP_DIRS[@]}"; do
    for app in "$directory"/SageMath*.app "$directory"/sage*.app; do
      [[ -d "$app" ]] || continue
      for candidate in \
        "$app/Contents/Frameworks/Sage.framework/Versions/Current/venv/bin/sage" \
        "$app/Contents/Resources/sage/sage" \
        "$app/Contents/Resources/sage/local/bin/sage"; do
        if try_sage "$candidate"; then return 0; fi
      done
    done
  done
  # Last resort: common user-managed environment roots, without recursive scanning.
  for directory in "${MAMBA_ROOT_PREFIX:-$HOME/micromamba}" "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3"; do
    for candidate in "$directory/bin/sage" "$directory"/envs/*/bin/sage; do
      if try_sage "$candidate"; then return 0; fi
    done
  done
  printf '%s\n' 'Could not find a working SageMath installation.' \
    'On macOS: brew install --cask sage' \
    'Then rerun this launcher. Or set SAGE=/absolute/path/to/sage.' >&2
  return 1
}
