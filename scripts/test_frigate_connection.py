from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

import requests
import urllib3

from env_util import load_project_env, project_root

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def _tls_verify(base_url: str) -> bool:
    if os.getenv("FRIGATE_TLS_VERIFY", "").lower() in ("0", "false", "no"):
        return False
    host = (urlparse(base_url).hostname or "").lower()
    if host in ("localhost", "127.0.0.1"):
        return False
    return True


def main() -> None:
    load_project_env(project_root())
    base_url = os.getenv("FRIGATE_BASE_URL", "https://localhost:8971").rstrip("/")
    verify = _tls_verify(base_url)
    username = os.getenv("FRIGATE_USERNAME", "")
    password = os.getenv("FRIGATE_PASSWORD", "")
    events_url = f"{base_url}/api/events"
    session = requests.Session()
    headers: dict[str, str] = {}

    if username and password:
        login = session.post(
            f"{base_url}/api/login",
            json={"user": username, "password": password},
            timeout=10,
            verify=verify,
        )
        login.raise_for_status()
        if not login.cookies.get("frigate_token"):
            try:
                token = login.json().get("access_token")
            except Exception:
                token = None
            if token:
                headers = {"Authorization": f"Bearer {token}"}
            else:
                raise RuntimeError(
                    "Frigate login succeeded but no frigate_token cookie or access_token."
                )

    response = session.get(events_url, headers=headers, timeout=10, verify=verify)
    if response.status_code in (401, 403):
        raise RuntimeError(
            "Frigate API is protected. Set FRIGATE_USERNAME and FRIGATE_PASSWORD in .env."
        )
    response.raise_for_status()
    events = response.json()
    print(f"Connected. Events returned: {len(events) if isinstance(events, list) else 'unknown'}")

    if isinstance(events, list) and events:
        event_id = events[0].get("id")
        if event_id:
            snapshot = session.get(
                f"{base_url}/api/events/{event_id}/snapshot.jpg",
                headers=headers,
                timeout=10,
                verify=verify,
            )
            snapshot.raise_for_status()
            print("Snapshot endpoint is accessible.")
    else:
        print("No events yet. Snapshot endpoint not checked.")


if __name__ == "__main__":
    main()
