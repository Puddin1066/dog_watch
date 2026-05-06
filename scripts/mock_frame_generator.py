from __future__ import annotations

import argparse
from io import BytesIO

from PIL import Image


def mock_jpeg_bytes(
    width: int = 320,
    height: int = 180,
    rgb: tuple[int, int, int] | None = None,
    *,
    seed: int = 0,
) -> bytes:
    """Tiny JPEG for tests and MOCK_MODE. Optional ``seed`` shifts color so motion-diff sees change."""
    if rgb is None:
        base_r, base_g, base_b = 64, 140, 90
        rgb = ((base_r + seed) % 256, (base_g + seed // 3) % 256, (base_b + seed // 5) % 256)
    image = Image.new("RGB", (width, height), color=rgb)
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=88)
    return buffer.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a synthetic JPEG to disk or stdout path")
    parser.add_argument("-o", "--output", type=str, default="", help="Output file path (.jpg)")
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=180)
    args = parser.parse_args()
    data = mock_jpeg_bytes(args.width, args.height)
    if args.output:
        path = args.output
        with open(path, "wb") as handle:
            handle.write(data)
        print(f"Wrote {len(data)} bytes to {path}")
    else:
        print(f"Mock JPEG size {len(data)} bytes (use -o path.jpg to save)")


if __name__ == "__main__":
    main()
