# Troubleshooting

## v2: `SNAPSHOT_URL` fails or empty

- Confirm the URL returns **JPEG** bytes (`python scripts/test_snapshot_url.py`).
- Try `SNAPSHOT_TLS_VERIFY=false` for self-signed HTTPS.
- Use **`MOCK_MODE=true`** to isolate motion + iMessage logic from the camera.

## Frigate API unreachable (Phase 2 only)

- Verify Frigate is running: `docker compose ps`
- Check Frigate logs: `docker compose logs frigate`
- Confirm `FRIGATE_BASE_URL` in `.env`

## No detections

- Validate camera RTSP URL in `config/frigate.yml`
- Check zone coordinates for `front_lawn`
- Confirm `dog` appears in Frigate UI events

## Reolink E1: no RTSP / port 554 never opens

**Standalone E1:** Reolink documents that **E1** gets **RTSP/ONVIF through a Home Hub or NVR**, not the same standalone LAN RTSP story as **E1 Pro**. The mobile app often has **no RTSP toggle** for that reason.

- [Which Reolink Products Support CGI / RTSP / ONVIF](https://support.reolink.com/hc/en-us/articles/900000617826-Which-Reolink-Products-Support-CGI-RTSP-ONVIF)
- [How to Configure Reolink Ports Settings](https://support.reolink.com/articles/900000621783-How-to-Configure-Reolink-Ports-Settings/)

**What to do:** Use an **RTSP URL from your Home Hub/NVR** (or upgrade to a model with **standalone** RTSP, e.g. **E1 Pro** per Reolink’s table), put that host/credentials/path into `.env` / `config/frigate.yml`, then restart Frigate.

Until Frigate receives a working stream, the UI will show no useful `lawn_cam` video and there will be no real detection events.

## iMessage failures

- Ensure Messages app is signed in
- Re-run `python3 scripts/test_imessage.py`
- Grant Automation permission for your terminal and `osascript`

## Snapshot download errors

- Confirm event has snapshots in Frigate
- Check local write permissions for `storage/snapshots`

## Mock mode confusion

- **`MOCK_MODE=true`** in `.env`: `event_watcher.py` uses a **mock Frigate HTTP API** (no Frigate container). Logs/messages include **`[MOCK]`**.
- **Docker `--profile mock-rtsp`**: **MediaMTX** publishes a **synthetic RTSP** test pattern (`e1pro-mock`). That is **not** the same as `MOCK_MODE`; Frigate still runs and ingests a real RTSP connection from its perspective.
- Set **`MOCK_MODE=false`** when testing against a **live** Frigate instance.
