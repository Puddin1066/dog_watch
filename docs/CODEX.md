# Using Codex on this repo

How to drive implementation from **`docs/PRD.md`** with OpenAI Codex (CLI or IDE) or similar agents.

## One-time setup

```bash
cd reolink-dog-alert
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env: IMESSAGE_TARGET, MOCK_MODE=true, IMESSAGE_DRY_RUN=true
```

Install [Codex CLI](https://github.com/openai/codex) if you use terminal-driven workflows. Point it at **this directory** (the git root).

## Files Codex should read every session

| File | Purpose |
|------|---------|
| `AGENTS.md` | Rules, commands, definition of done |
| `docs/PRD.md` | Full requirements |
| `docs/BACKLOG.md` | What to build next |
| `docs/architecture.md` | Module boundaries |

## Suggested prompts

### Bootstrap / orient

```text
Read AGENTS.md, docs/PRD.md, and docs/BACKLOG.md. Summarize v2 MVP vs Phase 2.
Pick the highest-priority todo backlog item and propose a minimal plan (files, tests, docs).
Do not implement until I confirm.
```

### Implement one backlog item

```text
Implement backlog item: "<paste title from docs/BACKLOG.md>".
Follow AGENTS.md coding rules. Run ./scripts/validate_dev.sh.
Update docs/BACKLOG.md status and docs/setup.md if env or behavior changed.
```

### Phase 2 — mock RTSP stack

```text
Verify Frigate + mock-rtsp integration per README Phase 2.
Use MOCK_MODE=false and IMESSAGE_DRY_RUN=true for event_watcher.
Document any failures in docs/troubleshooting.md.
```

### E1 Pro cutover (when hardware arrives)

```text
User has Reolink E1 Pro on LAN. Update .env Option B (RTSP port 554, h264Preview_01_main).
Document RTSP enable steps in docs/setup.md. Do not assume standalone E1 RTSP.
```

## Validation gate (run before every PR / commit)

```bash
./scripts/validate_dev.sh
```

Optional manual checks:

```bash
MOCK_MODE=true python scripts/lawn_alert.py --once
docker compose --profile mock-rtsp up -d
python scripts/test_frigate_connection.py
```

## Multi-agent split (PRD § Multi-Agent)

If running parallel Codex/Cursor agents, assign **non-overlapping** files:

| Agent | Owns |
|-------|------|
| Infrastructure | `docker-compose.yml`, `.env.example`, `README`, `scripts/validate_dev.sh` |
| Ingest + vision | `snapshot_ingest.py`, `detect_motion.py`, `mock_frame_generator.py`, tests |
| Alert core | `lawn_alert.py`, `config/roi.json`, logging |
| iMessage | `send_imessage.*`, `test_imessage.py` |
| Phase 2 | `frigate.yml`, `mediamtx.yml`, `event_watcher.py`, Frigate tests |
| QA | `docs/BACKLOG.md`, `validate_dev.sh`, acceptance runs |

Merge via git; resolve conflicts in `lawn_alert.py` last (integration point).

## Keeping PRD in sync

Canonical PRD may also live at:

`../reolink_e_1_frigate_imessage_dog_alert_prd.md`

After editing that file, refresh the copy in-repo:

```bash
cp ../reolink_e_1_frigate_imessage_dog_alert_prd.md docs/PRD.md
```

## What not to ask Codex for

- Committing `.env` or Frigate SQLite under `config/`
- Cloud APIs, Twilio, or training custom models (out of PRD MVP)
- “Make E1 work with RTSP” without Home Hub/NVR — hardware limitation
