from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import rioxarray
import xarray as xr

from fpts.domain.models import Location

_DOY_RE = re.compile(r"doy_(\d{3})\.tif$")


@dataclass(frozen=True)
class NdviTimeSeries:
    doys: list[int]
    ndvi: list[float]


def _doy_from_filename(path: Path) -> int:
    match = _DOY_RE.search(path.name)
    if not match:
        raise ValueError(f"Unexpected NDVI filename format: {path.name}")
    return int(match.group(1))


def load_ndvi_stack(paths: Sequence[Path]) -> xr.DataArray:
    """
    Load multiple single-band GeoTIFFs into a time-stacked DataArray.
    Output dims: time, band, y, x
    """
    if not paths:
        raise ValueError("Paths must not be empty")

    # sort by DOY so time is in order
    sorted_paths = sorted(paths, key=_doy_from_filename)
    rasters = [
        rioxarray.open_rasterio(path) for path in sorted_paths
    ]  # each: band, y, x

    stack = xr.concat(rasters, dim="time")  # time, band, y, x
    stack = stack.assign_coords(
        time=[_doy_from_filename(path) for path in sorted_paths]
    )
    return stack


def extract_ndvi_timeseries(stack: xr.DataArray, location: Location) -> NdviTimeSeries:
    """
    Extract NDVI values across time at a given lat/lon (nearest pixel).
    Assumes x=lon, y=lat (EPSG:4326 in our synthetic data).
    """
    sampled = stack.sel(x=location.lon, y=location.lat, method="nearest")
    values = sampled.isel(band=0).values
    doys = [int(time) for time in sampled["time"].values.tolist()]
    ndvi = [float(val) for val in values.tolist()]
    return NdviTimeSeries(doys=doys, ndvi=ndvi)


def extract_ndvi_timeseries_batch(
    stack: xr.DataArray, locations: Sequence[Location]
) -> list[NdviTimeSeries]:
    """
    Vectorized extraction for many lat/lon points (nearest pixel).

    Returns one NdviTimeSeries per input location in the same order.
    """
    if not locations:
        return []

    lons = [loc.lon for loc in locations]
    lats = [loc.lat for loc in locations]

    # dims after sel: time, band, points
    sampled = stack.sel(
        x=xr.DataArray(lons, dims="points"),
        y=xr.DataArray(lats, dims="points"),
        method="nearest",
    )

    values = sampled.isel(band=0).values  # shape: (time, points)
    doys = [int(t) for t in sampled["time"].values.tolist()]

    out: list[NdviTimeSeries] = []
    for i in range(len(locations)):
        ndvi = [float(v) for v in values[:, i].tolist()]
        out.append(NdviTimeSeries(doys=doys, ndvi=ndvi))
    return out
