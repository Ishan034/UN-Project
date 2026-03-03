from pathlib import Path
import json
import numpy as np
import rasterio

PROJECT_ROOT = Path(__file__).resolve().parent
ACLED_PATH = PROJECT_ROOT / "data/processed/acled_events_90d_1km.tif"
OUT_PATH = PROJECT_ROOT / "data/predictions/acled_heatmap.geojson"

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

if not ACLED_PATH.exists():
    raise FileNotFoundError(
        f"ACLED raster not found at {ACLED_PATH}. Run preprocessing/acled.py first."
    )

features = []

with rasterio.open(ACLED_PATH) as src:
    data = src.read(1)
    height, width = data.shape

    for row in range(0, height, 5):
        for col in range(0, width, 5):
            value = float(data[row, col])
            if np.isnan(value) or value <= 0:
                continue

            x, y = src.xy(row, col)
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [x, y]},
                    "properties": {"acled": value},
                }
            )

geojson = {"type": "FeatureCollection", "features": features}

with open(OUT_PATH, "w") as f:
    json.dump(geojson, f)

print(f"ACLED heatmap created with {len(features)} points at {OUT_PATH}")
