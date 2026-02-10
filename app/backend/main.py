from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime

app = FastAPI()

# =========================
# 🔓 ENABLE CORS (CRITICAL)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",        # local React
        "https://un-project-4ajo.onrender.com",  # deployed frontend (if any)
        "*"                             # safe for demo / UN prototype
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parent.parent
PRED_DIR = BASE_DIR / "data" / "predictions"

ZONES_FILE = PRED_DIR / "migration_zones.geojson"
HEATMAP_FILE = PRED_DIR / "migration_heatmap.geojson"


@app.get("/")
def root():
    return {"status": "ok"}


# =========================
# PREDICTION METADATA
# =========================
@app.get("/predict")
def predict():
    if not ZONES_FILE.exists():
        return {
            "status": "ok",
            "confidence": 0.0,
            "lead_time_days": 21,
            "zones": {
                "type": "FeatureCollection",
                "features": [],
            },
        }

    with open(ZONES_FILE) as f:
        zones = json.load(f)

    return {
        "status": "ok",
        "confidence": 0.95,
        "lead_time_days": 21,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "zones": zones,
    }


# =========================
# 🔥 HEATMAP ENDPOINT
# =========================
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
