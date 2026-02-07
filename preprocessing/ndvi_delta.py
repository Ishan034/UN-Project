"""
Compute temporal NDVI difference (ΔNDVI)
NDVI_delta = NDVI_current - NDVI_previous
"""

from pathlib import Path
import rasterio
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]

NDVI_CURR = PROJECT_ROOT / "data/processed/ndvi_1km_current.tif"
NDVI_PREV = PROJECT_ROOT / "data/processed/ndvi_1km_previous.tif"
OUT_DELTA = PROJECT_ROOT / "data/processed/ndvi_delta_1km.tif"

with rasterio.open(NDVI_CURR) as curr, rasterio.open(NDVI_PREV) as prev:
    delta = curr.read(1) - prev.read(1)

    meta = curr.meta.copy()
    meta.update(dtype="float32")

    with rasterio.open(OUT_DELTA, "w", **meta) as dst:
        dst.write(delta.astype("float32"), 1)

print("ΔNDVI written to:", OUT_DELTA)
