from pathlib import Path
import rasterio
from rasterio.warp import reproject, Resampling
import numpy as np

# Correct project root
PROJECT_ROOT = Path(__file__).resolve().parent

NDVI_PATH = PROJECT_ROOT / "data" / "processed" / "ndvi_delta_1km.tif"
RAIN_ORIG = PROJECT_ROOT / "data" / "chirps" / "SouthSudan_Rainfall_30d.tif"
RAIN_OUT = PROJECT_ROOT / "data" / "processed" / "rainfall_30d_1km.tif"

print("Loading NDVI grid (reference)...")

with rasterio.open(NDVI_PATH) as ndvi_src:
    ndvi_profile = ndvi_src.profile
    ndvi_height = ndvi_src.height
    ndvi_width = ndvi_src.width
    ndvi_transform = ndvi_src.transform
    ndvi_crs = ndvi_src.crs

print("Reprojecting rainfall to NDVI grid...")

with rasterio.open(RAIN_ORIG) as rain_src:

    rainfall_data = np.zeros(
        (ndvi_height, ndvi_width),
        dtype=np.float32
    )

    reproject(
        source=rasterio.band(rain_src, 1),
        destination=rainfall_data,
        src_transform=rain_src.transform,
        src_crs=rain_src.crs,
        dst_transform=ndvi_transform,
        dst_crs=ndvi_crs,
        resampling=Resampling.bilinear,
    )

    rainfall_data = np.nan_to_num(rainfall_data, nan=0.0)

    ndvi_profile.update(
        dtype=rasterio.float32,
        count=1
    )

    with rasterio.open(RAIN_OUT, "w", **ndvi_profile) as dst:
        dst.write(rainfall_data, 1)

print("Rainfall successfully aligned and saved.")
