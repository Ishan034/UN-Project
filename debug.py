from pathlib import Path
import rasterio
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
RAIN_PATH = PROJECT_ROOT / "data" / "processed" / "rainfall_30d_1km.tif.tif"

with rasterio.open(RAIN_PATH) as src:
    data = src.read(1)

print("Min:", np.nanmin(data))
print("Max:", np.nanmax(data))
print("Mean:", np.nanmean(data))
print("NaNs:", np.isnan(data).sum())
print("Total:", data.size)
