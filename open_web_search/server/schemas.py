from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field

class TavilyRequest(BaseModel):
    query: str
    search_depth: str = "basic" # basic, advanced
    topic: str = "general" # general, news
    max_results: int = 5
    include_images: bool = False
    include_answer: bool = False
    include_raw_content: bool = False
    include_domains: List[str] = []
    exclude_domains: List[str] = []
    
    # Extensions for Linker-Search
    use_neural_crawler: bool = False
    
    # v0.9.0 API Extensions
    mode: Optional[str] = None      # fast, balanced, deep
    reranker: Optional[str] = None  # fast, flash
    reader: Optional[str] = None    # trafilatura, browser
    max_evidence: Optional[int] = None

class TavilyImage(BaseModel):
    url: str
    description: Optional[str] = None

class TavilySearchResult(BaseModel):
    title: str
    url: str
    content: str
    raw_content: Optional[str] = None
    score: float = 0.0

class TavilyResponse(BaseModel):
    query: str
    answer: Optional[str] = None
    images: List[TavilyImage] = []
    results: List[TavilySearchResult] = []
    follow_up_questions: Optional[List[str]] = None
    response_time: float = 0.0
