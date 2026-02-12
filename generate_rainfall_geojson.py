from pathlib import Path
import rasterio
import json
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
RAIN_PATH = PROJECT_ROOT / "data" / "processed" / "rainfall_30d_1km.tif"
OUT_PATH = PROJECT_ROOT / "data" / "predictions" / "rainfall_heatmap.geojson"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

features = []

print("Loading rainfall raster...")

with rasterio.open(RAIN_PATH) as src:
    data = src.read(1)

    height, width = data.shape

    for row in range(0, height, 5):
        for col in range(0, width, 5):
            value = float(data[row, col])

            if np.isnan(value):
                continue

            x, y = src.xy(row, col)

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [x, y]
                },
                "properties": {
                    "rain": value
                }
            })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open(OUT_PATH, "w") as f:
    json.dump(geojson, f)

print(f"Rainfall heatmap created with {len(features)} points.")
