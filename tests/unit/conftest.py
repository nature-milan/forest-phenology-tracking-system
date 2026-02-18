import pytest

from fpts.api.main import create_app
from fpts.config.settings import Settings


@pytest.fixture
def app_memory():
    return create_app(
        settings=Settings(
            phenology_repo_backend="memory",
        )
    )
