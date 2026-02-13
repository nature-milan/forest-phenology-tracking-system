from pathlib import Path

import numpy as np
import rasterio
import rioxarray
from rasterio.transform import from_origin


def test_can_write_and_read_geotiff(tmp_path: Path):
    out_path = tmp_path / "tiny.tif"

    data = np.arange(100, dtype=np.int16).reshape((10, 10))
    transform = from_origin(west=-0.5, north=51.5, xsize=0.01, ysize=0.01)

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

    da = rioxarray.open_rasterio(out_path)

    assert da.shape == (1, 10, 10)
    assert str(da.rio.crs) == "EPSG:4326"
    assert int(da.isel(band=0, y=0, x=0).values) == 0
    assert int(da.isel(band=0, y=9, x=9).values) == 99
