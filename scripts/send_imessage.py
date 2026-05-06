from __future__ import annotations

import subprocess
from pathlib import Path


def send_imessage(target: str, message: str, image_path: Path) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"Snapshot path does not exist: {image_path}")

    script_path = Path(__file__).with_name("send_imessage.applescript")
    command = [
        "osascript",
        str(script_path),
        target,
        message,
        str(image_path.resolve()),
    ]

    process = subprocess.run(command, capture_output=True, text=True, check=False)
    if process.returncode != 0:
        stderr = process.stderr.strip() or "Unknown osascript error"
        raise RuntimeError(f"Failed to send iMessage: {stderr}")
