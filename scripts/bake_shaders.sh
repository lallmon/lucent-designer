#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
cd "$root"

GLSL_TARGETS="100 es,120,150,300 es,310 es,320 es,330"
# Extensions to bake (extend if new stages are added)
EXTS="vert frag geom comp tesc tese"

# Skip if no staged shader source changes (pre-commit trigger)
if ! git diff --name-only --cached -- components/shaders | grep -E '\.(vert|frag|geom|comp|tesc|tese)$' >/dev/null 2>&1; then
  echo "[bake_shaders] No staged shader source changes; skipping."
  exit 0
fi

bake() {
  local src="$1"
  local out="${src}.qsb"
  echo "[bake_shaders] Baking $src -> $out"
  pyside6-qsb "$src" -o "$out" --glsl "$GLSL_TARGETS"
}

shopt -s nullglob
for ext in $EXTS; do
  for src in components/shaders/*."$ext"; do
    [ -f "$src" ] || continue
    bake "$src"
  done
done
shopt -u nullglob

echo "[bake_shaders] Done."

