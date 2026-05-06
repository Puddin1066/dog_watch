from __future__ import annotations

import os
from pathlib import Path

from env_util import load_project_env, project_root
from send_imessage import send_imessage


def main() -> None:
    load_project_env(project_root())
    target = os.getenv("IMESSAGE_TARGET", "")
    if not target:
        raise ValueError("Set IMESSAGE_TARGET in your environment or .env.")

    fixture = Path("./storage/snapshots/test_fixture.jpg")
    fixture.parent.mkdir(parents=True, exist_ok=True)
    if not fixture.exists():
        fixture.write_bytes(
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\x99c\xf8\xff"
            b"\xff?\x00\x05\xfe\x02\xfeA\xf4\x9f\xc9\x00\x00\x00\x00IEND\xaeB`\x82"
        )

    send_imessage(target, "Test dog alert from local watcher.", fixture)
    print("iMessage test sent successfully.")


if __name__ == "__main__":
    main()
