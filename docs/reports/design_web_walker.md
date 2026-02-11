# Design: The Neural Web Walker (Recursive Navigation)

## 1. Philosophy
Current RAG systems are "Snapshot Retrievers"—they grab the top K results and read them once.
A human researcher is a "Walker"—they land on a page, read it, realize they need more detail, find a relevant link ("API Reference", "See Migration Guide"), and click it.

To achieve "High Quality" research, `Open-Web-Search` must evolve from a **Retriever** to a **Navigator**.

## 2. Core Architecture: Best-First Search

We will implement a `NeuralCrawler` that uses local embeddings to decide where to go next.

### Algorithm: `Neural Best-First Search`
1. **Frontier**: A priority queue of `(Url, RelevanceScore)`.
2. **Context**: The original user query (embedded once).
3. **Loop**:
    - Pop the highest scoring URL.
    - Fetch & Extract content (Playwright).
    - **Accumulate** evidence.
    - **Harvest Links**: Extract all `<a>` tags with their anchor text and surrounding context.
    - **Score Links**: Calculate Cosine Similarity(`LinkText`, `UserQuery`) using `sentence-transformers`.
    - **Filter**: Keep links with `score > threshold`.
    - Push valid, unvisited links to Frontier.
    - Repeat until `max_pages` or `sufficient_evidence`.

## 3. Key Components

### 3.1 `LinkAnalyzer` (The Brain)
- **Role**: Judges if a link is worth following.
- **Mechanism**:
    - Fast Mode: Keyword overlap (BM25-style).
    - Deep Mode: Semantic Embedding (`all-MiniLM-L6-v2`).
- **Optimization**: Batch encode link texts for performance.

### 3.2 `PlaywrightReader` Upgrade (The Legs)
- Needs to be robust against "Navigation Storms".
- Must share the browser instance across the crawl session (persistent context).
- **Smart Extraction**: identify "Content Area" links vs "Footer/Nav" links. (Heuristic: link density).

### 3.3 `CrawlerStrategy` (The Controller)
- Manages the `visited` set (bloom filter or set).
- Handles `politeness` (time delays between hits to same domain).
- Prevents "Rabbit Holes" (max depth).

## 4. Class Structure

```python
class LinkCandidate:
    url: str
    text: str
    context: str
    score: float

class NeuralCrawler:
    def __init__(self, reader: PlaywrightReader, refiner: HybridRefiner):
        ...
    
    async def crawl(self, start_urls: List[str], query: str, max_pages: int = 5) -> List[FetchedPage]:
        # Implementation of Best-First Search
        ...
```

## 5. Why this is "High Level"
- **Local AI Integration**: It doesn't randomly crawl; it *thinks* about where to click.
- **Graph Traversal**: It builds a knowledge graph on the fly.
- **Efficiency**: It stops early if the "Information Gain" drops.

## 6. Integrations
- Adds a new method `agent.deep_dive(url)` to the `DeepResearchLoop`, allowing the agent to say "I need to explore this source further" rather than just "I read it".
