# Architecture

## v2 MVP (default)

1. **`lawn_alert.py`** drives the loop at **`POLL_INTERVAL_SECONDS`**.
2. Optional **Home Assistant** gate: if `HA_*` is set, skip snapshot fetch when the motion entity is quiet.
3. **`snapshot_ingest.fetch_snapshot`** performs **HTTP GET** (or **`[MOCK]`** synthetic JPEGs).
4. **`detect_motion.MotionDetector`** compares consecutive grayscale frames inside a **normalized polygon ROI**.
5. **Cooldown** and **SHA-256 dedupe** gate alerts.
6. **`send_imessage.py`** invokes AppleScript to send text + image.

## Phase 2 (optional)

1. **RTSP source:** a **Reolink E1 Pro** (or other LAN RTSP camera), **or** the **Docker `mock-rtsp` profile** (**MediaMTX** + ffmpeg **testsrc** — clearly **[MOCK]** video, not a real dog scene).
2. **Frigate** ingests RTSP (see `config/frigate.yml` + Compose env) and emits `/api/events`.
3. **`event_watcher.py`** polls Frigate and reuses the same iMessage path (unless **`MOCK_MODE=true`**, which mocks the **Frigate HTTP API** instead).

## Design choices

- **Local-first** snapshot polling avoids Reolink **E1** standalone RTSP limitations.
- **Explicit `[MOCK]`** labeling for synthetic frames and dry-run iMessage.
- **Small modules** (`snapshot_ingest`, `detect_motion`, `lawn_alert`) for testability.
