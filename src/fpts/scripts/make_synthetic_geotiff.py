from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin


def main() -> None:
    # Output location: data/raw/synthetic/2020.tif
    out_path = Path("data/raw/synthetic/2020.tif")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a tiny 10x10 raster with values 0..99
    data = np.arange(100, dtype=np.int16).reshape((10, 10))

    # Define a simple georeferencing:
    # top-left corner at lon=-0.5, lat=51.5, pixel size 0.01 degrees
    transform = from_origin(west=-0.5, north=51.5, xsize=0.01, ysize=0.01)

    # Write a single-band GeoTIFF in WGS84
    with rasterio.open(
        out_path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(data, 1)

    print(f"Wrote GeoTIFF: {out_path.resolve()}")


if __name__ == "__main__":
    main()
