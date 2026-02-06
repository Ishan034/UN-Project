"""
Tile tensor stacker (PyTorch) — ROBUST VERSION
--------------------------------------------
This version FIXES raster misalignment by explicitly reprojecting
Rainfall onto the NDVI grid before stacking.

Pipeline:
1. Load NDVI raster (reference grid)
2. Load Rainfall raster
3. Reproject Rainfall -> NDVI grid if needed
4. Extract [NDVI, Rainfall] tiles (64×64)
5. Save each tile as a PyTorch tensor [2, 64, 64]

This is production-safe and expected in real geospatial ML.
"""

from pathlib import Path
import torch
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling

# =========================
# PATH RESOLUTION
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# =========================
# CONFIG
# =========================
TILE_SIZE = 64  # pixels (1 km per pixel)
TARGET_CRS = "EPSG:3857"

NDVI_PATH = PROJECT_ROOT / "data/processed/ndvi_1km.tif"
RAIN_PATH = PROJECT_ROOT / "data/processed/rainfall_30d_1km.tif"
BOUNDARY_PATH = PROJECT_ROOT / "data/boundaries/south_sudan.shp"
OUTPUT_DIR = PROJECT_ROOT / "data/tensors"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# =========================
# HELPERS
# =========================

def reproject_to_match(src, ref_src):
    """Reproject src raster onto ref_src grid."""
    destination = np.zeros(
        (ref_src.height, ref_src.width), dtype=np.float32
    )

    reproject(
        source=rasterio.band(src, 1),
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=ref_src.transform,
        dst_crs=ref_src.crs,
        resampling=Resampling.average,
    )

    return destination


def world_to_pixel(src, x, y):
    return src.index(x, y)


# =========================
# MAIN STACKING LOGIC
# =========================

def stack_tiles():
    print("Loading rasters...")

    with rasterio.open(NDVI_PATH) as ndvi_src, rasterio.open(RAIN_PATH) as rain_src:
        print("NDVI grid:", ndvi_src.transform)
        print("Rain grid:", rain_src.transform)

        # 🔑 FIX: Force rainfall onto NDVI grid
        if ndvi_src.transform != rain_src.transform or ndvi_src.crs != rain_src.crs:
            print("Reprojecting rainfall to match NDVI grid...")
            rainfall_data = reproject_to_match(rain_src, ndvi_src)
        else:
            rainfall_data = rain_src.read(1).astype(np.float32)

        ndvi_data = ndvi_src.read(1).astype(np.float32)

        boundary = gpd.read_file(BOUNDARY_PATH, engine="fiona").to_crs(TARGET_CRS)
        minx, miny, maxx, maxy = boundary.total_bounds

        transform = ndvi_src.transform
        pixel_size = transform.a

        tile_id = 0

        x_coords = np.arange(minx, maxx, TILE_SIZE * pixel_size)
        y_coords = np.arange(miny, maxy, TILE_SIZE * pixel_size)

        for x in x_coords:
            for y in y_coords:
                row, col = world_to_pixel(ndvi_src, x, y)

                window = Window(col, row, TILE_SIZE, TILE_SIZE)

                try:
                    ndvi_patch = ndvi_data[row:row+TILE_SIZE, col:col+TILE_SIZE]
                    rain_patch = rainfall_data[row:row+TILE_SIZE, col:col+TILE_SIZE]
                except Exception:
                    continue

                if ndvi_patch.shape != (TILE_SIZE, TILE_SIZE):
                    continue

                tensor = torch.tensor(
                    np.stack([ndvi_patch, rain_patch]), dtype=torch.float32
                )

                torch.save(tensor, OUTPUT_DIR / f"tile_{tile_id}.pt")
                tile_id += 1

        print(f"Saved {tile_id} tile tensors")


if __name__ == "__main__":
    stack_tiles()
