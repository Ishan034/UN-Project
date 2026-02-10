from pathlib import Path
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parent
PRESSURE_RASTER = PROJECT_ROOT / "data/predictions/migration_pressure.tif"
OUT_FILE = PROJECT_ROOT / "data/predictions/migration_heatmap.geojson"

SAMPLE_STRIDE = 3  # every 3 km → adjustable

features = []

with rasterio.open(PRESSURE_RASTER) as src:
    data = src.read(1)
    transform = src.transform
    crs = src.crs

    for row in range(0, src.height, SAMPLE_STRIDE):
        for col in range(0, src.width, SAMPLE_STRIDE):
            val = data[row, col]
            if np.isnan(val):
                continue

            x, y = rasterio.transform.xy(transform, row, col)
            features.append({
                "geometry": Point(x, y),
                "pressure": float(val),
            })

gdf = gpd.GeoDataFrame(features, geometry="geometry", crs=crs)
gdf = gdf.to_crs(epsg=4326)
gdf.to_file(OUT_FILE, driver="GeoJSON")

print(f"Heatmap GeoJSON written to {OUT_FILE}")
