#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
# Keep runtime caches inside this checkout, not in the mathematical sources.
export DOT_SAGE="$ROOT/.runtime/sage"
export MPLCONFIGDIR="$ROOT/.runtime/matplotlib"
export XDG_CACHE_HOME="$ROOT/.runtime/cache"
mkdir -p "$DOT_SAGE" "$MPLCONFIGDIR" "$XDG_CACHE_HOME"
if [[ -n "${SAGE_PYTHON:-}" ]]; then
  PYTHON_BIN="$SAGE_PYTHON"
  if [[ "$PYTHON_BIN" != */* ]]; then PYTHON_BIN="$(command -v "$PYTHON_BIN" || true)"; fi
  if [[ ! -x "$PYTHON_BIN" ]] || ! "$PYTHON_BIN" -c 'import sage.all' >/dev/null 2>&1; then
    printf 'SAGE_PYTHON=%s cannot import sage.all. Use the Python from your Sage environment.\n' "$SAGE_PYTHON" >&2
    exit 1
  fi
  printf 'Using Sage-enabled Python: %s\n' "$PYTHON_BIN"
  RUNNER=("$PYTHON_BIN")
else
  source "$ROOT/scripts/find_sage.sh"
  SAGE_BIN="$(discover_sage)" || exit 1
  printf 'Using SageMath: %s\n' "$SAGE_BIN"
  "$SAGE_BIN" --version
  RUNNER=("$SAGE_BIN" -python)
fi
if [[ "${EXPLORER_CHECK_ONLY:-0}" == "1" ]]; then exit 0; fi
CORE_DIR="$ROOT/../core_code"
for helper in math_functions.sage plotting_functions.sage mandelbrot.sage; do
  if [[ ! -f "$CORE_DIR/$helper" ]]; then
    printf 'Missing core helper: %s/%s\nRun ui/launch.sh from a complete combined checkout.\n' "$CORE_DIR" "$helper" >&2
    exit 1
  fi
done
printf 'Starting UI: http://127.0.0.1:%s (Ctrl+C to stop)\n' "${PORT:-8124}"
exec "${RUNNER[@]}" "$ROOT/code/web/server.py" --port "${PORT:-8124}" "$@"
