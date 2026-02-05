from __future__ import annotations

from typing import Any

import rioxarray
from rasterio.errors import RasterioIOError

from fpts.domain.models import Location
from fpts.storage.raster_repository import RasterRepository


class RasterService:
    """
    Service responsible for reading raster data and sampling values.
    """

    def __init__(self, raster_repo: RasterRepository) -> None:
        self._raster_repo = raster_repo

    def sample_point(
        self,
        product: str,
        year: int,
        location: Location,
    ) -> Any:
        """
        Sample a raster at a given location (lat/ lon.)

        Returns the pixel value (band 1).

        Raises FileNotFoundError if raster does not exist.
        """

        if not self._raster_repo.exists(product=product, year=year):
            raise FileNotFoundError(
                f"Raster not found for product={product}, year={year}"
            )

        path = self._raster_repo.raw_raster_path(product=product, year=year)

        try:
            da = rioxarray.open_rasterio(path)
        except RasterioIOError as e:
            raise RuntimeError(f"Failed to open raster: {path}") from e

        # Note: y = latitude, x = longitude
        sampled = da.sel(
            x=location.lon,
            y=location.lat,
            method="nearest",
        )

        # Single-band raster -> take band 1
        value = sampled.isel(band=0).values.item()
        return value
