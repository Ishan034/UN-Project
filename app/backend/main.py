from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import json
from datetime import datetime

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent.parent
PRED_DIR = BASE_DIR / "data" / "predictions"

ZONES_FILE = PRED_DIR / "migration_zones.geojson"
HEATMAP_FILE = PRED_DIR / "migration_heatmap.geojson"


@app.get("/")
def root():
    return {"status": "ok"}


# -------------------------
# EXISTING PREDICT ENDPOINT
# -------------------------
@app.get("/predict")
def predict():
    if not ZONES_FILE.exists():
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "confidence": 0.0,
                "lead_time_days": 21,
                "zones": {
                    "type": "FeatureCollection",
                    "features": [],
                },
            },
        )

    with open(ZONES_FILE) as f:
        zones = json.load(f)

    return {
        "status": "ok",
        "confidence": 0.95,
        "lead_time_days": 21,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "zones": zones,
    }


# -------------------------
# 🔥 NEW HEATMAP ENDPOINT
# -------------------------
@app.get("/heatmap")
def heatmap():
    if not HEATMAP_FILE.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Heatmap not available"},
        )

    return FileResponse(
        HEATMAP_FILE,
        media_type="application/geo+json",
        filename="migration_heatmap.geojson",
    )
