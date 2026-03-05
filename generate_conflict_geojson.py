from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

PROJECT_ROOT = Path(__file__).resolve().parent

INPUT = PROJECT_ROOT / "data/conflict/south_sudan_conflict.csv"
OUTPUT = PROJECT_ROOT / "data/predictions/conflict_heatmap.geojson"

df = pd.read_csv(INPUT)

print("Rows:", len(df))

geometry = [Point(xy) for xy in zip(df["longitude"], df["latitude"])]

gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

gdf["weight"] = df["best"].fillna(1)

gdf[["geometry", "weight"]].to_file(OUTPUT, driver="GeoJSON")

print("Conflict GeoJSON written:", OUTPUT)