from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from typing import Optional

from fpts.domain.models import Location, PhenologyMetric
from fpts.processing.ndvi_stack import extract_ndvi_timeseries, load_ndvi_stack
from fpts.processing.phenology_algorithm import compute_sos_eos_threshold
from fpts.storage.raster_repository import RasterRepository


def _date_from_doy(year: int, doy: int) -> date:
    # DOY 1 = Jan 1
    return date(year, 1, 1) + timedelta(days=doy - 1)


class PhenologyComputationService:
    """
    Computes phenology metrics for a given location using an NDVI raster time stack.
    """

    def __init__(self, raster_repo: RasterRepository) -> None:
        self._raster_repo = raster_repo

    def compute_point_phenology(
        self,
        product: str,
        year: int,
        location: Location,
        threshold_frac: float = 0.5,
        is_forest: bool = True,
    ) -> PhenologyMetric:
        paths = self._raster_repo.list_ndvi_stack_paths(product=product, year=year)
        if not paths:
            raise FileNotFoundError(
                f"No NDVI stack files found for product={product}, year={year}"
            )

        stack = load_ndvi_stack(paths)
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
