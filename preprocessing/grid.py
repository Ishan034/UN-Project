import geopandas as gpd
import numpy as np
from shapely.geometry import box
from typing import List, Dict


# =========================
# CONFIG (LOCKED)
# =========================
GRID_RESOLUTION_METERS = 1000          # 1 km
TILE_SIZE_KM = 64                      # 64 km tiles
OVERLAP_KM = 8                         # 8 km overlap

TILE_SIZE_METERS = TILE_SIZE_KM * 1000
OVERLAP_METERS = OVERLAP_KM * 1000
TILE_STRIDE_METERS = TILE_SIZE_METERS - OVERLAP_METERS


# =========================
# STEP 1 — LOAD COUNTRY BOUNDARY
# =========================
def load_country_boundary(shapefile_path: str) -> gpd.GeoDataFrame:
    """
    Load and reproject country boundary to EPSG:3857 (meters).
    """
    gdf = gpd.read_file(shapefile_path)
    gdf = gdf.to_crs(epsg=3857)
    return gdf


# =========================
# STEP 2 — CREATE 1 KM GRID
# =========================
def create_1km_grid(boundary: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Generate a 1 km × 1 km grid clipped to the country boundary.
    """
    minx, miny, maxx, maxy = boundary.total_bounds

    x_coords = np.arange(minx, maxx, GRID_RESOLUTION_METERS)
    y_coords = np.arange(miny, maxy, GRID_RESOLUTION_METERS)

    cells = []
    for x in x_coords:
        for y in y_coords:
            cell = box(
                x,
                y,
                x + GRID_RESOLUTION_METERS,
                y + GRID_RESOLUTION_METERS
            )
            cells.append(cell)

    grid = gpd.GeoDataFrame(
        {"geometry": cells},
        crs="EPSG:3857"
    )

    # Clip grid to country boundary
    grid = gpd.overlay(grid, boundary, how="intersection")

    # Assign unique cell IDs
    grid["cell_id"] = np.arange(len(grid))

    return grid


# =========================
# STEP 3 — CREATE OVERLAPPING TILES
# =========================
def create_tiles(boundary: gpd.GeoDataFrame) -> List[Dict]:
    """
    Create overlapping 64×64 km tiles with 8 km overlap.
    Returns a list of tile bounding boxes + metadata.
    """
    minx, miny, maxx, maxy = boundary.total_bounds

    tiles = []
    tile_id = 0

    x_positions = np.arange(minx, maxx, TILE_STRIDE_METERS)
    y_positions = np.arange(miny, maxy, TILE_STRIDE_METERS)

    for x in x_positions:
        for y in y_positions:
            tile_geom = box(
                x,
                y,
                x + TILE_SIZE_METERS,
                y + TILE_SIZE_METERS
            )

            tiles.append({
                "tile_id": tile_id,
                "geometry": tile_geom
            })
            tile_id += 1

    return tiles


# =========================
# STEP 4 — ASSIGN CELLS TO TILES
# =========================
def assign_cells_to_tiles(
    grid: gpd.GeoDataFrame,
    tiles: List[Dict]
) -> Dict[int, gpd.GeoDataFrame]:
    """
    Assign 1 km grid cells to overlapping tiles.
    Returns: {tile_id: GeoDataFrame of cells}
    """
    tile_cell_map = {}

    for tile in tiles:
        tile_id = tile["tile_id"]
        tile_geom = tile["geometry"]

        tile_cells = grid[grid.intersects(tile_geom)].copy()
        tile_cells["tile_id"] = tile_id

        tile_cell_map[tile_id] = tile_cells

    return tile_cell_map


# =========================
# STEP 5 — MAIN PIPELINE
# =========================
def build_grid_and_tiles(shapefile_path: str):
    """
    Full pipeline:
    boundary → 1 km grid → overlapping tiles → cell assignment
    """
    boundary = load_country_boundary(shapefile_path)
    grid = create_1km_grid(boundary)
    tiles = create_tiles(boundary)
    tile_cell_map = assign_cells_to_tiles(grid, tiles)

    return grid, tiles, tile_cell_map
