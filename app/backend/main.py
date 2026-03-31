from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from datetime import datetime
import math

app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
CONFLICT_FILE = PRED_DIR / "conflict_heatmap.geojson"

# =========================
# TEMPORAL MEMORY (simple)
# =========================
previous_confidence = None

# =========================
# HELPERS
# =========================
def empty_geojson():
    return {
        "type": "FeatureCollection",
        "features": []
    }

def safe_file_response(file_path):
    if not file_path.exists():
        return empty_geojson()
    return FileResponse(file_path, media_type="application/geo+json")

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "ok"}

# =========================
# PREDICT (FINAL)
# =========================
@app.get("/predict")
def predict():
    global previous_confidence

    if not ZONES_FILE.exists():
        return {
            "status": "ok",
            "confidence": 0.0,
            "lead_time_days": 0,
            "risk_level": "LOW",
            "affected_score": 0,
            "zones": empty_geojson(),
        }

    with open(ZONES_FILE) as f:
        zones = json.load(f)

    features = zones.get("features", [])

    pressures = [abs(f["properties"].get("pressure", 0)) for f in features]

    if len(pressures) == 0:
        avg_pressure = 0
        total_pressure = 0
        max_p = 0
        std_p = 0
        top_mean = 0
    else:
        avg_pressure = sum(pressures) / len(pressures)
        total_pressure = sum(pressures)
        max_p = max(pressures)

        # =========================
        # Variance
        # =========================
        variance = sum((p - avg_pressure) ** 2 for p in pressures) / len(pressures)
        std_p = math.sqrt(variance)

        # =========================
        # Top 20% signal
        # =========================
        sorted_p = sorted(pressures, reverse=True)
        k = max(1, int(0.2 * len(sorted_p)))
        top_k = sorted_p[:k]
        top_mean = sum(top_k) / len(top_k)

    # =========================
    # RAW CONFIDENCE (STRUCTURAL)
    # =========================
    raw_confidence = (
        0.5 * max_p +
        0.3 * top_mean +
        0.2 * (1 / (1 + std_p))
    )

    # =========================
    # CALIBRATION (CRITICAL)
    # =========================
    # Sigmoid-like squashing → makes values meaningful
    calibrated = 1 / (1 + math.exp(-5 * (raw_confidence - 0.2)))

    # =========================
    # TEMPORAL SMOOTHING
    # =========================
    if previous_confidence is not None:
        calibrated = 0.7 * calibrated + 0.3 * previous_confidence

    previous_confidence = calibrated

    confidence = round(min(calibrated, 1), 3)

    # =========================
    # LEAD TIME
    # =========================
    lead_time = int(7 + avg_pressure * 14)

    # =========================
    # RISK LEVEL
    # =========================
    if total_pressure > 50:
        risk = "CRITICAL"
    elif total_pressure > 25:
        risk = "HIGH"
    elif total_pressure > 10:
        risk = "MODERATE"
    else:
        risk = "LOW"

    return {
        "status": "ok",
        "confidence": confidence,
        "lead_time_days": lead_time,
        "risk_level": risk,
        "affected_score": round(total_pressure, 2),
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "zones": zones,
    }

# =========================
# DATA ENDPOINTS
# =========================
@app.get("/heatmap")
def heatmap():
    return safe_file_response(HEATMAP_FILE)

@app.get("/ndvi")
def ndvi():
    return safe_file_response(NDVI_FILE)

@app.get("/rainfall")
def rainfall():
    return safe_file_response(RAIN_FILE)

@app.get("/conflict")
def conflict():
    return safe_file_response(CONFLICT_FILE)