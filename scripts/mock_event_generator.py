from __future__ import annotations

import json
import time


def generate_mock_event() -> dict[str, object]:
    now = time.time()
    return {
        "id": f"mock-{int(now)}",
        "label": "dog",
        "zones": ["front_lawn"],
        "start_time": now - 7.2,
        "end_time": now,
        "has_snapshot": True,
        "source": "MOCK_API_CALL",
    }


if __name__ == "__main__":
    print(json.dumps(generate_mock_event(), indent=2))
