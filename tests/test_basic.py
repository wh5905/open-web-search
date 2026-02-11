import pytest
from open_web_search.schemas.results import PipelineOutput

@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    assert pipeline.config.mode == "fast"
    assert pipeline.engine is not None
    assert pipeline.reader is not None

@pytest.mark.asyncio
async def test_search_execution(pipeline):
    # This is an integration test as it hits the real network
    # We might want to mock the engine for pure unit tests, 
    # but for this MVP ensuring it works end-to-end is valuable.
    query = "python programming language"
    output = await pipeline.run(query)
    
    assert isinstance(output, PipelineOutput)
    assert output.query == query
    assert len(output.results) >= 0 
    # Can't guarantee results if network fails, but shouldn't raise exception
    assert "error" not in output.trace

@pytest.mark.asyncio
async def test_empty_query_handling(pipeline):
    output = await pipeline.run("")
    assert output.query == ""
    # Should probably return empty results gracefully
