import asyncio
import sys
from loguru import logger
from open_web_search.refiners.hybrid import HybridRefiner
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

# Force logging to stdout
logger.remove()
logger.add(sys.stdout, level="DEBUG")

async def verify_logic():
    print("\n--- 🕵️‍♂️ Verifying LiteRanker Logic Flow ---")
    
    refiner = HybridRefiner()
    # Force load model
    if not refiner.model:
        print("❌ Model not loaded (SentenceTransformers missing?)")
        return

    query = "feline behavior"
    
    # 1. Exact Match (High Keyword, High Semantic)
    c1 = EvidenceChunk(url="u1", chunk_id="c1", content="Feline behavior includes hunting and sleeping naturally.", relevance_score=0.0)
    
    # 2. Synonym Match at START (Protection Test)
    # Should be caught by SAFETY_NET_COUNT (First 5)
    c2 = EvidenceChunk(url="u2", chunk_id="c2_start", content="Cats love to chase mice and nap all day long.", relevance_score=0.0)
    
    # 3. Keyword Stuffing (High Keyword, Low Semantic)
    c3 = EvidenceChunk(url="u3", chunk_id="c3", content="Feline feline feline behavior behavior behavior buy now.", relevance_score=0.0)
    
    # 4. Synonym Match at END (Risk Test)
    # Likely dropped if not in top keywords and not in intro. This is the Trade-off.
    c4 = EvidenceChunk(url="u4", chunk_id="c4_end", content="Kittens play with yarn.", relevance_score=0.0)
    
    # 5. Fillers
    fillers = [
        EvidenceChunk(url=f"f{i}", chunk_id=f"f{i}", content=f"Random text {i} with no keywords", relevance_score=0.0)
        for i in range(50) # Enough to push C4 out of random luck
    ]
    
    # Lucky filler
    fillers[10].content = "A feline is a cat."
    
    # Construct input order: C2 (Start), C1, C3, Fillers..., C4 (End)
    all_chunks = [c2, c1, c3] + fillers + [c4]
    
    # Scores
    c1.relevance_score = 1.0
    c2.relevance_score = 0.0 # Synonym blind
    c3.relevance_score = 0.9
    c4.relevance_score = 0.0
    fillers[10].relevance_score = 0.5
    for f in fillers: 
        if f != fillers[10]: f.relevance_score = 0.0
    
    mock_stage1_output = all_chunks
    
    # Patch
    refiner.keyword_refiner.refine = MagicMock_Async(return_value=mock_stage1_output)
    
    print(f"Input: {len(mock_stage1_output)} chunks.")
    
    # Create Test Page Container
    page = FetchedPage(url="http://test.com", text_plain="dummy")
    
    # RUN
    results = await refiner.refine([page], query)
    
    print("\n--- 🔍 Results Analysis ---")
    result_ids = [c.chunk_id for c in results]
    print(f"Returned IDs (Count {len(result_ids)}): {result_ids}")
    
    # Logic Checks
    if "c2_start" in result_ids:
        print("✅ C2 (Synonym at Start) - SAW SAFETY NET! (Preserved by First-5 Rule)")
    else:
        print("❌ C2 (Synonym at Start) - LOST! Safety Net Failed.")

    if "c4_end" in result_ids:
        print("⚠️ C4 (Synonym at End) - Preserved (Lucky?)")
    else:
        print("✅ C4 (Synonym at End) - Dropped (Expected Trade-off for Speed).")
        
    embed_count = len(set(result_ids)) # Approx
    print(f"Embedding Count: {embed_count} (Should be around 20-25)")

# Minimal Async Mock
class MagicMock_Async:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __call__(self, *args, **kwargs):
        return self.return_value

if __name__ == "__main__":
    asyncio.run(verify_logic())
