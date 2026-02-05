from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def write_geotiff(
    path: Path, data: np.ndarray, transform, crs: str = "EPSG:4326"
) -> None:
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
    # We’ll pretend these are NDVI observations through a year.
    # DOYs and NDVI values are chosen to clearly show a seasonal curve.
    doys = [1, 50, 100, 150, 200, 250, 300, 350]
    ndvi_values = [0.10, 0.12, 0.20, 0.50, 0.70, 0.60, 0.25, 0.12]

    out_dir = Path("data/raw/ndvi_synth/2020")
    transform = from_origin(west=-0.5, north=51.5, xsize=0.01, ysize=0.01)

    # 10x10 raster; every pixel has the same NDVI for this timestep (simple & deterministic)
    height, width = 10, 10

    for doy, ndvi_val in zip(doys, ndvi_values, strict=True):
        arr = np.full((height, width), ndvi_val, dtype=np.float32)
        path = out_dir / f"doy_{doy:03d}.tif"
        write_geotiff(path, arr, transform)

    print(f"Wrote {len(doys)} NDVI rasters to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
