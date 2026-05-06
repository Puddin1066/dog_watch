# Setup

## v2 MVP (snapshot + motion — default)

1. **Python 3.11+** and a venv: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
2. `cp .env.example .env` and configure:
   - **`SNAPSHOT_URL`**: any URL that returns a **JPEG** (common pattern: **Home Assistant** `camera_proxy` or snapshot service).
   - **`SNAPSHOT_HTTP_USER`** / **`SNAPSHOT_HTTP_PASSWORD`** if the URL needs Basic auth.
   - **`SNAPSHOT_TLS_VERIFY`**: `false` for self-signed HTTPS snapshot hosts.
3. **ROI:** edit **`config/roi.json`** (preferred) or set **`ROI_POLYGON`** in `.env` (normalized `x,y` pairs).
4. Tune **`MOTION_THRESHOLD`**, **`MIN_CONSECUTIVE_HITS`**, **`INTENSITY_DELTA`** (see PRD v2).
5. **`MOCK_MODE=true`** for development without a camera URL.
6. **`IMESSAGE_DRY_RUN=true`** until iMessage is verified.
7. Run **`python scripts/test_snapshot_url.py`**, then **`python scripts/lawn_alert.py`**.

## Optional — Phase 2 Frigate + RTSP

1. Install **Docker Desktop**.
2. **Mock RTSP (dev):** set **`CAMERA_IP=mock_rtsp`**, **`CAMERA_RTSP_PORT=8554`**, **`CAMERA_RTSP_PATH=e1pro-mock`** in `.env` (see `.env.example` Option A). Then:
   ```bash
   docker compose --profile mock-rtsp up -d
   ```
   **MediaMTX** serves a synthetic test pattern at `rtsp://mock_rtsp:8554/e1pro-mock` (**[MOCK]** — not a real camera). Frigate reads it via env substitution in **`config/frigate.yml`**.
3. **Real Reolink E1 Pro:** omit the `mock-rtsp` profile; set **`CAMERA_IP`**, **`CAMERA_RTSP_PORT=554`**, **`CAMERA_RTSP_PATH=h264Preview_01_main`**, and URL-encoded **`CAMERA_RTSP_PASSWORD`** as needed. `docker compose up -d`.
4. Open **`https://localhost:8971`**, finish first-time login, then set **`FRIGATE_USERNAME`** / **`FRIGATE_PASSWORD`** in `.env`.
5. `python scripts/test_frigate_connection.py`, then with **`MOCK_MODE=false`**, run **`python scripts/event_watcher.py`**.

**Note:** **`MOCK_MODE=true`** in `.env` makes **`event_watcher.py`** use a **mock Frigate HTTP client** (no live Frigate). That is separate from the **Docker mock RTSP** profile.

## macOS prerequisites

1. Sign in to **Messages** with iMessage enabled.
2. Confirm a manual iMessage send works.
3. Disable system sleep during testing.
4. Grant **Automation** in `System Settings → Privacy & Security → Automation` for your terminal and `osascript`.

## Reolink E1 note

Standalone **E1** does not provide the same **LAN RTSP** path as **E1 Pro**. Prefer a **snapshot URL** you control (e.g. **Home Assistant**) or add **Home Hub/NVR** for RTSP + optional Frigate (Phase 2). See the PRD v2 hardware section.
