from __future__ import annotations

import argparse
import hashlib
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from detect_motion import MotionDetector, load_polygon
from env_util import load_project_env, project_root
from send_imessage import send_imessage
from snapshot_ingest import fetch_snapshot, tls_verify_from_env


@dataclass(frozen=True)
class Settings:
    snapshot_url: str
    snapshot_user: str
    snapshot_password: str
    snapshot_tls_verify: bool
    mock_mode: bool
    imessage_dry_run: bool
    imessage_target: str
    alert_message: str
    poll_interval: float
    cooldown_seconds: float
    motion_threshold: float
    min_consecutive_hits: int
    intensity_delta: int
    snapshot_dir: Path
    log_file: Path
    dedupe_enabled: bool
    project_root: Path


def get_settings(root: Path) -> Settings:
    load_project_env(root)
    return Settings(
        snapshot_url=os.getenv("SNAPSHOT_URL", "").strip(),
        snapshot_user=os.getenv("SNAPSHOT_HTTP_USER", "").strip(),
        snapshot_password=os.getenv("SNAPSHOT_HTTP_PASSWORD", "").strip(),
        snapshot_tls_verify=tls_verify_from_env(),
        mock_mode=os.getenv("MOCK_MODE", "false").lower() == "true",
        imessage_dry_run=os.getenv("IMESSAGE_DRY_RUN", "false").lower() == "true",
        imessage_target=os.getenv("IMESSAGE_TARGET", "").strip(),
        alert_message=os.getenv(
            "ALERT_MESSAGE", "Possible dog event detected on front lawn."
        ).strip(),
        poll_interval=float(os.getenv("POLL_INTERVAL_SECONDS", "2")),
        cooldown_seconds=float(os.getenv("ALERT_COOLDOWN_SECONDS", "180")),
        motion_threshold=float(os.getenv("MOTION_THRESHOLD", "0.02")),
        min_consecutive_hits=int(os.getenv("MIN_CONSECUTIVE_HITS", "3")),
        intensity_delta=int(os.getenv("INTENSITY_DELTA", "25")),
        snapshot_dir=Path(os.getenv("SNAPSHOT_DIR", "./storage/snapshots")),
        log_file=Path(os.getenv("LOG_FILE", "./logs/alerts.log")),
        dedupe_enabled=os.getenv("DEDUPE_ENABLED", "true").lower() == "true",
        project_root=root,
    )


def configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


def ha_motion_allows() -> bool:
    base = os.getenv("HA_BASE_URL", "").strip().rstrip("/")
    token = os.getenv("HA_TOKEN", "").strip()
    entity = os.getenv("HA_MOTION_ENTITY_ID", "").strip()
    if not (base and token and entity):
        return True
    try:
        response = requests.get(
            f"{base}/api/states/{entity}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15,
        )
        if response.status_code != 200:
            logging.warning(
                "HA gate: %s for %s; allowing ingest.", response.status_code, entity
            )
            return True
        state = str(response.json().get("state", "")).lower()
        if state in ("on", "active", "true", "detected", "motion"):
            return True
        logging.debug("HA gate: state=%s → skip snapshot this cycle.", state)
        return False
    except Exception as exc:
        logging.warning("HA gate error (%s); allowing ingest.", exc)
        return True


class LawnAlertLoop:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        polygon = load_polygon(settings.project_root)
        self.detector = MotionDetector(polygon, intensity_delta=settings.intensity_delta)
        self._consecutive = 0
        self._last_alert_at = 0.0
        self._last_hash: str | None = None

    def _should_alert(self, jpeg: bytes, score: float) -> bool:
        if score < self.settings.motion_threshold:
            self._consecutive = 0
            return False
        self._consecutive += 1
        if self._consecutive < self.settings.min_consecutive_hits:
            return False

        now = time.time()
        if now - self._last_alert_at < self.settings.cooldown_seconds:
            logging.info(
                "Cooldown suppression (%.0fs remaining).",
                self.settings.cooldown_seconds - (now - self._last_alert_at),
            )
            self._consecutive = 0
            return False

        digest = hashlib.sha256(jpeg).hexdigest()
        if self.settings.dedupe_enabled and digest == self._last_hash:
            logging.info("Dedupe suppression (identical frame hash).")
            self._consecutive = 0
            return False

        self._consecutive = 0
        self._last_hash = digest
        self._last_alert_at = now
        return True

    def tick(self) -> None:
        if not ha_motion_allows():
            return

        jpeg = fetch_snapshot(
            self.settings.snapshot_url,
            http_user=self.settings.snapshot_user,
            http_password=self.settings.snapshot_password,
            tls_verify=self.settings.snapshot_tls_verify,
            mock_mode=self.settings.mock_mode,
        )
        score = self.detector.score(jpeg)
        logging.info("Motion score=%.4f (threshold=%.4f)", score, self.settings.motion_threshold)
        if not self._should_alert(jpeg, score):
            return

        self.settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self.settings.snapshot_dir / f"{stamp}.jpg"
        path.write_bytes(jpeg)
        logging.info("Snapshot saved to %s", path)

        prefix = "[MOCK] " if self.settings.mock_mode else ""
        message = f"{prefix}{self.settings.alert_message}"
        if self.settings.imessage_dry_run:
            logging.info("%s[DRY_RUN] iMessage skipped target=%s", prefix, self.settings.imessage_target)
        else:
            send_imessage(self.settings.imessage_target, message, path)
            logging.info("%siMessage sent.", prefix)

        self.detector.reset()


def main() -> None:
    parser = argparse.ArgumentParser(description="v2 lawn alert: HTTP snapshot + ROI motion + iMessage")
    parser.add_argument("--once", action="store_true", help="Run a single poll cycle and exit.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    settings = get_settings(root)
    configure_logging(settings.log_file)

    if not settings.imessage_target:
        raise ValueError("IMESSAGE_TARGET must be set in .env.")

    logging.info(
        "lawn_alert v2 start mock=%s dry_run=%s",
        settings.mock_mode,
        settings.imessage_dry_run,
    )

    loop = LawnAlertLoop(settings)
    if args.once:
        loop.tick()
        return

    while True:
        try:
            loop.tick()
        except Exception:
            logging.exception("tick failed")
        time.sleep(settings.poll_interval)


if __name__ == "__main__":
    main()
