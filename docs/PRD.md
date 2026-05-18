# PRD — Reolink E1 + Mac + iMessage Dog-on-Lawn Alert System (v2 — non-RTSP ingest)

## Document status (v2 redesign)

**Original PRD (v1)** assumed **continuous RTSP → Frigate → zone-filtered dog events**.  
**Reolink E1 (standalone)** does not match that model: Reolink documents **RTSP/ONVIF/CGI for E1 only when the camera is used with a Home Hub or NVR**, and **E1 / Lumus** do not expose the usual **HTTP/HTTPS/RTSP/ONVIF port toggles** for standalone LAN streaming like **E1 Pro** ([Which products support CGI / RTSP / ONVIF](https://support.reolink.com/hc/en-us/articles/900000617826-Which-Reolink-Products-Support-CGI-RTSP-ONVIF), [Port settings](https://support.reolink.com/articles/900000621783-How-to-Configure-Reolink-Ports-Settings/)).

**v2** replaces camera **RTSP ingest** with **non-RTSP still-image ingest** and **Mac-side logic**. **Frigate is optional Phase 2** (see appendix) if you later attach a **Home Hub / NVR** that exposes RTSP to the LAN.

## Project Overview

Build a local-first lawn monitoring system using a **Reolink E1** Wi‑Fi camera and **macOS iMessage**, **without** requiring a **continuous RTSP** feed from the camera for MVP.

The system must:

1. **Acquire lawn images** over **HTTP/HTTPS** (JPEG snapshots) or via an **optional Home Assistant** snapshot proxy — **no RTSP URL required** from the E1 for MVP v2.
2. **Decide when to alert** using **MVP rules** (motion / frame-diff / optional lightweight classifier — see **Detection tiers**).
3. **Infer likely dog-poop events** only as **post-MVP** behavioral logic (same spirit as v1, but not blocking MVP).
4. **Capture and retain** snapshot images locally for debugging.
5. Send **text + image** to the user via **iMessage** in near real time (subject to poll interval and cooldown).
6. Run **entirely on a Mac** during MVP (**Docker optional**; only required for Phase 2 Frigate).

This project is intended as:

- A practical **event + snapshot** automation prototype.
- A foundation for a future edge-AI SaaS product.
- A low-cost **local** system that respects E1 hardware constraints.

---

# High-Level Architecture (v2)

```text
Reolink E1 Wi‑Fi Camera
        ↓ still images only (HTTP/HTTPS snapshot URLs — no RTSP)
Optional: Home Assistant "camera snapshot" / automation webhook
        ↓
Python ingest service (poll + decode JPEG)
        ↓ ROI / motion-diff / optional local classifier (MVP tiers)
        ↓ cooldown + dedupe
AppleScript / osascript
        ↓
iMessage text + snapshot image
```

**Phase 2 (optional, not MVP v2):** Home Hub/NVR → **RTSP** → **Frigate** → same iMessage path (reuse v1 components if desired).

---

# Core Functional Goal (v2)

The system is considered successful when:

```text
The Mac periodically obtains a lawn snapshot without using RTSP,
the MVP detection rule fires (see Detection tiers),
a snapshot file is saved locally,
and the Mac sends that snapshot to the configured iMessage recipient,
respecting cooldown.
```

**Stretch goal (same as v1 spirit):** reduce false positives until “dog on lawn” is **usually** correct — acknowledge **not** Frigate-grade continuous multi-object tracking on standalone E1.

---

# MVP Scope

## Included (v2)

- **Non-RTSP ingest**: configurable **HTTP(S) JPEG snapshot** acquisition (poll interval from `.env`).
- **Lawn ROI**: user-defined **rectangle or polygon** in **normalized coordinates** (0–1) applied to JPEGs in Python (OpenCV or Pillow), not Frigate YAML zones.
- **Detection tier 1 (MVP default):** **frame-difference** inside ROI vs static background capture (or vs previous frame) + **minimum changed pixel ratio** + **cooldown**.
- **Detection tier 2 (optional flag):** integrate **Home Assistant** motion binary sensor or webhook as **pre-gate** (if user runs HA).
- **Detection tier 3 (optional flag):** call **Apple Vision / Core ML / ONNX** dog classifier on ROI crops (implementation choice left to build; must be **local** for MVP).
- Local **ingest + alert** service (single process acceptable for MVP).
- **iMessage** text/image sending (AppleScript).
- **Cooldown** + basic **dedupe** (hash or perceptual hash of last alert image).
- **Logging** (startup, HTTP failures, suppressions, iMessage outcomes).
- **Mock mode** for development without camera traffic (clearly labeled).

## Excluded

- **Continuous RTSP** from standalone **E1** as an MVP requirement.
- **Frigate** as MVP requirement (Phase 2 only).
- SaaS dashboard.
- Multi-user auth.
- Twilio.
- **Cloud inference** for MVP (tier 3 must stay local if enabled).
- Facial recognition.
- Custom full model training pipeline.
- Production-grade distributed systems.
- Guaranteed confirmation of defecation.

---

# Hardware Requirements

## Required

### Camera

- **Reolink E1** (Wi‑Fi, continuous power).  
  **Note:** v2 does **not** require standalone RTSP. If you later add **Home Hub / NVR** or switch to **E1 Pro**, you may enable **Phase 2 Frigate** (appendix).

Requirements:

- Wi‑Fi connectivity
- Continuous power
- **1080p or higher** recommended (for usable JPEG detail in ROI)

### Compute

Mac capable of:

- **Python 3.11+**
- Optional: **Docker Desktop** (Phase 2 Frigate only)
- Running continuously during testing

### Network

- Camera and Mac must share the same local network **for HTTP snapshot reachability** (exact URL depends on integration path; see **Ingest**).

### Optional (MVP tier 2)

- **Home Assistant** on the same LAN if using HA motion pre-gate or HA snapshot proxy.

---

# Software Stack (v2)

| Layer | Technology |
|---|---|
| Camera ingest | **HTTP(S) JPEG** (poll) or **HA snapshot API** / webhook |
| Motion / ROI | **OpenCV** or Pillow + numpy (frame diff inside polygon) |
| Optional classify | **Vision / Core ML / ONNX** (local only) |
| Optional Phase 2 | **Frigate** + Docker (RTSP from Hub/NVR only) |
| Event processing | Python |
| Messaging | AppleScript + iMessage |
| Configuration | `.env` + optional `config/roi.json` |
| Logging | Python `logging` |

---

# Repository Structure (v2)

```text
reolink-dog-alert/
├── README.md
├── docker-compose.yml          # optional: Frigate Phase 2 only
├── .env.example
├── .gitignore
├── config/
│   ├── roi.json                 # lawn polygon or bbox (normalized coords)
│   └── frigate.yml              # optional Phase 2 only
├── scripts/
│   ├── lawn_alert.py            # v2 main loop (ingest + detect + iMessage)
│   ├── snapshot_ingest.py       # HTTP GET JPEG + retries
│   ├── detect_motion.py         # ROI frame-diff + thresholds
│   ├── send_imessage.py
│   ├── send_imessage.applescript
│   ├── test_snapshot_url.py     # verifies JPEG download
│   ├── test_imessage.py
│   └── mock_frame_generator.py  # synthetic frames for dev
├── logs/
│   └── alerts.log
├── storage/
│   ├── frigate/                 # optional Phase 2
│   └── snapshots/
└── docs/
    ├── setup.md
    ├── troubleshooting.md
    └── architecture.md
```

**Migration note:** Existing `event_watcher.py` / Frigate test scripts map to **Phase 2** or can be **deprecated** in favor of `lawn_alert.py` for v2.

---

# Required Environment Variables (v2)

## `.env.example`

```bash
# --- Snapshot ingest (no RTSP) ---
# Full URL to a JPEG (illustrative — use Home Assistant snapshot proxy or vendor-documented URL for your deployment)
SNAPSHOT_URL=https://homeassistant.local:8123/api/camera_proxy/camera.lawn?token=...
# If the URL needs HTTP Basic auth:
SNAPSHOT_HTTP_USER=admin
SNAPSHOT_HTTP_PASSWORD=change_me
# TLS verify for snapshot host (often false for self-signed cams)
SNAPSHOT_TLS_VERIFY=false

# Optional Home Assistant pre-gate (tier 2)
# HA_BASE_URL=http://homeassistant.local:8123
# HA_TOKEN=long_lived_access_token
# HA_MOTION_ENTITY_ID=binary_sensor.front_lawn_motion

# --- ROI / detection (tier 1 default) ---
# Normalized polygon "x1,y1,x2,y2,..." or bbox "x,y,w,h" in 0..1
ROI_POLYGON=0.1,0.55,0.9,0.55,0.95,0.95,0.05,0.95
MOTION_THRESHOLD=0.02
MIN_CONSECUTIVE_HITS=3
POLL_INTERVAL_SECONDS=2

# --- Alerting ---
ALERT_COOLDOWN_SECONDS=180
IMESSAGE_TARGET=+15555555555
ALERT_MESSAGE=Possible dog event detected on front lawn.

# --- Runtime ---
MOCK_MODE=false
IMESSAGE_DRY_RUN=true
SNAPSHOT_DIR=./storage/snapshots
LOG_FILE=./logs/alerts.log

# --- Optional Phase 2 (Frigate + RTSP from Hub/NVR) ---
# FRIGATE_BASE_URL=https://localhost:8971
# FRIGATE_USERNAME=admin
# FRIGATE_PASSWORD=
```

**Important:** `SNAPSHOT_URL` is **integration-specific**. The implementer must document **one supported path** in `docs/setup.md` (e.g. HA `camera.snap` service URL, or vendor-documented CGI if available for the deployment). **Mock** `SNAPSHOT_URL` for CI.

---

# Docker Requirements (optional — Phase 2 only)

If Frigate is enabled, `docker-compose.yml` should follow current best practices (e.g. **HTTPS on 8971** on macOS when AirPlay occupies **5000**). **v2 MVP does not require Docker.**

Example (abbreviated):

```yaml
services:
  frigate:
    image: ghcr.io/blakeblackshear/frigate:stable
    container_name: frigate
    privileged: true
    restart: unless-stopped
    shm_size: "256mb"
    ports:
      - "8971:8971"
    volumes:
      - ./config:/config
      - ./storage/frigate:/media/frigate
```

RTSP `path` in `config/frigate.yml` applies **only** when a **Hub/NVR** exposes RTSP to Frigate.

---

# Ingest Requirements (v2)

## `scripts/snapshot_ingest.py`

- `GET` `SNAPSHOT_URL` with timeouts and **retry/backoff**.
- Support **HTTP Basic** auth via `SNAPSHOT_HTTP_USER` / `SNAPSHOT_HTTP_PASSWORD`.
- Validate `Content-Type` is image or body parses as JPEG; raise clear errors.
- **Mock mode:** when `MOCK_MODE=true`, return a **synthetic JPEG** path and log `[MOCK]`.

## Optional HA pre-gate (`tier 2`)

- If `HA_*` vars set, query HA REST for `binary_sensor` state **before** spending CPU on frame diff.

---

# Detection Logic (v2)

## Tier 1 — default MVP

Trigger when:

```text
JPEG acquired
AND ROI crop differs from reference/background by > MOTION_THRESHOLD
AND MIN_CONSECUTIVE_HITS satisfied (debounce)
AND cooldown expired
```

## Tier 3 — optional

When `CLASSIFIER=vision` (or similar) is set, add:

```text
AND local classifier P(dog) > threshold on ROI crop
```

**Out of scope for MVP:** Frigate-style **multi-object tracks** and **polygon zones in NVR config** on standalone E1.

## Alert copy

Default message:

```text
Possible dog event detected on front lawn.
```

---

# Lawn Alert Service Requirements

## File

```text
scripts/lawn_alert.py
```

## Responsibilities

1. Load `.env` and optional `config/roi.json`.
2. Poll `SNAPSHOT_URL` every `POLL_INTERVAL_SECONDS`.
3. Run **tier 1** (and optional **tier 2/3**) detection.
4. Enforce **cooldown** and **dedupe**.
5. Save JPEGs to `SNAPSHOT_DIR` with monotonic filenames.
6. Invoke **iMessage** sender.
7. Log all outcomes.

## Pseudo-flow

```text
Start lawn_alert
↓
Load .env
↓
Loop:
    fetch snapshot (or MOCK)
    optional HA motion gate
    run ROI motion-diff (+ optional classifier)
    if qualifies:
        save snapshot
        send iMessage (unless DRY_RUN)
        update cooldown + last-hash
    log
↓
Repeat forever
```

---

# Snapshot Handling

Snapshots must:

- Be downloaded locally from `SNAPSHOT_URL` (or generated in **MOCK** mode with explicit `[MOCK]` logging).
- Be saved with **timestamp- or monotonic** filenames (Frigate `event_id` is not available in v2).
- Be retained for debugging.

Example:

```text
storage/snapshots/20260506T131927Z.jpg
```

---

# iMessage Integration Requirements

## Approach

Use:

```text
osascript
```

with:

```text
AppleScript
```

No Twilio.

No SMS gateways.

Messages are sent directly through the local Messages app.

---

# AppleScript Requirements

## File

```text
scripts/send_imessage.applescript
```

## Required functionality

The script must:

1. Send text.
2. Send image attachment.
3. Use configurable target number.

Expected behavior:

```text
Possible dog event detected on front lawn.
[image attached]
```

---

# Python iMessage Wrapper

## File

```text
scripts/send_imessage.py
```

Responsibilities:

- Invoke osascript.
- Validate snapshot path exists.
- Handle subprocess failures.
- Raise clear errors.

---

# Logging Requirements

## File

```text
logs/alerts.log
```

Must log:

- startup
- **snapshot URL reachability** (HTTP status, latency)
- optional **HA pre-gate** state when enabled
- qualifying **motion / classifier** hits
- skipped frames (below threshold)
- cooldown suppression
- iMessage success
- iMessage failure
- snapshot download failures

Example:

```text
[INFO] Snapshot fetched (200, 42ms).
[INFO] Motion score 0.041 above threshold; consecutive hits 3/3.
[INFO] Snapshot saved.
[INFO] iMessage sent successfully.
```

---

# Cooldown Requirements

To avoid spam:

```text
No additional alert for configured cooldown duration.
```

Default:

```text
180 seconds
```

---

# Testing Requirements

## Test Scripts

Cursor must implement:

### `test_snapshot_url.py`

Verifies:

- `SNAPSHOT_URL` returns a decodable JPEG (or documented image format)
- auth headers work when configured
- TLS options behave as expected

### `test_imessage.py`

Verifies:

- Messages automation permissions
- text sending
- image sending

### `mock_frame_generator.py`

Produces synthetic JPEGs or ndarray fixtures so **motion-diff** and optional classifiers can be unit-tested **without** the camera.

### `test_frigate_connection.py` (Phase 2 only)

Verifies Frigate only when Docker + Frigate are in scope.

---

# Acceptance Criteria (v2)

The project is complete only when:

## Ingest

- `SNAPSHOT_URL` (or **MOCK** path) reliably returns images in dev and on LAN.
- Transient HTTP failures are retried; permanent failures surface clearly in logs.

## Detection

- **Tier 1** motion rule fires on controlled test footage (recorded clip or mock frames) with **tunable** false-positive rate.
- **ROI** matches the physical lawn area after user calibration doc steps.

## Event logic

- **Cooldown** prevents alert spam.
- **Dedupe** prevents duplicate sends for visually identical frames (configurable strictness).

## Snapshot

- Each alert persists a **local JPEG** under `SNAPSHOT_DIR`.

## Messaging

- iMessage sends automatically (unless `IMESSAGE_DRY_RUN=true`).
- Image attachment appears.
- Message reaches configured phone.

## Reliability

- `lawn_alert.py` recovers from temporary HTTP failures (backoff, no crash loop).
- Optional: if Phase 2 Frigate is enabled, Docker restart policy keeps Frigate alive (not required for v2 MVP sign-off).

---

# macOS Setup Requirements

Cursor must document:

## Required user setup

1. Install **Python 3.11+**.
2. Install **Docker Desktop** only if using **Phase 2 Frigate**.
3. Sign into Messages.
4. Confirm iMessage works manually.
5. Disable sleep during testing.
6. Grant automation permissions.

## Automation permissions

Document:

```text
System Settings → Privacy & Security → Automation
```

---

# Reolink Setup Requirements (v2)

Document:

1. Connect camera to Wi‑Fi.
2. **Reserve DHCP** (static lease) for the camera MAC — IP must stay stable for `SNAPSHOT_URL`.
3. **Choose ingest path** and document it in `docs/setup.md`:
   - **Preferred:** Home Assistant **camera snapshot** or **local file** URL the Mac can `GET` repeatedly.
   - **If Reolink documents an HTTP snapshot URL** for your exact firmware/deployment, that may be used — **do not assume** standalone E1 exposes CGI/RTSP without Hub/NVR (see [compatibility](https://support.reolink.com/hc/en-us/articles/900000617826-Which-Reolink-Products-Support-CGI-RTSP-ONVIF)).
4. Enable **smart / motion** alerts in the Reolink app as needed for framing; v2 MVP may still **poll JPEGs** regardless of push notifications.

**Removed from v2 MVP:** “Verify RTSP in VLC” as a gate — RTSP is **not** the primary ingest.

---

# Window Camera Optimization

Document:

## Required changes for indoor-through-window use

### Disable IR

The Reolink IR LEDs must be disabled at night to avoid window glare.

### Camera framing

Frame:

- mostly lawn
- minimal sky
- minimal street

### Lighting

Use:

- porch lights
- street lights
- external illumination

instead of IR reflection.

---

# Multi-Agent Cursor Build Instructions

Cursor must operate using multiple coordinated implementation agents.

## Agent Roles

### Agent 1 — Infrastructure

Responsibilities:

- repo scaffold
- optional Docker (Phase 2)
- environment config
- README

### Agent 2 — Ingest + vision

Responsibilities:

- `SNAPSHOT_URL` integration (and HA optional path)
- JPEG decode + ROI pipeline
- motion-diff thresholds + optional classifier hook
- calibration docs (`docs/setup.md`)

### Agent 3 — Alert core

Responsibilities:

- `lawn_alert.py` main loop
- cooldown + dedupe
- snapshot persistence
- structured logging

### Agent 4 — iMessage

Responsibilities:

- AppleScript
- Python wrapper
- attachment handling
- permissions

### Agent 5 — QA / Iteration

Responsibilities:

- run tests
- patch failures
- validate objective success
- iterate until success

---

# Iteration Rule

Agents must iterate until:

```text
A real-world lawn disturbance (or staged test) produces a successful iMessage
with image attachment, with false positives tuned to an agreed acceptable level for tier-1 MVP.
```

Mock tests are acceptable before hardware validation. **Dog-specific accuracy** is a **stretch** until tier 3 or Phase 2 Frigate.

---

# Build Order (v2)

1. Repository scaffold + `.env.example` + `config/roi.json` template.
2. `snapshot_ingest.py` + `test_snapshot_url.py` (include **MOCK** path).
3. `detect_motion.py` + unit tests with `mock_frame_generator.py`.
4. `lawn_alert.py` integrating ingest + detect + cooldown.
5. AppleScript messaging + `test_imessage.py`.
6. End-to-end dry run (`IMESSAGE_DRY_RUN=true`) on LAN.
7. Live iMessage validation (`IMESSAGE_DRY_RUN=false`) with human-in-loop false-positive tuning.
8. **Optional Phase 2:** Docker + Frigate + RTSP from Hub/NVR only if hardware supports it.

---

# Final Runtime Commands (v2)

## Run lawn alert (MVP)

```bash
python scripts/lawn_alert.py
```

## Optional — start Frigate (Phase 2 only)

```bash
docker compose up -d
```

---

# Future Enhancements (Not MVP)

## Behavioral inference

Potential future logic:

```text
dog
+ stationary
+ hindquarters lowered
+ person nearby
→ likely poop event
```

## Additional future features

- **Phase 2 Frigate** when **Home Hub/NVR** provides RTSP (restore v1-style continuous CV).
- video clip alerts
- cloud sync
- mobile app
- neighborhood analytics
- repeat offender tracking
- managed appliance hardware
- Twilio fallback
- Vercel dashboard
- deeper Home Assistant integration (blueprints, presence)

---

# Appendix — Phase 2 (Frigate + RTSP, optional)

Use this appendix **only** if the deployment adds **Reolink Home Hub / NVR** (or replaces camera with **standalone RTSP** models such as **E1 Pro** per Reolink docs). Then:

- Run **Frigate** in Docker with RTSP `path` pointed at the **Hub/NVR/camera** stream.
- Optionally reuse **Frigate zones + dog labels** and a thin watcher that polls **`/api/events`** as in v1.

---

# Final Objective (v2)

The finished MVP should behave like this:

```text
Motion or change on lawn ROI (from JPEG stream)
↓
Mac evaluates tier-1 (optional tier-2/3) rules
↓
Snapshot saved locally
↓
Mac sends iMessage with image (respecting cooldown)
↓
User receives near-real-time alert
```

The implementation should prioritize:

- simplicity
- local-first operation
- reliability
- low cost
- maintainability
- rapid iteration
- **honest hardware constraints** (standalone E1 vs Hub/NVR vs E1 Pro)

