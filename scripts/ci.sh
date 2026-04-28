#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -n "${VIRTUAL_ENV:-}" && -x "$VIRTUAL_ENV/bin/python" ]]; then
  PYTHON_BIN="$VIRTUAL_ENV/bin/python"
elif [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python)"
else
  echo "ERROR: python3 or python not found" >&2
  exit 127
fi

echo "Using Python: $PYTHON_BIN"
"$PYTHON_BIN" -m pytest -q
"$PYTHON_BIN" run.py --help >/dev/null

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
"$PYTHON_BIN" run.py \
  --db examples/demo_state.db \
  --output "$TMP_DIR/demo_output" \
  --memory-review \
  --memory-review-out "$TMP_DIR/demo_memory_review.md" \
  --judge \
  --strict \
  --report "$TMP_DIR/demo_report.md" \
  --manifest "$TMP_DIR/demo_manifest.json" >/dev/null

echo "local CI passed"
