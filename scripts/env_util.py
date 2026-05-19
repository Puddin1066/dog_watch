"""Load `.env` then `.env.local` from project root (later files override)."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_project_env(root: Path | None = None) -> None:
    base = root or project_root()
    preexisting = set(os.environ.keys())
    for name in (".env", ".env.local"):
        path = base / name
        if not path.exists():
            continue
        for raw_line in path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            if key in preexisting:
                continue
            os.environ[key] = value.strip()
