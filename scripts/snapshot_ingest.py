from __future__ import annotations

import logging
import os
import time
from typing import Any

import requests

from mock_frame_generator import mock_jpeg_bytes


def fetch_snapshot(
    url: str,
    *,
    http_user: str = "",
    http_password: str = "",
    tls_verify: bool = True,
    timeout: int = 15,
    retries: int = 3,
    mock_mode: bool = False,
) -> bytes:
    """Download a JPEG (or image) from SNAPSHOT_URL. MOCK_MODE returns a labeled synthetic JPEG."""
    if mock_mode:
        logging.info("[MOCK] snapshot_ingest: returning synthetic JPEG (no HTTP).")
        return mock_jpeg_bytes(seed=int(time.time() * 1000) % 256)

    if not url.strip():
        raise ValueError("SNAPSHOT_URL is empty. Set it in .env or enable MOCK_MODE=true.")

    auth: Any = None
    if http_user or http_password:
        auth = (http_user, http_password)

    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            response = requests.get(
                url,
                auth=auth,
                timeout=timeout,
                verify=tls_verify,
            )
            response.raise_for_status()
            data = response.content
            if not data:
                raise RuntimeError("Snapshot response body is empty.")
            ctype = (response.headers.get("Content-Type") or "").lower()
            if "image" not in ctype and not data.startswith(b"\xff\xd8"):
                logging.warning("Unexpected Content-Type %s; continuing if body looks like JPEG.", ctype)
            return data
        except Exception as exc:
            last_error = exc
            wait = 0.5 * (2**attempt)
            logging.warning("Snapshot fetch attempt %s failed: %s (retry in %.1fs)", attempt + 1, exc, wait)
            time.sleep(wait)
    assert last_error is not None
    raise RuntimeError(f"Snapshot fetch failed after {retries} attempts: {last_error}") from last_error


def tls_verify_from_env() -> bool:
    raw = os.getenv("SNAPSHOT_TLS_VERIFY", "true").lower()
    if raw in ("0", "false", "no"):
        return False
    return True
