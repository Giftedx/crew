"""Minimal adaptive compression helpers."""

from __future__ import annotations

from pathlib import Path

# JPEG compression tuning constants
INITIAL_JPEG_QUALITY = 85  # Starting quality for adaptive downscale
MIN_JPEG_QUALITY = 35  # Lower bound to avoid excessive degradation (balances size vs fidelity)
QUALITY_STEP = 5  # Step decrement per iteration

try:
    from PIL import Image
except Exception:  # pragma: no cover - pillow optional
    Image = None  # type: ignore


def fit_to_limit(path_in: str | Path, bytes_limit: int, kind: str) -> tuple[Path, dict]:
    """Ensure the file at ``path_in`` fits within ``bytes_limit``.

    Currently performs simple JPEG re-encoding for images when Pillow is available
    and otherwise raises if the file is too large.
    """
    src = Path(path_in)
    dst = src
    stats: dict = {"original_size": src.stat().st_size}
    if kind == "images" and Image:
        with Image.open(src) as im:
            quality = INITIAL_JPEG_QUALITY
            dst = src.with_suffix(".jpg")
            while True:
                im.save(
                    dst,
                    format="JPEG",
                    quality=quality,
                    optimize=True,
                    exif=b"",  # strip EXIF to avoid leaking metadata
                )
                size = dst.stat().st_size
                if size <= bytes_limit or quality <= MIN_JPEG_QUALITY:
                    stats["final_size"] = size
                    break
                quality -= QUALITY_STEP
    else:
        size = src.stat().st_size
        if size > bytes_limit:
            raise ValueError("file exceeds size limit and cannot be compressed")
        stats["final_size"] = size
    return dst, stats


__all__ = ["fit_to_limit"]
