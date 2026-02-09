"""
Raster → GeoJSON conversion (V2 – CORRIDOR-AWARE)
-----------------------------------------------
Converts migration pressure raster into source/destination zones
using CONNECTED PIXEL CLUSTERS instead of area-based filtering.

This is correct for pastoral migration:
- Allows thin corridors
- Allows fragmented but coherent zones
- Avoids whole-country false positives
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
# CONFIG (V2 FINAL)
# =========================
LOW_PERCENTILE = 25
HIGH_PERCENTILE = 75
MIN_PRESSURE_SPREAD = 0.005
MIN_PIXELS = 6   # connected pixels, NOT area

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
    # SIGNAL CHECK
    # -------------------------
    pressure_min = float(np.min(data))
    pressure_max = float(np.max(data))
    pressure_range = pressure_max - pressure_min

    print(f"Pressure range: {pressure_range:.6f}")

    if pressure_range < MIN_PRESSURE_SPREAD:
        print("Pressure field too uniform → no significant migration signal")

        empty_gdf = gpd.GeoDataFrame(
            columns=["geometry", "type", "pressure"],
            geometry="geometry",
            crs="EPSG:4326",
        )
        empty_gdf.to_file(OUT_GEOJSON, driver="GeoJSON")
        print(f"Empty GeoJSON written to {OUT_GEOJSON}")
        return

    # -------------------------
    # ADAPTIVE THRESHOLDS
    # -------------------------
    neg_thr = np.percentile(data, LOW_PERCENTILE)
    pos_thr = np.percentile(data, HIGH_PERCENTILE)

    print(f"Thresholds → source ≤ {neg_thr:.4f}, destination ≥ {pos_thr:.4f}")

    source_mask = data <= neg_thr
    dest_mask = data >= pos_thr

    features = []

    # -------------------------
    # SOURCE ZONES
    # -------------------------
    print("Extracting source zones...")
    for geom, val in shapes(data, mask=source_mask, transform=transform):
        geom_shape = shape(geom)

        # Connected pixel count (not area!)
        pixel_count = int(geom_shape.area / abs(transform.a * transform.e))

        if pixel_count < MIN_PIXELS:
            continue

        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "source",
        })

    # -------------------------
    # DESTINATION ZONES
    # -------------------------
    print("Extracting destination zones...")
    for geom, val in shapes(data, mask=dest_mask, transform=transform):
        geom_shape = shape(geom)

        pixel_count = int(geom_shape.area / abs(transform.a * transform.e))

        if pixel_count < MIN_PIXELS:
            continue

        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "destination",
        })

    # -------------------------
    # EMPTY CHECK
    # -------------------------
    if not features:
        print("No valid regions after filtering → writing empty GeoJSON")

        empty_gdf = gpd.GeoDataFrame(
            columns=["geometry", "type", "pressure"],
            geometry="geometry",
            crs="EPSG:4326",
        )
        empty_gdf.to_file(OUT_GEOJSON, driver="GeoJSON")
        return

    gdf = gpd.GeoDataFrame(features, geometry="geometry", crs=crs)

    # Reproject for Mapbox
    gdf = gdf.to_crs(epsg=4326)

    # -------------------------
    # CLIP TO BOUNDARY ONLY
    # -------------------------
    boundary = gpd.read_file(BOUNDARY_PATH, engine="fiona").to_crs(epsg=4326)
    gdf = gpd.clip(gdf, boundary)

    # -------------------------
    # SAVE
    # -------------------------
    gdf[["geometry", "type", "pressure"]].to_file(
        OUT_GEOJSON, driver="GeoJSON"
    )

    print(f"GeoJSON written to {OUT_GEOJSON}")
    print(f"Zones written: {len(gdf)}")


if __name__ == "__main__":
    raster_to_geojson()
