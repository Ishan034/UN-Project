from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from datetime import datetime
import geopandas as gpd
import json

app = FastAPI()

# =========================
# CORS (required)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS_DIR = PROJECT_ROOT / "data" / "predictions"
ZONES_FILE = PREDICTIONS_DIR / "migration_zones.geojson"

LEAD_TIME_DAYS = 21

# =========================
# PREDICT ENDPOINT
# =========================
@app.api_route("/predict", methods=["GET", "POST"])
def predict():
    if not ZONES_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No prediction available. Run offline inference first."
        )

    # 🔑 Load with GeoPandas
    gdf = gpd.read_file(ZONES_FILE)

    # 🔑 CRITICAL FIX: reproject to WGS84 (lat/lon)
    gdf = gdf.to_crs(epsg=4326)

    # Convert to GeoJSON dict
    zones_geojson = json.loads(gdf.to_json())

    features = zones_geojson.get("features", [])

    source_zones = sum(
        1 for f in features if f["properties"].get("type") == "source"
    )
    destination_zones = sum(
        1 for f in features if f["properties"].get("type") == "destination"
    )

    # Simple confidence heuristic
    confidence = min(0.95, 0.5 + 0.05 * (source_zones + destination_zones))

    return {
        "status": "ok",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "lead_time_days": LEAD_TIME_DAYS,
        "confidence": round(confidence, 2),
        "zones": zones_geojson,
    }
