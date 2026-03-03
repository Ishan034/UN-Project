"""
ACLED preprocessing
-------------------
Builds a 1km raster of recent conflict event density aligned to the NDVI grid.

Input CSV requirements:
- latitude
- longitude
- event_date (optional but used for lookback filtering)

Output:
- data/processed/acled_events_90d_1km.tif
"""

from pathlib import Path
import pandas as pd
import numpy as np
import rasterio
from rasterio.transform import rowcol
from rasterio.warp import transform as transform_coords

# =========================
# PATHS
# =========================
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACLED_DIR = PROJECT_ROOT / "data/acled"
ACLED_CSV = ACLED_DIR / "south_sudan_acled.csv"
REFERENCE_RASTER = PROJECT_ROOT / "data/processed/ndvi_delta_1km.tif"
OUTPUT_RASTER = PROJECT_ROOT / "data/processed/acled_events_90d_1km.tif"

LOOKBACK_DAYS = 90  # ~3 months
DATE_COLUMN = "event_date"
LAT_COLUMN = "latitude"
LON_COLUMN = "longitude"
SOURCE_CRS = "EPSG:4326"  # ACLED coordinates are lon/lat in WGS84


def resolve_acled_csv(csv_path: Path) -> Path:
    """Resolve ACLED csv path, supporting any single CSV in data/acled."""
    if csv_path.exists():
        return csv_path

    if ACLED_DIR.exists():
        csv_candidates = sorted(ACLED_DIR.glob("*.csv"))
        if len(csv_candidates) == 1:
            return csv_candidates[0]
        if len(csv_candidates) > 1:
            raise FileNotFoundError(
                "Multiple CSV files found in data/acled. "
                "Please keep one file or rename target to south_sudan_acled.csv."
            )

    raise FileNotFoundError(
        f"ACLED CSV not found at {csv_path}. Place your export there first."
    )


def load_and_filter_acled(csv_path: Path) -> pd.DataFrame:
    csv_path = resolve_acled_csv(csv_path)
    print(f"Using ACLED file: {csv_path}")

    df = pd.read_csv(csv_path)

    for col in [LAT_COLUMN, LON_COLUMN]:
        if col not in df.columns:
            raise ValueError(f"Missing required ACLED column: {col}")

    df = df.dropna(subset=[LAT_COLUMN, LON_COLUMN]).copy()

    if DATE_COLUMN in df.columns:
        df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN], errors="coerce")
        newest = df[DATE_COLUMN].max()
        if pd.notna(newest):
            cutoff = newest - pd.Timedelta(days=LOOKBACK_DAYS)
            df = df[df[DATE_COLUMN] >= cutoff]

    return df


def rasterize_event_density(df: pd.DataFrame):
    with rasterio.open(REFERENCE_RASTER) as ref:
        height, width = ref.height, ref.width
        transform = ref.transform
        crs = ref.crs

        density = np.zeros((height, width), dtype=np.float32)

        lons = df[LON_COLUMN].to_numpy(dtype=float)
        lats = df[LAT_COLUMN].to_numpy(dtype=float)

        # Reproject ACLED lon/lat points (WGS84) onto the reference raster CRS.
        if str(crs) != SOURCE_CRS:
            xs, ys = transform_coords(SOURCE_CRS, crs, lons.tolist(), lats.tolist())
        else:
            xs, ys = lons, lats

        in_bounds = 0
        for x, y in zip(xs, ys):
            row, col = rowcol(transform, x, y)
            if 0 <= row < height and 0 <= col < width:
                density[row, col] += 1.0
                in_bounds += 1

        if density.max() > 0:
            density = density / density.max()

        OUTPUT_RASTER.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(
            OUTPUT_RASTER,
            "w",
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype="float32",
            crs=crs,
            transform=transform,
        ) as dst:
            dst.write(density, 1)

    print(f"ACLED raster written to: {OUTPUT_RASTER}")
    print(f"Included events after filtering: {len(df)}")
    print(f"Events inside reference raster extent: {in_bounds}")


def main():
    df = load_and_filter_acled(ACLED_CSV)
    rasterize_event_density(df)


if __name__ == "__main__":
    main()
