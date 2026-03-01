from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def write_geotiff(path: Path, data: np.ndarray, transform, crs: str = "EPSG:4326") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(data, 1)


def main() -> None:
    # Use the same DATA_DIR contract as the API
    data_root = Path(os.getenv("DATA_DIR", "data"))
    out_dir = data_root / "raw" / "ndvi_synth" / "2020"

    # Idempotency: if already seeded, exit cleanly
    sentinel = out_dir / ".seeded"
    if sentinel.exists():
        print(f"Seed already present at {out_dir.resolve()}, skipping.")
        return

    # We’ll pretend these are NDVI observations through a year.
    # DOYs and NDVI values are chosen to clearly show a seasonal curve.
    doys = [1, 50, 100, 150, 200, 250, 300, 350]
    ndvi_values = [0.10, 0.12, 0.20, 0.50, 0.70, 0.60, 0.25, 0.12]

    transform = from_origin(west=-0.5, north=51.5, xsize=0.01, ysize=0.01)

    # 10x10 raster; every pixel has the same NDVI for this timestep (simple & deterministic)
    height, width = 10, 10

    for doy, ndvi_val in zip(doys, ndvi_values, strict=True):
        arr = np.full((height, width), ndvi_val, dtype=np.float32)
        path = out_dir / f"doy_{doy:03d}.tif"
        write_geotiff(path, arr, transform)

    sentinel.write_text("ok\n")
    print(f"Wrote {len(doys)} NDVI rasters to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
