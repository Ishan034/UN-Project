from pathlib import Path
import rasterio
import json
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
NDVI_PATH = PROJECT_ROOT / "data/processed/ndvi_delta_1km.tif"
OUT_PATH = PROJECT_ROOT / "data/predictions/ndvi_heatmap.geojson"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

features = []

with rasterio.open(NDVI_PATH) as src:
    data = src.read(1)

    for row in range(0, data.shape[0], 5):
        for col in range(0, data.shape[1], 5):
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
                    "ndvi": value
                }
            })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open(OUT_PATH, "w") as f:
    json.dump(geojson, f)

print("NDVI heatmap file created.")
