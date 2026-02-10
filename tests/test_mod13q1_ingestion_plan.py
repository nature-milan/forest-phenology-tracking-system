from fpts.ingestion.mod13q1 import _doy_from_iso


def test_doy_from_iso_handles_leap_year() -> None:
    assert _doy_from_iso("2020-01-01T00:00:00Z") == 1
    assert _doy_from_iso("2020-02-29T00:00:00Z") == 60
    assert _doy_from_iso("2020-12-31T00:00:00Z") == 366
