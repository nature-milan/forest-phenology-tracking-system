from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import xarray as xr

from fpts.domain.models import Location, PhenologyMetric
from fpts.processing.ndvi_stack import load_ndvi_stack, extract_ndvi_timeseries
from fpts.processing.phenology_algorithm import compute_sos_eos_threshold
from fpts.storage.raster_repository import RasterRepository


def _date_from_doy(year: int, doy: int) -> date:
    return date(year, 1, 1) + timedelta(days=doy - 1)


class PhenologyComputationService:
    """
    Computes phenology metrics for a given location using an NDVI raster time stack.

    Includes a small in-memory cache of loaded stacks keyed by (product, year)
    """

    def __init__(self, raster_repo: RasterRepository) -> None:
        self._raster_repo = raster_repo
        self._stack_cache: dict[tuple[str, int], xr.DataArray] = {}

    def compute_point_phenology(
        self,
        product: str,
        year: int,
        location: Location,
        threshold_frac: float = 0.5,
        is_forest: bool = True,
    ) -> PhenologyMetric:
        key = (product, year)

        if key in self._stack_cache:
            stack = self._stack_cache[key]

        else:
            paths = self._raster_repo.list_ndvi_stack_paths(product=product, year=year)
            if not paths:
                raise FileNotFoundError(
                    f"No NDVI stack files found for product={product}, year={year}"
                )
            stack = load_ndvi_stack(paths)
            self._stack_cache[key] = stack

        time_series = extract_ndvi_timeseries(stack, location)

        dates = compute_sos_eos_threshold(
            ndvi=time_series.ndvi, doys=time_series.doys, frac=threshold_frac
        )

        sos_date: Optional[date] = (
            _date_from_doy(year, dates.sos_doy) if dates.sos_doy else None
        )
        eos_date: Optional[date] = (
            _date_from_doy(year, dates.eos_doy) if dates.eos_doy else None
        )

        return PhenologyMetric(
            year=year,
            location=location,
            sos_date=sos_date,
            eos_date=eos_date,
            season_length=dates.season_length,
            is_forest=is_forest,
        )
