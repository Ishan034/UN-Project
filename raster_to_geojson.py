"""
Raster → GeoJSON conversion (V1 – ADAPTIVE)
----------------------------------------
Converts migration pressure raster into meaningful zones using
ADAPTIVE thresholds derived from the data distribution.

This avoids empty outputs when pressure magnitudes are small
(which is normal for NDVI-change models).
"""

from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
from rasterio.features import shapes
from shapely.geometry import shape

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent

PRESSURE_RASTER = PROJECT_ROOT / "data/predictions/migration_pressure.tif"
BOUNDARY_PATH = PROJECT_ROOT / "data/boundaries/south_sudan.shp"

OUT_DIR = PROJECT_ROOT / "data/predictions"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_GEOJSON = OUT_DIR / "migration_zones.geojson"

# =========================
# CONFIG
# =========================
LOW_PERCENTILE = 15   # bottom 15% → source
HIGH_PERCENTILE = 85  # top 15% → destination

MIN_PIXELS = 25       # remove tiny noisy regions

# =========================
# MAIN
# =========================

def raster_to_geojson():
    print("Loading pressure raster...")

    with rasterio.open(PRESSURE_RASTER) as src:
        data = src.read(1)
        transform = src.transform
        crs = src.crs

    data = np.nan_to_num(data, nan=0.0)

    # -------------------------
    # ADAPTIVE THRESHOLDS
    # -------------------------
    neg_thr = np.percentile(data, LOW_PERCENTILE)
    pos_thr = np.percentile(data, HIGH_PERCENTILE)

    print(f"Adaptive thresholds → source ≤ {neg_thr:.4f}, destination ≥ {pos_thr:.4f}")

    source_mask = data <= neg_thr
    dest_mask = data >= pos_thr

    features = []

    print("Extracting source zones...")
    for geom, val in shapes(data, mask=source_mask, transform=transform):
        geom_shape = shape(geom)
        if geom_shape.area < MIN_PIXELS:
            continue
        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "source"
        })

    print("Extracting destination zones...")
    for geom, val in shapes(data, mask=dest_mask, transform=transform):
        geom_shape = shape(geom)
        if geom_shape.area < MIN_PIXELS:
            continue
        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "destination"
        })

    if not features:
        raise RuntimeError("Still no zones extracted — pressure field may be uniform")

    gdf = gpd.GeoDataFrame(features, geometry="geometry", crs=crs)

    # Clip to country boundary
    boundary = gpd.read_file(BOUNDARY_PATH, engine="fiona").to_crs(crs)
    gdf = gpd.clip(gdf, boundary)

    gdf.to_file(OUT_GEOJSON, driver="GeoJSON")
    print(f"GeoJSON written to {OUT_GEOJSON}")

    summary = {
        "source_zones": int((gdf['type'] == 'source').sum()),
        "destination_zones": int((gdf['type'] == 'destination').sum()),
        "min_pressure": float(np.min(data)),
        "max_pressure": float(np.max(data)),
        "low_threshold": float(neg_thr),
        "high_threshold": float(pos_thr)
    }

    print("Summary:", summary)
    return summary


if __name__ == "__main__":
    raster_to_geojson()
