"""
Offline inference — FINAL, NaN-SAFE
----------------------------------
Prevents NaNs from propagating through CNN inference.
"""

from pathlib import Path
import torch
import torch.nn as nn
import numpy as np
import rasterio

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent

TENSOR_DIR = PROJECT_ROOT / "data/tensors"
MODEL_PATH = PROJECT_ROOT / "models/ndvi_change_cnn.pt"
OUT_RASTER = PROJECT_ROOT / "data/predictions/migration_pressure.tif"
REFERENCE_RASTER = PROJECT_ROOT / "data/processed/ndvi_delta_1km.tif"

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TILE_SIZE = 64

# =========================
# MODEL (MUST MATCH TRAINING)
# =========================
class NDVIChangeCNN(nn.Module):
    def __init__(self, in_channels: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_channels, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 1, 1),
        )

    def forward(self, x):
        return self.net(x)

# =========================
# LOAD MODEL
# =========================
tile_files = sorted(TENSOR_DIR.glob("tile_*.pt"))
if len(tile_files) == 0:
    raise RuntimeError(f"No tensors found in {TENSOR_DIR}")

sample_tensor = torch.load(tile_files[0])
in_channels = int(sample_tensor.shape[0])

model = NDVIChangeCNN(in_channels=in_channels).to(DEVICE)
state_dict = torch.load(MODEL_PATH, map_location=DEVICE)
try:
    model.load_state_dict(state_dict)
except RuntimeError as exc:
    raise RuntimeError(
        "Model weights are incompatible with tensor channel count. "
        "Regenerate tensors and retrain the model before running inference."
    ) from exc
model.eval()

# =========================
# LOAD GRID
# =========================
with rasterio.open(REFERENCE_RASTER) as ref:
    height, width = ref.height, ref.width
    transform = ref.transform
    crs = ref.crs

pressure_sum = np.zeros((height, width), dtype=np.float32)
pressure_count = np.zeros((height, width), dtype=np.float32)

# =========================
# INFERENCE
# =========================
print("Running inference...")

tiles_per_row = width // TILE_SIZE

for tile_file in tile_files:
    tensor = torch.load(tile_file)

    # 🔑 SANITIZE INPUT (CRITICAL)
    tensor = torch.nan_to_num(
        tensor,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    tensor = tensor.unsqueeze(0).to(DEVICE)

    with torch.no_grad():
        pred = model(tensor).squeeze().cpu().numpy()

    # 🔑 SANITIZE OUTPUT
    pred = np.nan_to_num(pred, nan=0.0, posinf=0.0, neginf=0.0)

    tile_id = int(tile_file.stem.split("_")[1])
    row = (tile_id // tiles_per_row) * TILE_SIZE
    col = (tile_id % tiles_per_row) * TILE_SIZE

    if row + TILE_SIZE > height or col + TILE_SIZE > width:
        continue

    pressure_sum[row:row+TILE_SIZE, col:col+TILE_SIZE] += pred
    pressure_count[row:row+TILE_SIZE, col:col+TILE_SIZE] += 1

# =========================
# FINAL PRESSURE MAP
# =========================
valid = pressure_count > 0
pressure = np.zeros_like(pressure_sum)
pressure[valid] = pressure_sum[valid] / pressure_count[valid]

print("Pressure stats:")
print("Min:", float(np.min(pressure)))
print("Max:", float(np.max(pressure)))
print("Std:", float(np.std(pressure)))

# =========================
# WRITE OUTPUT
# =========================
with rasterio.open(
    OUT_RASTER,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=1,
    dtype="float32",
    crs=crs,
    transform=transform,
) as dst:
    dst.write(pressure, 1)

print("Migration pressure raster written to:", OUT_RASTER)
