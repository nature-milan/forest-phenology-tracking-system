from __future__ import annotations

from pathlib import Path

import rioxarray


def main() -> None:
    path = Path("data/raw/synthetic/2020.tif")
    if not path.exists():
        raise FileNotFoundError(
            f"Raster not found: {path}. Run make_synthetic_geotiff first."
        )

    da = rioxarray.open_rasterio(path)  # DataArray with dims: band, y, x

    print("Opened:", path)
    print("Shape:", da.shape)
    print("CRS:", da.rio.crs)
    print("Transform:", da.rio.transform())

    # Read a couple of values
    v00 = int(da.isel(band=0, y=0, x=0).values)
    v99 = int(da.isel(band=0, y=9, x=9).values)

    print("Top-left value:", v00)  # expected 0
    print("Bottom-right value:", v99)  # expected 99


if __name__ == "__main__":
    main()
