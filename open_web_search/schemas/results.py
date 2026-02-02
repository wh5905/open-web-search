from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None
    score: Optional[float] = None
    source_engine: str
    rank: Optional[int] = None
    published_at: Optional[datetime] = None
    raw: Optional[Dict[str, Any]] = None

class FetchedPage(BaseModel):
    url: str
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: Optional[str] = None
    text_markdown: Optional[str] = None
    text_plain: Optional[str] = None
    language: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class EvidenceChunk(BaseModel):
    url: str
    chunk_id: str
    content: str
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    relevance_score: float
    title: Optional[str] = None

class PipelineOutput(BaseModel):
    query: str
    rewritten_queries: List[str] = Field(default_factory=list)
    results: List[SearchResult] = Field(default_factory=list)
    pages: List[FetchedPage] = Field(default_factory=list)
    evidence: List[EvidenceChunk] = Field(default_factory=list)
    elapsed_ms: int = 0
    warnings: List[str] = Field(default_factory=list)
    trace: Dict[str, Any] = Field(default_factory=dict)
    blocked_domains: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
