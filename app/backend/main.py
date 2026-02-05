from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Cattle Migration Prediction API", version="0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "API running", "scope": "UN demo"}

@app.post("/predict")
def predict():
    # Placeholder for model inference
    return {
        "heatmap_url": "/static/mock_heatmap.json",
        "confidence": 0.78,
        "lead_time_days": 21
    }

@app.post("/upload-dataset")
def upload_dataset(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "status": "uploaded and queued for processing"
    }

@app.get("/metrics")
def metrics():
    return {
        "accuracy": 0.81,
        "conflicts_prevented_est": 34,
        "evaluation_window_days": 30
    }
