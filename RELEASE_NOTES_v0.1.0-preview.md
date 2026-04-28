# v0.1.0-preview

Technical Preview for Hermes Agent users.

## What is included

- Hermes `state.db` reader
- Auto `SKILL.md` candidate generation
- Secret/PII sanitizer
- Safety audit and risk scoring
- Heuristic judge and strict quality gate
- Memory review output
- Safe-auto mode with auto/review/reject routing
- Safe Markdown report and machine-readable manifest
- Synthetic demo database and demo outputs

## Safety notice

This is a privacy-sensitive developer preview. Do not upload real `state.db` files or publish generated outputs without manual review.

Recommended first command:

```bash
core-hermes-extract --db ~/.hermes/state.db --dry-run --strict
```

## Verification

Local CI:

```bash
./scripts/ci.sh
```

Current result: `41 passed`.
