# Reolink Dog Alert

Local-first lawn alerts: **PRD v2** (HTTP snapshots + ROI motion) and **Phase 2** (Frigate + RTSP, e.g. **Reolink E1 Pro** or a **mock RTSP** dev stream).

**PRD:** [`docs/PRD.md`](docs/PRD.md) (copy of parent [`../reolink_e_1_frigate_imessage_dog_alert_prd.md`](../reolink_e_1_frigate_imessage_dog_alert_prd.md))

**AI / Codex:** read [`AGENTS.md`](AGENTS.md) → [`docs/BACKLOG.md`](docs/BACKLOG.md) → [`docs/CODEX.md`](docs/CODEX.md). Validate with `./scripts/validate_dev.sh`.

---

## v2 MVP — snapshot + motion (default)

1. `cd reolink-dog-alert && python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `cp .env.example .env` — set **`SNAPSHOT_URL`** (or keep **`MOCK_MODE=true`** for synthetic JPEGs).
4. Edit **`config/roi.json`** (lawn region, normalized coordinates).
5. `python scripts/test_snapshot_url.py` then `python scripts/lawn_alert.py --once` or continuous `python scripts/lawn_alert.py`.

Optional overrides: **`.env.local`** (gitignored), loaded after `.env`.

---

## Phase 2 — Frigate + RTSP (E1 Pro or mock)

### A) Mock RTSP (synthetic pattern — **not** a real camera)

Use this until the **E1 Pro** is on the LAN. **MediaMTX** publishes `rtsp://mock_rtsp:8554/e1pro-mock` on the Compose network; Frigate ingests it like a normal camera.

1. In `.env`, set the **Option A** block from `.env.example` (`CAMERA_IP=mock_rtsp`, `CAMERA_RTSP_PORT=8554`, `CAMERA_RTSP_PATH=e1pro-mock`, credentials as shown).
2. `docker compose --profile mock-rtsp up -d` (or `docker-compose --profile mock-rtsp up -d`).
3. Open **`https://localhost:8971`**, complete Frigate first-login, then set **`FRIGATE_USERNAME`** / **`FRIGATE_PASSWORD`** in `.env`.
4. `python scripts/test_frigate_connection.py` — confirms API + optional snapshot.
5. `MOCK_MODE=false` → `python scripts/event_watcher.py` (polls **live** Frigate; dog events only if the stream actually contains a detected dog in **`front_lawn`**).

**Two different “mocks”:**

| Flag / component | What it mocks |
|-------------------|----------------|
| **Docker `mock_rtsp` profile** | **RTSP video** into Frigate (test pattern). |
| **`MOCK_MODE=true` in `.env`** | **Frigate HTTP API** inside `event_watcher.py` (no Frigate process). |

### B) Real Reolink E1 Pro

1. Enable RTSP in the Reolink app; use **`CAMERA_IP`**, port **`554`**, path typically **`h264Preview_01_main`**, and **`CAMERA_RTSP_PASSWORD`** URL-encoded if it contains `@` or other reserved characters.
2. `docker compose up -d` (no `mock-rtsp` profile).
3. Same Frigate UI and `event_watcher.py` flow as above.

**`CAMERA_RTSP_PORT`:** defaults to **`554`** in Compose if omitted (see `docker-compose.yml`).

---

## iMessage

- **`IMESSAGE_DRY_RUN=true`**: log only, no Messages send.
- Grant **Automation** for your terminal / Python → **Messages** (`System Settings → Privacy & Security → Automation`).

---

## Script reference

| Script | Role |
|--------|------|
| `scripts/lawn_alert.py` | v2 main loop (snapshot + motion + iMessage) |
| `scripts/snapshot_ingest.py` | HTTP snapshot fetch |
| `scripts/detect_motion.py` | ROI frame diff |
| `scripts/send_imessage.py` | AppleScript wrapper |
| `scripts/send_imessage.applescript` | Messages.app |
| `scripts/test_snapshot_url.py` | Snapshot URL / mock smoke test |
| `scripts/test_imessage.py` | iMessage smoke test |
| `scripts/mock_frame_generator.py` | Synthetic JPEG helper |
| `scripts/event_watcher.py` | Frigate event poller + iMessage |
| `scripts/test_frigate_connection.py` | Frigate API check |
| `scripts/mock_event_generator.py` | Dev helper for events |
| `scripts/env_util.py` | Loads `.env` then `.env.local` |

---

## Config layout

| Path | Role |
|------|------|
| `config/frigate.yml` | Frigate cameras / zones / objects |
| `config/mediamtx.yml` | **Mock RTSP** (MediaMTX + ffmpeg testsrc) |
| `config/roi.json` | v2 lawn polygon |

More detail: **`docs/setup.md`**, **`docs/troubleshooting.md`**.

## Codex / agent workflow

1. Open this repo root in Codex (or Cursor with `AGENTS.md`).
2. `cp .env.example .env` and keep **`MOCK_MODE=true`** / **`IMESSAGE_DRY_RUN=true`** until hardware is ready.
3. Run **`./scripts/validate_dev.sh`** after each task.
4. Implement the next **`todo`** in **`docs/BACKLOG.md`**; update checkboxes when done.
