from __future__ import annotations

import json
import os
from io import BytesIO
from pathlib import Path
from typing import Sequence

import numpy as np
from PIL import Image, ImageDraw


def load_polygon(project_root: Path) -> list[tuple[float, float]]:
    roi_path = project_root / "config" / "roi.json"
    if roi_path.exists():
        data = json.loads(roi_path.read_text())
        poly = data.get("polygon")
        if isinstance(poly, list) and len(poly) >= 3:
            out: list[tuple[float, float]] = []
            for point in poly:
                if isinstance(point, (list, tuple)) and len(point) == 2:
                    out.append((float(point[0]), float(point[1])))
            if len(out) >= 3:
                return out
    env_poly = os.getenv("ROI_POLYGON", "").strip()
    if not env_poly:
        raise ValueError("Define lawn ROI in config/roi.json or set ROI_POLYGON in .env.")
    parts = [float(x) for x in env_poly.replace(" ", "").split(",") if x]
    if len(parts) < 6 or len(parts) % 2:
        raise ValueError("ROI_POLYGON must be x,y pairs: x1,y1,x2,y2,...")
    return list(zip(parts[0::2], parts[1::2]))


def _mask_from_polygon(width: int, height: int, polygon: Sequence[tuple[float, float]]) -> np.ndarray:
    mask_img = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask_img)
    pixels = [(int(x * width), int(y * height)) for x, y in polygon]
    draw.polygon(pixels, fill=255)
    return np.array(mask_img, dtype=bool)


class MotionDetector:
    """Tier-1: fraction of ROI pixels where |I - I_prev| > intensity_delta."""

    def __init__(
        self,
        polygon: Sequence[tuple[float, float]],
        intensity_delta: int = 25,
    ) -> None:
        self.polygon = list(polygon)
        self.intensity_delta = intensity_delta
        self._prev: np.ndarray | None = None
        self._mask: np.ndarray | None = None
        self._shape: tuple[int, int] | None = None

    def reset(self) -> None:
        self._prev = None
        self._mask = None
        self._shape = None

    def score(self, jpeg_bytes: bytes) -> float:
        image = Image.open(BytesIO(jpeg_bytes)).convert("L")
        current = np.asarray(image, dtype=np.int16)
        height, width = current.shape
        shape = (height, width)
        if self._shape != shape:
            self._shape = shape
            self._mask = _mask_from_polygon(width, height, self.polygon)
            self._prev = None
        assert self._mask is not None
        if self._prev is None:
            self._prev = current.copy()
            return 0.0
        diff = np.abs(current - self._prev)
        changed = np.logical_and(diff > self.intensity_delta, self._mask)
        total = int(np.count_nonzero(self._mask))
        self._prev = current.copy()
        if total == 0:
            return 0.0
        return float(np.count_nonzero(changed) / total)
