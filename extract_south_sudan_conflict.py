import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

INPUT = PROJECT_ROOT / "data/conflict/ged231.csv"
OUTPUT = PROJECT_ROOT / "data/conflict/south_sudan_conflict.csv"

print("Loading conflict dataset...")

df = pd.read_csv(INPUT)

south_sudan = df[df["country"] == "South Sudan"]

print("South Sudan events:", len(south_sudan))

south_sudan.to_csv(OUTPUT, index=False)

print("Saved to:", OUTPUT)