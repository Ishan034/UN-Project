"""
Offline inference script (V1)
----------------------------
Runs the trained CNN on stacked tiles and produces:
1. Migration pressure raster
2. Summary statistics for backend / frontend

This script is designed for SCHEDULED / NEAR-REAL-TIME runs.
"""

from pathlib import Path
import numpy as np
import torch
import rasterio
from rasterio.transform import from_origin

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parent

MODEL_PATH = PROJECT_ROOT / "models/ndvi_change_cnn.pt"
TENSOR_DIR = PROJECT_ROOT / "data/tensors"
NDVI_REF = PROJECT_ROOT / "data/processed/ndvi_1km.tif"

OUT_DIR = PROJECT_ROOT / "data/predictions"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_RASTER = OUT_DIR / "migration_pressure.tif"

# =========================
# MODEL DEFINITION (MUST MATCH TRAINING)
# =========================
class MigrationCNN(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Conv2d(2, 16, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(16, 32, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(32, 1, 1)
        )

    def forward(self, x):
        return self.net(x)

# =========================
# MAIN INFERENCE
# =========================
def run_inference():
    print("Loading model...")

    model = MigrationCNN()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    model.eval()

    tiles = sorted(TENSOR_DIR.glob("tile_*.pt"))
    if len(tiles) == 0:
        raise RuntimeError("No tiles found for inference")

    print(f"Running inference on {len(tiles)} tiles")

    # Load reference raster for shape + transform
    with rasterio.open(NDVI_REF) as ref:
        height, width = ref.height, ref.width
        transform = ref.transform
        crs = ref.crs

    # Initialize pressure map
    pressure_map = np.zeros((height, width), dtype=np.float32)
    count_map = np.zeros((height, width), dtype=np.int32)

    tile_size = 64

    for idx, tile_path in enumerate(tiles):
        tensor = torch.load(tile_path).unsqueeze(0)  # [1, 2, 64, 64]
        with torch.no_grad():
            pred = model(tensor).squeeze().numpy()  # [64, 64]

        # Infer tile placement from index (same order as stacking)
        tile_row = idx // (width // tile_size)
        tile_col = idx % (width // tile_size)

        r0 = tile_row * tile_size
        c0 = tile_col * tile_size

        if r0 + tile_size > height or c0 + tile_size > width:
            continue

        pressure_map[r0:r0+tile_size, c0:c0+tile_size] += pred
        count_map[r0:r0+tile_size, c0:c0+tile_size] += 1

    # Average overlapping predictions
    valid = count_map > 0
    pressure_map[valid] /= count_map[valid]

    # =========================
    # SAVE RASTER
    # =========================
    with rasterio.open(
        OUT_RASTER,
        "w",
        driver="GTiff",
        height=pressure_map.shape[0],
        width=pressure_map.shape[1],
        count=1,
        dtype="float32",
        crs=crs,
        transform=transform,
    ) as dst:
        dst.write(pressure_map, 1)

    print(f"Migration pressure raster saved to {OUT_RASTER}")

    # Summary stats (for backend confidence)
    stats = {
        "min": float(np.nanmin(pressure_map)),
        "max": float(np.nanmax(pressure_map)),
        "mean": float(np.nanmean(pressure_map)),
    }

    print("Summary stats:", stats)
    return stats


if __name__ == "__main__":
    run_inference()
