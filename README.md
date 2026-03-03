# UN-Project

UN Cattle Movement Prediction Project for South Sudan.

## Current pipeline (as implemented)

1. **Prepare spatial layers**
   - NDVI delta raster in `data/processed/ndvi_delta_1km.tif`
   - 30-day rainfall raster in `data/processed/rainfall_30d_1km.tif`
2. **Stack model-ready tiles**
   - `preprocessing/stack_tiles.py` creates `data/tensors/tile_*.pt`
3. **Train model**
   - `training_ndvi_change.py` trains a CNN and writes `models/ndvi_change_cnn.pt`
4. **Run inference**
   - `offline_inference.py` generates `data/predictions/migration_pressure.tif`

## New: ACLED integration

This project now supports incorporating ACLED conflict events as an additional feature channel.

### ACLED timeframe and source

- Current implementation uses a **90-day lookback** (`LOOKBACK_DAYS = 90`), which is approximately **3 months**.
- ACLED data should come from your ACLED export for South Sudan (CSV) downloaded via:
  - ACLED Data Export Tool: https://acleddata.com/data-export-tool/
  - or ACLED API: https://acleddata.com/

### Step 1 — add ACLED CSV

Place your ACLED export at:

- `data/acled/south_sudan_acled.csv`

Expected columns:

- `latitude`
- `longitude`
- `event_date` (recommended for 90-day lookback filtering)

### Step 2 — build ACLED raster

```bash
python preprocessing/acled.py
```

This creates:

- `data/processed/acled_events_90d_1km.tif`

The raster is aligned with the NDVI grid and stores normalized event density (0–1).

### Step 3 — generate ACLED web layer

```bash
python generate_acled_geojson.py
```

This creates:

- `data/predictions/acled_heatmap.geojson`

Used by backend endpoint `/acled` and the frontend ACLED toggle layer.

### Step 4 — restack tiles

```bash
python preprocessing/stack_tiles.py
```

If the ACLED raster exists, tensors are stacked as 3 channels:

1. NDVI delta
2. Rainfall
3. ACLED conflict density

If ACLED raster is missing, the pipeline falls back to the original 2-channel tensors.

### Step 5 — retrain and infer

```bash
python training_ndvi_change.py
python offline_inference.py
```

Both scripts now infer model input channels from the tensor data automatically, so they work with 2-channel and 3-channel pipelines.
