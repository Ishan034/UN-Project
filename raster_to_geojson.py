"""
Raster → GeoJSON conversion (V2 – SIGNAL-AWARE)
---------------------------------------------
Converts migration pressure raster into source/destination zones
ONLY when a meaningful spatial signal exists.

Key improvements:
- Suppresses whole-country false positives
- Handles near-uniform pressure fields honestly
- Outputs EMPTY GeoJSON when no significant migration pressure is detected

This is UN-grade early-warning behavior.
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
# CONFIG (SIGNAL GUARDS)
# =========================
LOW_PERCENTILE = 15     # bottom 15% → source
HIGH_PERCENTILE = 85    # top 15% → destination

MIN_PRESSURE_SPREAD = 0.01   # suppress if signal too weak
MAX_AREA_RATIO = 0.3         # suppress giant blobs (>30% of country)
MIN_PIXELS = 25              # remove tiny noise regions

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

        # Write EMPTY GeoJSON (valid but no zones)
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

    print("Extracting source zones...")
    for geom, val in shapes(data, mask=source_mask, transform=transform):
        geom_shape = shape(geom)
        if geom_shape.area < MIN_PIXELS:
            continue
        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "source",
        })

    print("Extracting destination zones...")
    for geom, val in shapes(data, mask=dest_mask, transform=transform):
        geom_shape = shape(geom)
        if geom_shape.area < MIN_PIXELS:
            continue
        features.append({
            "geometry": geom_shape,
            "pressure": float(val),
            "type": "destination",
        })

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

    # Reproject to WGS84 for Mapbox
    gdf = gdf.to_crs(epsg=4326)

    # -------------------------
    # CLIP + AREA FILTER
    # -------------------------
    boundary = gpd.read_file(BOUNDARY_PATH, engine="fiona").to_crs(epsg=4326)
    gdf = gpd.clip(gdf, boundary)

    country_area = boundary.geometry.area.sum()
    gdf["area_ratio"] = gdf.geometry.area / country_area
    gdf = gdf[gdf["area_ratio"] < MAX_AREA_RATIO]

    if gdf.empty:
        print("All regions filtered out → writing empty GeoJSON")
        gdf = gpd.GeoDataFrame(
            columns=["geometry", "type", "pressure"],
            geometry="geometry",
            crs="EPSG:4326",
        )

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