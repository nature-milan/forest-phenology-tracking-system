from pathlib import Path

from fpts.storage.local_raster_repository import LocalRasterRepository


def test_local_raster_repository_builds_expected_path(tmp_path: Path):
    repo = LocalRasterRepository(data_dir=tmp_path)

    p = repo.raw_raster_path(product="mcd12q2", year=2020)

    assert p == tmp_path / "raw" / "mcd12q2" / "2020.tif"
    assert repo.exists(product="mcd12q2", year=2020) is False
