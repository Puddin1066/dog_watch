# Contributing

Thanks for your interest in improving this project.

## Quick start

1. Fork and clone the repository.
2. Create a virtual environment and install dependencies:
   - `python3 -m venv .venv && source .venv/bin/activate`
   - `pip install -r requirements.txt`
3. Copy env template:
   - `cp .env.example .env`
4. Keep safe defaults while developing:
   - `MOCK_MODE=true`
   - `IMESSAGE_DRY_RUN=true`

## Development rules

- Follow `AGENTS.md` and `docs/PRD.md` for scope and constraints.
- Clearly label mocked API/data flows with `[MOCK]` in logs or user-visible messages.
- Keep modules focused (ingest, detection, alerting, messaging) and avoid duplicated logic.
- Do not commit secrets, `.env`, Frigate DB files, or runtime artifacts.

## Before opening a pull request

1. Run:
   - `./scripts/validate_dev.sh`
2. Update docs when behavior or env vars change:
   - `README.md`
   - `docs/setup.md`
   - `docs/troubleshooting.md`
   - `docs/BACKLOG.md` (if a backlog item status changed)
3. Keep PRs small and focused on one logical change.

## Pull request checklist

- [ ] I ran `./scripts/validate_dev.sh`.
- [ ] I used mock mode and dry-run mode where appropriate.
- [ ] I documented any new env vars or behavior changes.
- [ ] I did not include secrets or generated runtime files.
