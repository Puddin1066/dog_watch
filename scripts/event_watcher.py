from __future__ import annotations

# Phase 2 (optional): Frigate + RTSP when a Home Hub/NVR or standalone-RTSP camera is available.
# v2 MVP primary entrypoint: scripts/lawn_alert.py

import logging
import os
import time
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urlparse

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from env_util import load_project_env, project_root
from send_imessage import send_imessage


@dataclass(frozen=True)
class Settings:
    frigate_base_url: str
    frigate_username: str
    frigate_password: str
    target_zone: str
    min_duration_seconds: float
    alert_cooldown_seconds: int
    poll_interval_seconds: int
    imessage_target: str
    snapshot_dir: Path
    log_file: Path
    mock_mode: bool
    imessage_dry_run: bool


def get_settings() -> Settings:
    load_project_env(project_root())
    return Settings(
        frigate_base_url=os.getenv("FRIGATE_BASE_URL", "https://localhost:8971"),
        frigate_username=os.getenv("FRIGATE_USERNAME", ""),
        frigate_password=os.getenv("FRIGATE_PASSWORD", ""),
        target_zone=os.getenv("TARGET_ZONE", "front_lawn"),
        min_duration_seconds=float(os.getenv("MIN_EVENT_DURATION_SECONDS", "5")),
        alert_cooldown_seconds=int(os.getenv("ALERT_COOLDOWN_SECONDS", "180")),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "2")),
        imessage_target=os.getenv("IMESSAGE_TARGET", ""),
        snapshot_dir=Path(os.getenv("SNAPSHOT_DIR", "./storage/snapshots")),
        log_file=Path(os.getenv("LOG_FILE", "./logs/alerts.log")),
        mock_mode=os.getenv("MOCK_MODE", "false").lower() == "true",
        imessage_dry_run=os.getenv("IMESSAGE_DRY_RUN", "false").lower() == "true",
    )


def configure_logging(log_file: Path) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )


class FrigateClient(Protocol):
    def get_recent_events(self) -> list[dict[str, Any]]:
        ...

    def download_snapshot(self, event_id: str, out_path: Path) -> None:
        ...


def _frigate_tls_verify(base_url: str) -> bool:
    if os.getenv("FRIGATE_TLS_VERIFY", "").lower() in ("0", "false", "no"):
        return False
    host = (urlparse(base_url).hostname or "").lower()
    if host in ("localhost", "127.0.0.1"):
        return False
    return True


class HttpFrigateClient:
    def __init__(
        self,
        base_url: str,
        username: str = "",
        password: str = "",
        timeout: int = 10,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout
        self.verify = _frigate_tls_verify(self.base_url)
        self._session = requests.Session()
        self._session_logged_in = False
        self._bearer_token: str | None = None

    def _ensure_login(self) -> None:
        if self._session_logged_in:
            return
        if not self.username or not self.password:
            return

        response = self._session.post(
            f"{self.base_url}/api/login",
            json={"user": self.username, "password": self.password},
            timeout=self.timeout,
            verify=self.verify,
        )
        response.raise_for_status()
        if response.cookies.get("frigate_token"):
            self._session_logged_in = True
            return
        try:
            data = response.json()
        except Exception:
            data = {}
        token = data.get("access_token") if isinstance(data, dict) else None
        if token:
            self._bearer_token = token
            self._session_logged_in = True
            return
        raise RuntimeError(
            "Frigate login succeeded but no frigate_token cookie or access_token in response."
        )

    def _request_headers(self) -> dict[str, str]:
        if self._bearer_token:
            return {"Authorization": f"Bearer {self._bearer_token}"}
        return {}

    def get_recent_events(self) -> list[dict[str, Any]]:
        self._ensure_login()
        response = self._session.get(
            f"{self.base_url}/api/events",
            headers=self._request_headers(),
            timeout=self.timeout,
            verify=self.verify,
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, list) else []

    def download_snapshot(self, event_id: str, out_path: Path) -> None:
        self._ensure_login()
        response = self._session.get(
            f"{self.base_url}/api/events/{event_id}/snapshot.jpg",
            headers=self._request_headers(),
            timeout=self.timeout,
            verify=self.verify,
        )
        response.raise_for_status()
        out_path.write_bytes(response.content)


class MockFrigateClient:
    """Mocks Frigate HTTP events API only (no Docker). For synthetic RTSP, use docker compose profile mock-rtsp."""

    def get_recent_events(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "mock-170202393",
                "label": "dog",
                "zones": ["front_lawn"],
                "end_time": time.time(),
                "start_time": time.time() - 7.2,
                "has_snapshot": True,
            }
        ]

    def download_snapshot(self, event_id: str, out_path: Path) -> None:
        # Clear MOCK indicator to avoid confusion with live detections.
        out_path.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\xff"
            b"\xff?\x00\x05\xfe\x02\xfeA\xf4\x9f\xc9\x00\x00\x00\x00IEND\xaeB`\x82"
        )


class AlertProcessor:
    def __init__(self, settings: Settings, client: FrigateClient) -> None:
        self.settings = settings
        self.client = client
        self.last_alert_at = 0.0
        self.processed_ids: set[str] = set()

    def run_forever(self) -> None:
        logging.info("Watcher started. mock_mode=%s", self.settings.mock_mode)
        if self.settings.mock_mode:
            logging.info("[MOCK] Mock event source enabled.")

        while True:
            try:
                for event in self.client.get_recent_events():
                    self._handle_event(event)
            except Exception as exc:
                logging.exception("Error while polling Frigate events: %s", exc)
            time.sleep(self.settings.poll_interval_seconds)

    def run_once(self) -> None:
        logging.info("Watcher one-shot run started. mock_mode=%s", self.settings.mock_mode)
        for event in self.client.get_recent_events():
            self._handle_event(event)

    def _handle_event(self, event: dict[str, Any]) -> None:
        event_id = str(event.get("id", ""))
        if not event_id or event_id in self.processed_ids:
            return

        if not self._qualifies(event):
            logging.info("Skipped non-qualifying event id=%s", event_id)
            self.processed_ids.add(event_id)
            return

        now = time.time()
        if now - self.last_alert_at < self.settings.alert_cooldown_seconds:
            logging.info("Cooldown suppression for event id=%s", event_id)
            self.processed_ids.add(event_id)
            return

        self.settings.snapshot_dir.mkdir(parents=True, exist_ok=True)
        snapshot_path = self.settings.snapshot_dir / f"{event_id}.jpg"
        self.client.download_snapshot(event_id, snapshot_path)
        logging.info("Snapshot saved to %s", snapshot_path)

        prefix = "[MOCK] " if self.settings.mock_mode else ""
        message = f"{prefix}Possible dog event detected on front lawn."
        if self.settings.imessage_dry_run:
            logging.info(
                "%s[DRY_RUN] iMessage skipped for event id=%s target=%s",
                prefix,
                event_id,
                self.settings.imessage_target,
            )
        else:
            send_imessage(self.settings.imessage_target, message, snapshot_path)
            logging.info("%siMessage sent successfully for event id=%s", prefix, event_id)

        self.last_alert_at = now
        self.processed_ids.add(event_id)

    def _qualifies(self, event: dict[str, Any]) -> bool:
        label = event.get("label")
        zones = event.get("zones", [])
        start_time = float(event.get("start_time") or 0)
        end_time = float(event.get("end_time") or time.time())
        duration = max(0.0, end_time - start_time)
        has_zone = self.settings.target_zone in zones
        return (
            label == "dog"
            and has_zone
            and duration >= self.settings.min_duration_seconds
            and bool(event.get("has_snapshot", True))
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Frigate dog event watcher")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one poll cycle and exit (useful for validation).",
    )
    args = parser.parse_args()

    settings = get_settings()
    configure_logging(settings.log_file)
    if not settings.imessage_target:
        raise ValueError("IMESSAGE_TARGET must be configured.")

    client: FrigateClient
    if settings.mock_mode:
        client = MockFrigateClient()
    else:
        client = HttpFrigateClient(
            base_url=settings.frigate_base_url,
            username=settings.frigate_username,
            password=settings.frigate_password,
        )

    processor = AlertProcessor(settings, client)
    if args.once:
        processor.run_once()
    else:
        processor.run_forever()


if __name__ == "__main__":
    main()
