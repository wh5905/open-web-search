import pytest
import asyncio
from unittest.mock import MagicMock
from open_web_search.refiners.hybrid import HybridRefiner
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

@pytest.mark.asyncio
async def test_lite_ranker_logic():
    # 1. Setup
    refiner = HybridRefiner()
    if not refiner.model:
        pytest.skip("SentenceTransformer not installed")
        
    query = "python features"
    
    # 2. Mock Data: Generate 50 dummy chunks
    # Some with keywords, some garbage
    pages = [FetchedPage(url="http://test.com", text_plain="")]
    
    # Mock KeywordRefiner to return controlled chunks
    # We simulate 50 chunks. 
    # Top 5: "python 3.15 has new features" (High keyword score)
    # Next 10: "python is snake" (Medium)
    # Rest: "lorem ipsum" (Zero)
    
    # FIX: Use unique URLs to avoid MAX_PER_SOURCE=3 limit which would hide valid chunks
    high_chunks = [
        EvidenceChunk(url=f"u1_{i}", content=f"python 3.15 new features {i}", relevance_score=0.9, chunk_id=f"h{i}") 
        for i in range(5)
    ]
    mid_chunks = [
        EvidenceChunk(url=f"u2_{i}", content=f"python is a snake {i}", relevance_score=0.5, chunk_id=f"m{i}") 
        for i in range(10)
    ]
    junk_chunks = [
        EvidenceChunk(url="u3", content=f"lorem ipsum {i}", relevance_score=0.0, chunk_id=f"j{i}") 
        for i in range(35)
    ]
    
    all_chunks = high_chunks + mid_chunks + junk_chunks
    assert len(all_chunks) == 50
    
    # Mock the internal keyword refiner call
    # Since we can't easily mock the internal attribute method call in this simple script without patching,
    # let's use the real method but monkeypatch the keyword_refiner.refine
    
    async def mock_keyword_refine(pages, q):
        return all_chunks[:] # Return copy
        
    refiner.keyword_refiner.refine = mock_keyword_refine
    
    # 3. Execution
    # We expect LiteRanker to filter down to Top 20 based on keyword score.
    # High(5) + Mid(10) + Top 5 Junk = 20 chunks sent to embedding.
    # The junk should have low semantic score and be filtered out by MMR or ranked low.
    
    results = await refiner.refine(pages, query)
    
    # 4. Assertions
    print(f"\nInput Chunks: {len(all_chunks)}")
    print(f"Output Chunks: {len(results)}")
    
    # Check if high, mid are preserved
    # We expect the 5 high chunks to be in the result because they are both keyword & semantic rich
    ids = [c.chunk_id for c in results]
    
    detected_high = sum(1 for cid in ids if cid.startswith('h'))
    print(f"High Quality Retrieved: {detected_high}/5")
    
    assert detected_high == 5, "LiteRanker discarded high quality chunks!"
    assert len(results) <= 20, "Should not return more than pre-filter limit (logic check)"
    
    # Check simple performance
    import time
    start = time.time()
    await refiner.refine(pages, query)
    print(f"Execution Time (50 chunks -> 20 embedded): {time.time() - start:.4f}s")
    
if __name__ == "__main__":
    asyncio.run(test_lite_ranker_logic())
