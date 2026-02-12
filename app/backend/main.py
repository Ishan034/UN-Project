from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime

app = FastAPI()

# =========================
# 🔓 ENABLE CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Safe for demo / UN prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).resolve().parents[2]
PRED_DIR = BASE_DIR / "data" / "predictions"

ZONES_FILE = PRED_DIR / "migration_zones.geojson"
HEATMAP_FILE = PRED_DIR / "migration_heatmap.geojson"
NDVI_FILE = PRED_DIR / "ndvi_heatmap.geojson"
RAIN_FILE = PRED_DIR / "rainfall_heatmap.geojson"


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
# 🔥 MIGRATION HEATMAP
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


# =========================
# 🌱 NDVI LAYER
# =========================
@app.get("/ndvi")
def ndvi():
    if not NDVI_FILE.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "NDVI not available"},
        )

    return FileResponse(
        NDVI_FILE,
        media_type="application/geo+json",
        filename="ndvi_heatmap.geojson",
    )


# =========================
# 🌧 RAINFALL LAYER
# =========================
@app.get("/rainfall")
def rainfall():
    if not RAIN_FILE.exists():
        return JSONResponse(
            status_code=404,
            content={"error": "Rainfall not available"},
        )

    return FileResponse(
        RAIN_FILE,
        media_type="application/geo+json",
        filename="rainfall_heatmap.geojson",
    )
