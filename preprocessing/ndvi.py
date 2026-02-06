"""
NDVI preprocessing pipeline
---------------------------
This script:
1. Loads Sentinel-2 imagery (Red + NIR bands)
2. Computes NDVI
3. Reprojects to EPSG:3857
4. Resamples to 1 km resolution
5. Clips to South Sudan boundary
6. Outputs NDVI raster aligned with the 1 km grid

This is V1: simple, robust, UN-grade (not overengineered).
"""

import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
from pathlib import Path

TARGET_CRS = "EPSG:3857"
TARGET_RESOLUTION = 1000  # meters (1 km)


def load_band(band_path: str):
    """Load a single Sentinel-2 band."""
    return rasterio.open(band_path)


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """Compute NDVI with numerical stability."""
    ndvi = (nir - red) / (nir + red + 1e-6)
    return np.clip(ndvi, -1.0, 1.0)


def reproject_and_resample(src, data: np.ndarray):
    """Reproject raster to EPSG:3857 and resample to 1 km."""
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
    """Clip raster to country boundary."""
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


def normalize_ndvi(ndvi: np.ndarray) -> np.ndarray:
    """Normalize NDVI from [-1, 1] to [0, 1]."""
    return (ndvi + 1.0) / 2.0


def process_ndvi(
    red_band_path: str,
    nir_band_path: str,
    boundary_shapefile: str,
    output_path: str,
):
    """
    Full NDVI preprocessing pipeline.
    """
    boundary = gpd.read_file(boundary_shapefile, engine="fiona").to_crs(TARGET_CRS)


    red_src = load_band(red_band_path)
    nir_src = load_band(nir_band_path)

    red = red_src.read(1).astype(np.float32)
    nir = nir_src.read(1).astype(np.float32)

    ndvi = compute_ndvi(red, nir)

    ndvi_resampled, transform = reproject_and_resample(red_src, ndvi)

    ndvi_clipped, clipped_transform = clip_to_boundary(
        ndvi_resampled, transform, boundary
    )

    ndvi_normalized = normalize_ndvi(ndvi_clipped)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=ndvi_normalized.shape[0],
        width=ndvi_normalized.shape[1],
        count=1,
        dtype="float32",
        crs=TARGET_CRS,
        transform=clipped_transform,
    ) as dst:
        dst.write(ndvi_normalized, 1)

    print(f"NDVI written to {output_path}")


if __name__ == "__main__":
    # Example usage
    process_ndvi(
        red_band_path="data/sentinel2/B04.tif",
        nir_band_path="data/sentinel2/B08.tif",
        boundary_shapefile="data/boundaries/south_sudan.shp",
        output_path="data/processed/ndvi_1km.tif",
    )
