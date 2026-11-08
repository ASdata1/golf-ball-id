"""Rebuild data/processed/ (clips + shots.parquet) from every session in data/raw/."""
from golfball.ingest import build_index

index = build_index()
print(index.groupby(["session_id", "ball_model"]).size().to_string())
print(f"\n{len(index)} shots, {index.valid.sum()} valid")
