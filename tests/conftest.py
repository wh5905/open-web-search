import pytest
import asyncio
from open_web_search.config import LinkerConfig
from open_web_search.core.pipeline import AsyncPipeline

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def basic_config():
    return LinkerConfig(
        mode="fast",
        observability_level="basic",
        cache_dir=".linker_cache_test" # Use different cache for tests
    )

@pytest.fixture
def pipeline(basic_config):
    return AsyncPipeline(config=basic_config)
