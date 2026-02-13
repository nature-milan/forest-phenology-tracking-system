from pathlib import Path

from fpts.processing.ndvi_stack import load_ndvi_stack
from fpts.storage.local_raster_repository import LocalRasterRepository


def test_mod13q1_fixture_stack_loads_offline() -> None:
    repo = LocalRasterRepository(data_dir=Path("tests/fixtures"))

    paths = repo.list_ndvi_stack_paths(product="mod13q1", year=2020)
    assert [p.name for p in paths] == ["doy_001.tif", "doy_017.tif", "doy_033.tif"]

    stack = load_ndvi_stack(paths)

    # time coord should be DOYs from filenames
    assert stack.sizes["time"] == 3
    assert stack["time"].values.tolist() == [1, 17, 33]

    # tiny file expectations
    assert stack.sizes["x"] == 32
    assert stack.sizes["y"] == 32
