"""
Rainfall preprocessing pipeline (SIMPLIFIED V1)
---------------------------------------------
Assumes rainfall is already aggregated (e.g. 30-day sum)
and exported from Google Earth Engine as a single GeoTIFF.
"""

from pathlib import Path

import geopandas as gpd
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask

# =========================
# PATH RESOLUTION
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# =========================
# CONFIG
# =========================
TARGET_CRS = "EPSG:3857"
TARGET_RESOLUTION = 1000  # meters (1 km)

# =========================
# CORE FUNCTIONS
# =========================
def reproject_and_resample(src, data: np.ndarray):
    transform = rasterio.transform.from_origin(
        src.bounds.left,
        src.bounds.top,
        TARGET_RESOLUTION,
        TARGET_RESOLUTION,
    )

    width = int((src.bounds.right - src.bounds.left) / TARGET_RESOLUTION)
    height = int((src.bounds.top - src.bounds.bottom) / TARGET_RESOLUTION)

    destination = np.zeros((height, width), dtype=np.float32)

    reproject(
        source=data,
        destination=destination,
        src_transform=src.transform,
        src_crs=src.crs,
        dst_transform=transform,
        dst_crs=TARGET_CRS,
        resampling=Resampling.average,
    )

    return destination, transform


def clip_to_boundary(raster: np.ndarray, transform, boundary: gpd.GeoDataFrame):
    shapes = boundary.geometry.values

    with rasterio.io.MemoryFile() as memfile:
        with memfile.open(
            driver="GTiff",
            height=raster.shape[0],
            width=raster.shape[1],
            count=1,
            dtype=raster.dtype,
            crs=TARGET_CRS,
            transform=transform,
        ) as dataset:
            dataset.write(raster, 1)
            clipped, clipped_transform = mask(dataset, shapes, crop=True)

    return clipped[0], clipped_transform


def normalize_rainfall(rainfall: np.ndarray) -> np.ndarray:
    p2, p98 = np.percentile(rainfall, [2, 98])
    rainfall = np.clip(rainfall, p2, p98)
    return (rainfall - p2) / (p98 - p2 + 1e-6)

# =========================
# MAIN PIPELINE
# =========================
def process_rainfall(rainfall_file: Path, boundary_shapefile: Path, output_path: Path):
    print("Boundary path:", boundary_shapefile)
    print("Boundary exists:", boundary_shapefile.exists())
    print("Rainfall file:", rainfall_file)
    print("Rainfall exists:", rainfall_file.exists())

    boundary = gpd.read_file(boundary_shapefile, engine="fiona").to_crs(TARGET_CRS)

    with rasterio.open(rainfall_file) as src:
        rainfall = src.read(1).astype(np.float32)

        rainfall_resampled, transform = reproject_and_resample(src, rainfall)
        rainfall_clipped, clipped_transform = clip_to_boundary(
            rainfall_resampled, transform, boundary
        )

    rainfall_normalized = normalize_rainfall(rainfall_clipped)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=rainfall_normalized.shape[0],
        width=rainfall_normalized.shape[1],
        count=1,
        dtype="float32",
        crs=TARGET_CRS,
        transform=clipped_transform,
    ) as dst:
        dst.write(rainfall_normalized, 1)

    print(f"Rainfall written to {output_path}")

# =========================
# ENTRYPOINT
# =========================
if __name__ == "__main__":
    process_rainfall(
        rainfall_file=PROJECT_ROOT / "data/chirps/SouthSudan_Rainfall_30d.tif",
        boundary_shapefile=PROJECT_ROOT / "data/boundaries/south_sudan.shp",
        output_path=PROJECT_ROOT / "data/processed/rainfall_30d_1km.tif",
    )
