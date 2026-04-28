# Release Checklist

Use this before every public release or X announcement.

## Safety

- [ ] Do not publish a real Hermes `state.db`.
- [ ] Do not publish generated outputs from real history without manual review.
- [ ] Confirm `.gitignore` blocks private DBs, generated reports, manifests, memory reviews, and `.env` files.
- [ ] Run a secret scan on tracked files before release.
- [ ] Confirm examples use only `examples/demo_state.db` synthetic data.

## Required Commands

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest
./scripts/ci.sh
core-hermes-extract --db examples/demo_state.db --dry-run --strict
```

## GitHub Actions

- [ ] GitHub Actions CI template is present at `.github-disabled/workflows/ci.yml`.
- [ ] Move it to `.github/workflows/ci.yml` using a GitHub token with `workflow` scope before claiming CI is active.
- [ ] CI passes on supported Python versions.
- [ ] If workflow upload fails, use a GitHub token with `workflow` scope.

## Messaging

- [ ] Call the release a Technical Preview.
- [ ] Say it is for developers and Hermes Agent power users.
- [ ] Tell users to start with `dry-run`.
- [ ] Warn: Do not publish `state.db` or generated outputs without review.
- [ ] Avoid claiming it is safe for everyone or fully automatic.

## Version

- [ ] Release tag uses `v0.1.0-preview` style.
- [ ] README status matches the tag.
- [ ] Release notes include privacy warning and dry-run command.
