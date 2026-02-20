import time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from loguru import logger
import os

from open_web_search.config import LinkerConfig
from open_web_search.core.loop import DeepResearchLoop # Kept for backward compat if needed, but not used in new flow
from open_web_search.server.schemas import TavilyRequest, TavilyResponse, TavilySearchResult

app = FastAPI(title="Linker-Search Universal API", version="0.3.0")

# Global Agent Cache (Mocking reusable context if needed, but for now mostly stateless)
# Ideally we init the agent per request or re-use a shared one if it's stateless.
# DeepResearchLoop is cheap to init.

@app.post("/search", response_model=TavilyResponse)
@app.post("/v1/search", response_model=TavilyResponse) # Mock official endpoint
async def search(request: TavilyRequest):
    start_time = time.time()
    logger.info(f"API Request: {request.query} (depth={request.search_depth})")
    
    # 1. Map Parameters to Linker Config
    # Default to 'deep' if advanced, else 'fast'
    default_mode = "deep" if request.search_depth == "advanced" else "fast"
    
    # Priority: Explicit mode > Search Depth > Default
    mode = request.mode or default_mode
    
    # Crawler Logic
    use_crawler = request.use_neural_crawler or (request.search_depth == "advanced" and mode == "deep")
    
    config = LinkerConfig(
        mode=mode,
        engine_provider="searxng",
        # Allow env var override for base URL, default to localhost
        engine_base_url=os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080"),
        search_language="auto",
        
        # New v0.9.0 Consiguration
        reranker_type=request.reranker or "fast",
        reader_type=request.reader or "trafilatura",
        max_evidence=request.max_evidence or request.max_results,
        
        # Legacy/Crawler params (Only relevant if mode=deep)
        use_neural_crawler=use_crawler,
        crawler_max_pages=request.max_results if use_crawler else 3,
        crawler_max_depth=2 if use_crawler else 1,
        
        security={
            "allowed_domains": request.include_domains,
            "blocked_domains": request.exclude_domains
        }
    )
    
    # 2. Run Pipeline (AsyncPipeline is the new standard)
    from open_web_search import AsyncPipeline
    try:
        pipeline = AsyncPipeline(config)
        # Using context manager is safer if available, but for now standard usage:
        output = await pipeline.run(request.query)
    except Exception as e:
        logger.exception("Search failed")
        raise HTTPException(status_code=500, detail=str(e))
        
    # 3. Map Response to Tavily Schema
    tavily_results = []
    
    # Combine standard search results + evidence chunks
    # Note: Linker 'results' are just links, 'pages' are content. 
    # Tavily 'results' expects content snippets.
    # We use 'evidence' chunks as they are the most relevant parts.
    
    if output.evidence:
        # Use Refined Evidence
        for ev in output.evidence[:request.max_results]:
            tavily_results.append(TavilySearchResult(
                title=ev.title or "No Title",
                url=ev.url,
                content=ev.content,
                score=ev.relevance_score
            ))
    elif output.pages:
         # Fallback to pages
         for p in output.pages[:request.max_results]:
             tavily_results.append(TavilySearchResult(
                 title=p.title or "No Title",
                 url=p.url,
                 content=p.text_plain[:500] + "...",
                 score=0.5
             ))
             
    answer = output.answer if request.include_answer else None
    
    elapsed = time.time() - start_time
    
    return TavilyResponse(
        query=request.query,
        answer=answer,
        images=[], # TODO: Extract images
        results=tavily_results,
        follow_up_questions=[], # TODO: Planner could generate this
        response_time=elapsed
    )

@app.get("/health")
def health():
    return {"status": "ok", "service": "linker-search"}
