from .config import LinkerConfig, SecurityConfig
from .core.pipeline import AsyncPipeline
from .core.loop import DeepResearchLoop
from .schemas.results import PipelineOutput

__version__ = "0.7.0"
__all__ = ["LinkerConfig", "SecurityConfig", "AsyncPipeline", "DeepResearchLoop", "search"]

# Global singleton for Level 1/2
_default_pipeline = None

async def search(query: str, mode: str = "balanced", **kwargs) -> PipelineOutput:
    """
    One-shot search function.
    Manages a global pipeline instance lazily.
    """
    global _default_pipeline
    
    # If kwargs exist, we might need a temporary config or update the global one.
    # For simplicity in v1: Create ephemeral pipeline if custom config needed, 
    # or reuse global if standard.
    
    if kwargs:
        # Custom run (Level 2)
        cfg = LinkerConfig(mode=mode, **kwargs)
        # Verify if we need to close this pipeline after use? 
        # AsyncPipeline usually doesn't hold heavy persistent resources except HTTP client.
        # But let's be safe and context manage it if possible, or just run it.
        # AsyncPipeline doesn't utilize __aenter__ yet in code I saw, but let's check.
        # The code in pipeline.py has a close() method.
        pipeline = AsyncPipeline(cfg)
        try:
            return await pipeline.run(query)
        finally:
            if hasattr(pipeline, 'close'): # Graceful check
                 await pipeline.close()

    # Default run (Level 1)
    if not _default_pipeline:
        _default_pipeline = AsyncPipeline(LinkerConfig(mode=mode))
        
    return await _default_pipeline.run(query)
