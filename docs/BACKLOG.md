# Backlog (PRD v2 + Phase 2)

**Source of truth:** `docs/PRD.md`  
**Agent workflow:** `AGENTS.md` · **Codex how-to:** `docs/CODEX.md`

Status: `done` | `partial` | `todo`

---

## v2 MVP — build order (PRD § Build Order)

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Repo scaffold, `.env.example`, `config/roi.json` | done | |
| 2 | `snapshot_ingest.py` + `test_snapshot_url.py` + MOCK | done | Retries + synthetic JPEG |
| 3 | `detect_motion.py` + `mock_frame_generator.py` | partial | No `pytest` unit tests yet |
| 4 | `lawn_alert.py` (ingest + detect + cooldown) | done | HA pre-gate implemented |
| 5 | AppleScript + `send_imessage.py` + `test_imessage.py` | done | Manual macOS permissions |
| 6 | E2E dry run (`IMESSAGE_DRY_RUN=true`) | partial | Run on user LAN with real `SNAPSHOT_URL` |
| 7 | Live iMessage + false-positive tuning | todo | User + real lawn footage |
| 8 | `docs/setup.md` — **one documented SNAPSHOT_URL path** (HA or vendor) | partial | E1 Pro RTSP doc in README; snapshot URL TBD |

---

## v2 acceptance criteria (PRD § Acceptance Criteria)

| Criterion | Status | Verify with |
|-----------|--------|-------------|
| Ingest: MOCK or `SNAPSHOT_URL` reliable | partial | `MOCK_MODE=true python scripts/test_snapshot_url.py` |
| Ingest: retries / clear errors | done | `snapshot_ingest.py` |
| Tier-1 motion on test/mock frames | partial | Lower `MIN_CONSECUTIVE_HITS` + mock motion in `mock_frame_generator` |
| ROI matches lawn after calibration | todo | User edits `config/roi.json` + doc steps |
| Cooldown prevents spam | done | Logs in `lawn_alert.py` |
| Dedupe identical frames | done | SHA-256 in `lawn_alert.py` |
| Alert JPEG in `SNAPSHOT_DIR` | done | |
| iMessage auto-send (not dry-run) | todo | `python scripts/test_imessage.py` |
| `lawn_alert.py` survives HTTP blips | partial | Exception handler in main loop; add metrics if needed |

---

## Optional tiers (post-MVP v2)

| Item | Status | PRD ref |
|------|--------|---------|
| Tier 2: HA motion pre-gate | done | `HA_*` in `.env` |
| Tier 3: local dog classifier (Vision / ONNX) | todo | `CLASSIFIER` env hook not added |
| Background capture / reference frame tuning | todo | `detect_motion.reset()` after alert only |

---

## Phase 2 — Frigate + RTSP (appendix)

| Item | Status | Notes |
|------|--------|-------|
| `docker-compose.yml` + `config/frigate.yml` | done | Port 8971, env-based RTSP URL |
| Mock RTSP (`mock-rtsp` profile + MediaMTX) | done | `config/mediamtx.yml` |
| `event_watcher.py` + Frigate auth | done | Cookie + bearer login |
| `test_frigate_connection.py` | done | |
| E1 Pro LAN RTSP in `.env` (Option B) | todo | User hardware pending |
| Frigate zone `front_lawn` calibrated for real stream | todo | Edit coordinates in `frigate.yml` |
| End-to-end: real dog in zone → iMessage | todo | Needs live stream + `MOCK_MODE=false` |

---

## QA / engineering debt

| Item | Status |
|------|--------|
| `scripts/validate_dev.sh` one-shot dev check | done |
| `pytest` tests for `detect_motion` | todo |
| CI workflow (compile + mock smoke) | todo |
| Sync parent PRD if edited at `../reolink_e_1_...md` | todo | Copy to `docs/PRD.md` when canonical file changes |

---

## Changelog (agents: append one line per session)

- _2026-05-06_: Initial backlog; mock RTSP + Frigate Phase 2 scaffold committed.
