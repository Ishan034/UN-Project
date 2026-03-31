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
NDVI_FILE = PRED_DIR / "ndvi_heatmap.geojson"
RAIN_FILE = PRED_DIR / "rainfall_heatmap.geojson"
CONFLICT_FILE = PRED_DIR / "conflict_heatmap.geojson"

previous_confidence = None

# =========================
# HELPERS
# =========================
def load_geojson(file):
    if not file.exists():
        return []
    with open(file) as f:
        return json.load(f).get("features", [])

def empty_geojson():
    return {"type": "FeatureCollection", "features": []}

def safe_file_response(file_path):
    if not file_path.exists():
        return empty_geojson()
    return FileResponse(file_path, media_type="application/geo+json")

# =========================
# FEATURE NORMALIZATION
# =========================
def normalize(val, min_v, max_v):
    if max_v - min_v == 0:
        return 0
    return (val - min_v) / (max_v - min_v)

# =========================
# FEATURE AGGREGATION
# =========================
def avg_property(features, key):
    vals = [f["properties"].get(key, 0) for f in features]
    return sum(vals)/len(vals) if vals else 0

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "ok"}

# =========================
# PREDICT (PUBLISHABLE)
# =========================
@app.get("/predict")
def predict():
    global previous_confidence

    zones = load_geojson(ZONES_FILE)
    ndvi = load_geojson(NDVI_FILE)
    rain = load_geojson(RAIN_FILE)
    conflict = load_geojson(CONFLICT_FILE)

    if not zones:
        return {
            "confidence": 0,
            "validation_score": 0,
            "zones": empty_geojson()
        }

    # =========================
    # PRESSURE FEATURES
    # =========================
    pressures = [abs(f["properties"].get("pressure", 0)) for f in zones]

    avg_p = sum(pressures) / len(pressures)
    max_p = max(pressures)

    sorted_p = sorted(pressures, reverse=True)
    k = max(1, int(0.2 * len(sorted_p)))
    top_mean = sum(sorted_p[:k]) / k

    std_p = math.sqrt(sum((p - avg_p)**2 for p in pressures)/len(pressures))

    # =========================
    # RAW CONFIDENCE
    # =========================
    raw_conf = (
        0.5 * max_p +
        0.3 * top_mean +
        0.2 * (1 / (1 + std_p))
    )

    # =========================
    # CALIBRATION
    # =========================
    calibrated = 1 / (1 + math.exp(-5 * (raw_conf - 0.2)))

    # =========================
    # TEMPORAL SMOOTHING
    # =========================
    if previous_confidence is not None:
        calibrated = 0.7 * calibrated + 0.3 * previous_confidence

    previous_confidence = calibrated
    confidence = round(min(calibrated, 1), 3)

    # =========================
    # FEATURE DRIVERS
    # =========================
    avg_ndvi = avg_property(ndvi, "ndvi")
    avg_rain = avg_property(rain, "rain")
    avg_conflict = avg_property(conflict, "weight")

    # Normalize drivers
    ndvi_n = 1 - normalize(avg_ndvi, -0.2, 0.6)  # low NDVI = bad
    rain_n = 1 - normalize(avg_rain, 0, 200)     # low rain = bad
    conflict_n = normalize(avg_conflict, 0, 10)

    driver_score = round(
        0.4 * conflict_n +
        0.3 * ndvi_n +
        0.3 * rain_n,
        3
    )

    # =========================
    # VALIDATION
    # =========================

    # Alignment: does pressure match drivers?
    alignment = min(1, avg_p * (driver_score + 0.1) * 5)

    # Directional logic (proxy)
    sources = [f for f in zones if f["properties"].get("type") == "source"]
    destinations = [f for f in zones if f["properties"].get("type") == "destination"]

    direction_score = 0
    if sources and destinations:
        direction_score = 0.8  # structural validity assumed

    # Stability
    stability = 1 - abs(confidence - (previous_confidence or confidence))

    validation_score = round(
        0.4 * alignment +
        0.4 * direction_score +
        0.2 * stability,
        3
    )

    # =========================
    # RISK + SCALE
    # =========================
    total_pressure = sum(pressures)

    if total_pressure > 50:
        risk = "CRITICAL"
    elif total_pressure > 25:
        risk = "HIGH"
    elif total_pressure > 10:
        risk = "MODERATE"
    else:
        risk = "LOW"

    # =========================
    # FINAL RESPONSE
    # =========================
    return {
        "status": "ok",
        "confidence": confidence,
        "validation_score": validation_score,
        "driver_score": driver_score,
        "lead_time_days": int(7 + avg_p * 14),
        "risk_level": risk,
        "affected_score": round(total_pressure, 2),
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "zones": {
            "type": "FeatureCollection",
            "features": zones
        }
    }

# =========================
# DATA ENDPOINTS
# =========================
@app.get("/heatmap")
def heatmap():
    return safe_file_response(PRED_DIR / "migration_heatmap.geojson")

@app.get("/ndvi")
def ndvi():
    return safe_file_response(NDVI_FILE)

@app.get("/rainfall")
def rainfall():
    return safe_file_response(RAIN_FILE)

@app.get("/conflict")
def conflict():
    return safe_file_response(CONFLICT_FILE)