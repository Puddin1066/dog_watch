from __future__ import annotations

import os

from env_util import load_project_env, project_root
from snapshot_ingest import fetch_snapshot, tls_verify_from_env


def main() -> None:
    root = project_root()
    load_project_env(root)
    mock = os.getenv("MOCK_MODE", "false").lower() == "true"
    url = os.getenv("SNAPSHOT_URL", "").strip()
    user = os.getenv("SNAPSHOT_HTTP_USER", "").strip()
    password = os.getenv("SNAPSHOT_HTTP_PASSWORD", "").strip()
    verify = tls_verify_from_env()

    data = fetch_snapshot(
        url,
        http_user=user,
        http_password=password,
        tls_verify=verify,
        mock_mode=mock,
    )
    if len(data) < 100:
        raise RuntimeError(f"Snapshot too small ({len(data)} bytes).")
    if not data.startswith(b"\xff\xd8"):
        print("Warning: body does not start with JPEG SOI; continuing if image tools accept it.")
    print(f"OK: fetched {len(data)} bytes (mock={mock}).")


if __name__ == "__main__":
    main()
