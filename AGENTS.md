# Agent guide — Reolink Dog Alert

Instructions for **Codex**, **Cursor**, and other coding agents. Follow the PRD; do not expand scope without explicit user approval.

## Read first

1. **`docs/PRD.md`** — canonical product requirements (v2 MVP + Phase 2 Frigate appendix).
2. **`docs/BACKLOG.md`** — prioritized tasks and acceptance checklist (update status when you complete work).
3. **`docs/architecture.md`** — system diagram and module boundaries.

## Product goal (v2 MVP)

Local Mac service that:

1. Polls **HTTP(S) JPEG** snapshots (`SNAPSHOT_URL`) or **`MOCK_MODE`** synthetic frames.
2. Detects **motion inside a lawn ROI** (tier 1; optional HA gate tier 2; optional classifier tier 3 — not required for MVP sign-off).
3. Saves snapshots under `storage/snapshots/`, respects **cooldown** and **dedupe**.
4. Sends **iMessage** (text + image) via AppleScript unless `IMESSAGE_DRY_RUN=true`.

**Phase 2 (optional):** Frigate + RTSP (Reolink **E1 Pro** or Docker **mock-rtsp** profile). See README Phase 2 section.

## Hardware truth (do not regress)

| Camera | MVP v2 ingest | Phase 2 RTSP |
|--------|----------------|--------------|
| Reolink **E1** (standalone) | HTTP snapshot / HA proxy — **no LAN RTSP** | Home Hub/NVR only |
| Reolink **E1 Pro** | HTTP snapshot if available | **Standalone RTSP** on LAN |

Never assume standalone E1 exposes RTSP. User ordered **E1 Pro** for Phase 2.

## Repository layout

```text
scripts/lawn_alert.py       # v2 main loop (default entrypoint)
scripts/snapshot_ingest.py  # HTTP GET + retries; MOCK path
scripts/detect_motion.py      # ROI polygon frame-diff
scripts/send_imessage.py      # osascript wrapper
scripts/event_watcher.py      # Phase 2 Frigate poller
scripts/env_util.py           # loads .env then .env.local
config/roi.json               # lawn polygon (normalized 0–1)
config/frigate.yml            # Phase 2 only
config/mediamtx.yml           # MOCK RTSP test pattern
```

## Environment

- Copy **`.env.example` → `.env`**; never commit `.env` / `.env.local`.
- **`MOCK_MODE=true`**: synthetic JPEG ingest and/or mock Frigate HTTP API — logs use **`[MOCK]`**.
- **`IMESSAGE_DRY_RUN=true`**: skip real Messages sends during dev.
- Load order: **`.env`** then **`.env.local`** (override).

## Commands (run from repo root)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # if missing

# Validate without camera / iMessage
./scripts/validate_dev.sh

# v2 smoke tests
MOCK_MODE=true python scripts/test_snapshot_url.py
MOCK_MODE=true IMESSAGE_DRY_RUN=true python scripts/lawn_alert.py --once

# Phase 2 (Docker required)
docker compose --profile mock-rtsp up -d
python scripts/test_frigate_connection.py
MOCK_MODE=false IMESSAGE_DRY_RUN=true python scripts/event_watcher.py --once
```

## Coding rules

- **Python 3.11+**, stdlib + `requirements.txt` only unless PRD adds a dependency.
- **Local-first**: no cloud inference, Twilio, or SaaS for MVP.
- **Label mocks**: any synthetic API, RTSP, or frame path must log **`[MOCK]`** and stay off by default in production configs.
- **Small modules**: keep ingest, detection, alerting, and iMessage separated; extend existing functions before adding parallel implementations.
- **Secrets**: never commit passwords, `FRIGATE_PASSWORD`, or Frigate DB files under `config/`.
- **macOS-only** for iMessage; do not replace with Twilio.

## Definition of done (v2 MVP)

Per PRD acceptance criteria — all must pass:

- [ ] `test_snapshot_url.py` OK with real `SNAPSHOT_URL` or `MOCK_MODE=true`
- [ ] Tier-1 motion fires on controlled/mock frames; ROI documented in `docs/setup.md`
- [ ] Cooldown + dedupe verified in logs
- [ ] Alert JPEG saved under `SNAPSHOT_DIR`
- [ ] iMessage works with `IMESSAGE_DRY_RUN=false` (human verification)
- [ ] `lawn_alert.py` survives transient HTTP errors (no crash loop)

Stretch / Phase 2: dog-specific detection via Frigate or tier-3 classifier — not blocking v2 MVP.

## Workflow for Codex

1. Pick the **next open item** in `docs/BACKLOG.md` (highest priority `todo`).
2. Implement minimally; match existing style in neighboring scripts.
3. Run **`./scripts/validate_dev.sh`** and relevant smoke scripts.
4. Update **`docs/BACKLOG.md`** checkboxes and add a one-line note under **Changelog** if useful.
5. Update **`docs/setup.md`** / **`docs/troubleshooting.md`** when behavior or env vars change.
6. One logical change per commit; message explains **why**.

## Out of scope (unless user asks)

- SaaS dashboard, multi-user auth, Twilio, cloud ML training
- Guaranteed “dog pooping” detection
- Refactors unrelated to the current backlog item

## Questions to ask the user

- Exact **`SNAPSHOT_URL`** for E1 / HA when moving off pure mock
- **`IMESSAGE_TARGET`** and permission to send live test messages
- Whether Phase 2 should target **mock RTSP** or **E1 Pro** IP when hardware arrives
