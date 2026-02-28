from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OutOfCoverageError(Exception):
    lat: float
    lon: float
    tolerance_deg: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def __str__(self) -> str:
        return (
            f"Location outside raster coverage: lat={self.lat}, lon={self.lon} "
            f"(tolerance={self.tolerance_deg}°; "
            f"lon range=[{self.x_min}, {self.x_max}], "
            f"lat range=[{self.y_min}, {self.y_max}])"
        )
