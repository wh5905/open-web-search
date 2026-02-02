import asyncio
from typing import List, Optional
from loguru import logger
from open_web_search.engines.base import BaseSearchEngine
from open_web_search.schemas.results import SearchResult

class CompositeSearchEngine(BaseSearchEngine):
    """
    The 'Hydra' Engine: Manages a priority list of search engines.
    If the primary engine fails (or returns suspiciously empty results),
    it automatically fails over to the next engine in the chain.
    """
    def __init__(self, engines: List[BaseSearchEngine]):
        self.engines = engines
        if not self.engines:
            raise ValueError("CompositeSearchEngine requires at least one engine.")

    async def search(self, queries: List[str]) -> List[SearchResult]:
        if not queries:
            return []

        errors = []
        
        # Try each engine in priority order
        for i, engine in enumerate(self.engines):
            engine_name = engine.__class__.__name__
            logger.info(f"Composite: Attempting search with {engine_name} (Priority {i+1})")
            
            try:
                results = await engine.search(queries)
                
                # Success criteria checks
                if results:
                    logger.info(f"Composite: {engine_name} succeeded with {len(results)} results.")
                    return results
                else:
                    logger.warning(f"Composite: {engine_name} returned 0 results. Warning signal.")
                    # If it's the last engine, return empty. 
                    # If not, treat as soft failure and try next?
                    # Strategy: If result is empty, it MIGHT be a query issue or a soft block.
                    # Let's try the next engine just in case, unless it's a specific 'not found' confidence?
                    # For now, let's treat 0 results as a "Try Next" signal if fallback exists.
                    if i < len(self.engines) - 1:
                        logger.info(f"Composite: Falling back from {engine_name} due to empty results...")
                        continue
                    else:
                        return [] # All empty
            
            except Exception as e:
                logger.error(f"Composite: {engine_name} failed: {e}")
                errors.append(f"{engine_name}: {str(e)}")
                
                # If last engine, raise or return empty?
                # Best to return empty list with error logged, to prevent pipeline crash.
                if i < len(self.engines) - 1:
                    logger.warning(f"Composite: Failing over to next engine...")
                    continue
        
        logger.error(f"Composite: All engines failed. Errors: {errors}")
        return []
