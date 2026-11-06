#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
export PYTHONDONTWRITEBYTECODE=1
# Keep runtime caches inside this repository, including discovery probes.
export DOT_SAGE="$ROOT/.runtime/sage"
export MPLCONFIGDIR="$ROOT/.runtime/matplotlib"
export XDG_CACHE_HOME="$ROOT/.runtime/cache"
mkdir -p "$DOT_SAGE" "$MPLCONFIGDIR" "$XDG_CACHE_HOME"
source "$ROOT/scripts/find_sage.sh"
SAGE_BIN="$(discover_sage)" || exit 1
printf 'Using SageMath: %s\n' "$SAGE_BIN"
"$SAGE_BIN" --version
if [[ "${EXPLORER_CHECK_ONLY:-0}" == "1" ]]; then exit 0; fi
CORE_DIR="$ROOT/../core_code"
for helper in math_functions.sage plotting_functions.sage mandelbrot.sage; do
  if [[ ! -f "$CORE_DIR/$helper" ]]; then
    printf 'Missing core helper: %s/%s\nKeep ui/ and core_code/ in the same combined checkout.\n' "$CORE_DIR" "$helper" >&2
    exit 1
  fi
done
printf 'Starting local UI: http://127.0.0.1:%s (Ctrl+C to stop)\n' "${PORT:-8124}"
exec "$SAGE_BIN" -python "$ROOT/code/web/server.py" --port "${PORT:-8124}" "$@"
