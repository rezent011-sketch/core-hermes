#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q
python run.py --help >/dev/null
