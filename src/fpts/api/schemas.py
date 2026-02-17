from datetime import date
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class LocationSchema(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)

    model_config = ConfigDict(frozen=True)


class PhenologyPointResponse(BaseModel):
    """
    Phenology metrics for a single location and year.
    This is the shape that our phenology endpoints will return to a client.
    """

    year: int
    location: LocationSchema
    sos_date: Optional[date] = None
    eos_date: Optional[date] = None
    season_length: Optional[int] = None
    is_forest: bool

    model_config = ConfigDict(frozen=True)


class PhenologyYearMetricSchema(BaseModel):
    year: int
    sos_date: Optional[date] = None
    eos_date: Optional[date] = None
    season_length: Optional[int] = None
    is_forest: bool

    model_config = ConfigDict(frozen=True)


class PhenologyTimeseriesResponse(BaseModel):
    product: str
    location: LocationSchema
    start_year: int
    end_year: int
    metrics: list[PhenologyYearMetricSchema]

    model_config = ConfigDict(frozen=True)


class GeoJSONPolygonRequest(BaseModel):
    geometry: dict = Field(..., description="GeoJSON Polygon or MultiPolygon geometry")

    @field_validator("geometry")
    @classmethod
    def validate_geometry_type(cls, val: dict) -> dict:
        if not isinstance(val, dict):
            raise ValueError("Geometry must be a JSON object")

        geom_type = val.get("type")
        if geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Only Polygon or MultiPolygon geometries are supported")

        if "coordinates" not in val:
            raise ValueError("GeoJSON geometry must contain coordinates")

        return val

    model_config = ConfigDict(frozen=True)


class PhenologyAreaStatsResponse(BaseModel):
    product: str
    year: int
    n: int

    mean_season_length: float | None = None
    median_season_length: float | None = None
    forest_fraction: float | None = None

    model_config = ConfigDict(frozen=True)


class SeasonLengthStat(str, Enum):
    mean = "mean"
    median = "median"
    both = "both"
