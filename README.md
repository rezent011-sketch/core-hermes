# Core Hermes Auto Skill Extractor

**Technical Preview for Hermes Agent users.**

Core Hermes reads a Hermes Agent `~/.hermes/state.db` and generates reviewable `SKILL.md` candidates, memory candidates, reports, and safe-auto decisions.

## Critical Privacy Warning

This is a **developer technical preview**, not a consumer-safe one-click tool.

This tool analyzes local conversation history. A Hermes `state.db` may contain:

- API keys, tokens, credentials, command output
- Telegram IDs, emails, URLs, personal data
- private project details and customer data

**Never upload your real `state.db`. Never commit it to git. Never publish generated outputs from real history without manual review.**

The tool includes sanitization, safety audit, risk scoring, strict mode, and safe-auto quarantine, but no automated scanner is perfect. Treat all generated files as sensitive until reviewed. If you are unsure, run only the synthetic demo first.

Public sharing rule: share the repository and demo outputs only. Do not share private databases, reports, manifests, extracted skills, or memory review files created from real user history.

## Safe First Run

Use dry-run first. This writes nothing.

```bash
git clone https://github.com/rezent011-sketch/core-hermes.git
cd core-hermes
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest

core-hermes-extract --db ~/.hermes/state.db --dry-run --strict
```

## Recommended Review Workflow

```bash
core-hermes-extract \
  --db ~/.hermes/state.db \
  --output ./extracted_skills \
  --review \
  --memory-review \
  --memory-review-out ./memory_review.md \
  --judge \
  --strict \
  --report ./core-hermes-report.md \
  --manifest ./core-hermes-manifest.json
```

Review these before installing or sharing:

- `./extracted_skills/review/*.md`
- `./memory_review.md`
- `./core-hermes-report.md`
- `./core-hermes-manifest.json`

## Safe-Auto Mode

Safe-auto does **not** blindly install everything.

Rules:

- high score + risk `0` + safety audit pass → auto install
- medium score → `review/`
- risk detected / low score → `rejected/`

```bash
core-hermes-extract \
  --db ~/.hermes/state.db \
  --output ./extracted_skills \
  --safe-auto \
  --auto-threshold 0.93 \
  --review-threshold 0.75 \
  --judge \
  --strict \
  --report ./core-hermes-report.md \
  --manifest ./core-hermes-manifest.json
```

Start with `--dry-run` or review workflow before enabling safe-auto on real history.

## Features

- Hermes `state.db` reader
- Auto skill extraction
- `SKILL.md` generation
- Secret/PII sanitizer
- Quality scoring and duplicate merging
- Safety audit and risk scoring
- Heuristic judge layer compatible with future LLM judge
- Quality gate and strict exit codes
- Memory review file generation
- Safe-auto operation mode
- Manifest and Markdown report output

## CLI Options

Key options:

- `--dry-run` analyze only, write nothing
- `--review` write skills under `output/review`
- `--memory-review` generate memory candidates
- `--memory-review-out PATH` write checkbox review file
- `--judge` run judge-backed quality evaluation
- `--strict` fail with exit `2` on safety/quality failures
- `--report PATH` write safe Markdown report
- `--manifest PATH` write machine-readable safe manifest
- `--safe-auto` enable safe auto-install/quarantine workflow
- `--auto-threshold 0.93` threshold for automatic install
- `--install-from DIR` install reviewed skills manually

## Demo Without Private Data

A synthetic demo database is included under `examples/demo_state.db`.

```bash
core-hermes-extract \
  --db examples/demo_state.db \
  --output ./demo_output \
  --memory-review \
  --memory-review-out ./demo_memory_review.md \
  --judge \
  --strict \
  --report ./demo_report.md \
  --manifest ./demo_manifest.json
```

## Local CI / Test Command

GitHub Actions CI template is included under `.github-disabled/workflows/ci.yml` and runs tests on Python 3.10, 3.11, and 3.12. Move it to `.github/workflows/ci.yml` with a GitHub token that has `workflow` scope.

Run the same local checks before publishing:

```bash
./scripts/ci.sh
```

Expected currently:

```text
47 passed
local CI passed
```

If GitHub rejects workflow updates, use a GitHub token with `workflow` scope.

## Release Checklist

Before announcing a release, follow `RELEASE_CHECKLIST.md`.

## Current Status

`v0.1.0-preview`

Package metadata uses PEP 440-compatible `0.1.0`; the public release tag and status are `v0.1.0-preview`.

- Intended audience: developers and Hermes Agent power users
- Status: technical preview
- Safe default: review-first
- General-user claim: **not yet**

## Repository

https://github.com/rezent011-sketch/core-hermes

## License

MIT
