from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime

app = FastAPI()

# ✅ CORS (required)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PREDICTIONS_DIR = PROJECT_ROOT / "data/predictions"
ZONES_FILE = PREDICTIONS_DIR / "migration_zones.geojson"

LEAD_TIME_DAYS = 21

# ✅ Accept BOTH GET and POST
@app.api_route("/predict", methods=["GET", "POST"])
def predict():
    if not ZONES_FILE.exists():
        raise HTTPException(
            status_code=404,
            detail="No prediction available. Run offline inference first."
        )

    with open(ZONES_FILE, "r", encoding="utf-8") as f:
        zones_geojson = json.load(f)

    features = zones_geojson.get("features", [])

    source_zones = sum(
        1 for f in features if f["properties"]["type"] == "source"
    )
    destination_zones = sum(
        1 for f in features if f["properties"]["type"] == "destination"
    )

    confidence = min(0.95, 0.5 + 0.05 * (source_zones + destination_zones))

    return {
        "status": "ok",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "lead_time_days": LEAD_TIME_DAYS,
        "confidence": round(confidence, 2),
        "zones": zones_geojson,
    }
