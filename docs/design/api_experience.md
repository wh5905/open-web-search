# Open-Web-Search: API Experience (DX) Design

## 1. Design Philosophy
We aim to serve two distinct user personas:
1.  **The Pragmatist**: "I just want search results in my agent. Don't make me read docs."
2.  **The Architect**: "I need to inject a custom ChromaDB retriever and swap the LLM for Llama-3."

To achieve this, we propose a **4-Tier API Surface**.

---

## 2. API Tiers

### Level 1: The "It Just Works" (Zero-Config)
**Target**: Beginners, Hackathons, Quick Scripts.
**Usage**: Simple function call. No classes, no config objects.

```python
import open_web_search as ows

# Defaults to 'balanced' mode
results = await ows.search("Who is the CEO of OpenAI?")
print(results.answer)
```

### Level 2: The "Tweaker" (Parameter Override)
**Target**: Application developers who need specific behaviors but don't want boilerplate.
**Usage**: Pass common params as kwargs.

```python
# "I need a deep research report on this topic"
results = await ows.search(
    "Future of Quantum Computing", 
    mode="deep", 
    reranker="flash",   # Enable FlashRanker
    headless=True       # Ensure browser is stealthy
)
```

### Level 3: The "Power User" (Object-Oriented)
**Target**: Production apps, long-running services (FastAPI), stateful agents.
**Usage**: Explicit `LinkerConfig` and `AsyncPipeline` management.

```python
from open_web_search import AsyncPipeline, LinkerConfig

# reused across requests
config = LinkerConfig(
    mode="fast",
    reranker_type="flash",
    reader_type="browser",
    openai_api_key="sk-..." 
)

pipeline = AsyncPipeline(config)

# Request 1
res1 = await pipeline.run("Query 1")
# Request 2 (reuses connections/models)
res2 = await pipeline.run("Query 2")
```

### Level 4: The "Architect" (Dependency Injection)
**Target**: Framework builders, Researchers replacing core modules.
**Usage**: Compose the pipeline manually.

```python
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.engines import CustomSearxNG
from open_web_search.refiners import MyCustomReranker

# Inject custom components
pipeline = AsyncPipeline()
pipeline.engine = CustomSearxNG(url="http://my-private-instance")
pipeline.refiner = MyCustomReranker(model="gpt-4")

results = await pipeline.run("Query")
```

---

## 3. Implementation Strategy (v0.8.0)

To support Level 1 & 2, we need to add a convenience wrapper in `__init__.py`.

### Proposed `__init__.py`

```python
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
        # Custom run
        cfg = LinkerConfig(mode=mode, **kwargs)
        async with AsyncPipeline(cfg) as pipe:
            return await pipe.run(query)
            
    # Default run
    if not _default_pipeline:
        _default_pipeline = AsyncPipeline(LinkerConfig(mode=mode))
        
    return await _default_pipeline.run(query)
```

## 4. Why this matters?
- **Retention**: Users drop off if they have to import 3 classes to do a "Hello World".
- **Scalability**: We don't block power users from accessing the guts of the system.
- **Pythonic**: Use functions for actions, objects for state.
