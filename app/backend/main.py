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

# =========================
# TEMP MEMORY
# =========================
prev_raw_conf = None
prev_conf = None

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

def normalize(val, min_v, max_v):
    if max_v - min_v == 0:
        return 0
    return (val - min_v) / (max_v - min_v)

def avg_property(features, key):
    vals = [f["properties"].get(key, 0) for f in features]
    return sum(vals)/len(vals) if vals else 0

# =========================
# VALIDATION COMPONENTS
# =========================

def compute_alignment(zones, ndvi, rain, conflict):
    scores = []

    avg_nd = avg_property(ndvi, "ndvi")
    avg_rn = avg_property(rain, "rain")
    avg_cf = avg_property(conflict, "weight")

    # Normalize drivers
    nd_n = 1 - normalize(avg_nd, -0.2, 0.6)
    rn_n = 1 - normalize(avg_rn, 0, 200)
    cf_n = normalize(avg_cf, 0, 10)

    expected_driver = 0.4 * cf_n + 0.3 * nd_n + 0.3 * rn_n

    for f in zones:
        p = abs(f["properties"].get("pressure", 0))
        scores.append(1 - abs(p - expected_driver))

    return max(0, sum(scores)/len(scores)) if scores else 0


def compute_direction(zones):
    sources = [f for f in zones if f["properties"].get("type") == "source"]
    dests = [f for f in zones if f["properties"].get("type") == "destination"]

    valid = 0
    total = 0

    for s in sources:
        for d in dests:
            ps = abs(s["properties"].get("pressure", 0))
            pd = abs(d["properties"].get("pressure", 0))

            if ps > pd:  # source worse than destination
                valid += 1
            total += 1

    return valid / total if total > 0 else 0


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
    global prev_raw_conf, prev_conf

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
    # PRESSURE
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
    if prev_conf is not None:
        calibrated = 0.7 * calibrated + 0.3 * prev_conf

    prev_conf = calibrated
    confidence = round(min(calibrated, 1), 3)

    # =========================
    # DRIVER SCORE
    # =========================
    avg_ndvi = avg_property(ndvi, "ndvi")
    avg_rain = avg_property(rain, "rain")
    avg_conflict = avg_property(conflict, "weight")

    ndvi_n = 1 - normalize(avg_ndvi, -0.2, 0.6)
    rain_n = 1 - normalize(avg_rain, 0, 200)
    conflict_n = normalize(avg_conflict, 0, 10)

    driver_score = round(
        0.4 * conflict_n +
        0.3 * ndvi_n +
        0.3 * rain_n,
        3
    )

    # =========================
    # VALIDATION (REAL)
    # =========================
    alignment = compute_alignment(zones, ndvi, rain, conflict)
    direction = compute_direction(zones)

    if prev_raw_conf is None:
        stability = 1
    else:
        stability = 1 - abs(raw_conf - prev_raw_conf)

    prev_raw_conf = raw_conf

    validation_score = round(
        0.4 * alignment +
        0.4 * direction +
        0.2 * stability,
        3
    )

    # =========================
    # RISK
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