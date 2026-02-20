from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field

class SecurityConfig(BaseModel):
    allowed_domains: List[str] = Field(default_factory=list)
    blocked_domains: List[str] = Field(default_factory=list)
    blocked_keywords: List[str] = Field(default_factory=list)
    pii_masking: bool = False
    ssl_verify: Union[bool, str] = True
    proxy: Optional[str] = None
    network_profile: Literal["public", "enterprise"] = "public"

class LinkerConfig(BaseModel):
    mode: Literal["turbo", "fast", "balanced", "deep"] = "deep"
    
    # Engine Settings
    engine_provider: Literal["ddg", "google_cse", "searxng"] = "ddg"
    engine_api_key: Optional[str] = None
    engine_base_url: Optional[str] = "http://localhost:8787"  # Default to local SearXNG
    
    # LLM Settings (For Planner/Synthesizer)
    llm_base_url: Optional[str] = None
    llm_api_key: str = "EMPTY"
    llm_model: str = "gpt-3.5-turbo" # Or local model name
    
    # Reader Settings
    reader_type: Literal["trafilatura", "browser"] = "trafilatura"
    reader_timeout: int = 10
    reader_max_pages: int = 5
    reader_user_agent: str = "LinkerSearch/0.1"
    
    # Crawler Settings (The Web Walker)
    use_neural_crawler: bool = False
    crawler_max_depth: int = 1
    crawler_max_pages: int = 3

    # Search Settings
    search_language: str = "auto"  # 'auto' (defaults to 'us-en'), 'en-US', 'ko-KR', etc.
    
    # Refiner Settings
    chunk_size: int = 1000
    chunk_overlap: int = 100
    max_evidence: int = 5 # Reduced to fit 4k-8k context models
    max_context_tokens: int = 6000 # Strict limit for local LLM (v0.5 Adaptive)
    min_relevance: float = 0.01 # Lowered to accept Search Snippets (v0.5 Universality)
    enable_snippet_fallback: bool = True # Toggle for comparison experiments
    enable_stealth_escalation: bool = True # Try Playwright if Trafilatura fails

    # FlashRanker Settings (ADR 004)
    reranker_type: Literal["fast", "flash"] = "fast" # 'fast'=Bi-Encoder, 'flash'=Cross-Encoder/SLM
    reranker_model: str = "BAAI/bge-reranker-v2-m3" # Default Flash model
    device: Literal["auto", "cpu", "cuda", "mps"] = "auto" # Inference Device

    # Enterprise Settings (Phase 17)
    custom_headers: dict = Field(default_factory=dict) # Cookie, Authorization, etc.
    
    # Runtime
    concurrency: int = 5
    max_retries: int = 2
    cache_ttl: int = 3600 # 1 hour
    cache_dir: str = ".linker_cache"

    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    observability_level: Literal["basic", "full"] = "basic"

    def set_mode(self, mode: Literal["turbo", "fast", "balanced", "deep"]):
        """
        Applies preset configurations for the selected mode.
        """
        self.mode = mode
        if mode == "turbo":
            # Zero-Fetch Mode: Snippet Synthesis Only (< 0.8s goal)
            self.concurrency = 10
            self.reader_timeout = 1
            self.enable_stealth_escalation = False 
            self.reranker_type = "fast" 
            self.max_evidence = 3
            self.chunk_size = 500
            
        elif mode == "fast":
            # Fast Mode: Low Latency (< 2s goal)
            self.concurrency = 10
            self.reader_timeout = 3
            self.enable_stealth_escalation = False # Disable slow Playwright
            self.reranker_type = "fast" # Use Bi-Encoder
            self.max_evidence = 3
            self.chunk_size = 500 # Faster processing
            
        elif mode == "balanced":
            # Default: Good mix of speed and robustness (< 5s goal)
            self.concurrency = 5
            self.reader_timeout = 10
            self.enable_stealth_escalation = True # Enable Fallback
            self.reranker_type = "fast" # Use Bi-Encoder for speed
            self.max_evidence = 5
            self.chunk_size = 1000
            self.enable_snippet_fallback = True

        elif mode == "deep":
            # Researcher: Quality above all (> 10s allowed)
            self.concurrency = 3 # Be polite to servers
            self.reader_timeout = 30
            self.enable_stealth_escalation = True # Aggressive recovery
            self.reranker_type = "flash" # Use Cross-Encoder (FlashRanker)
            self.max_evidence = 10
            self.chunk_size = 2000
            self.crawler_max_depth = 2 # Enable recursive crawling
            self.enable_snippet_fallback = True # Salvage snippets if strictly blocked
            
        # Try to upgrade to SearXNG if available (Smart Auto-Detect)
        self._auto_detect_engine()

    def _auto_detect_engine(self):
        """
        Smartly detects if SearXNG is running locally and upgrades the engine.
        """
        # Only auto-detect if user hasn't explicitly set a remote engine or API key
        if self.engine_provider != "ddg" and self.engine_api_key:
            return

        import socket
        
        # Common SearXNG ports
        potential_urls = [
            ("http://localhost:8787", 8787),
            ("http://localhost:8080", 8080),
            ("http://localhost:8888", 8888)
        ]
        
        from loguru import logger
        
        for url, port in potential_urls:
            try:
                # Fast socket check (timeout 0.1s)
                with socket.create_connection(("localhost", port), timeout=0.1):
                    self.engine_provider = "searxng"
                    self.engine_base_url = url
                    logger.info(f"🚀 [LinkerConfig] SearXNG detected at {url}. Upgrading engine provider!")
                    return
            except (socket.timeout, ConnectionRefusedError, OSError):
                continue
        
        # If we reached here, SearXNG was not found.
        # Quietly log a tip if we are in deep mode (where it matters most)
        if self.mode == "deep":
            logger.info("💡 [Tip] For better results, run SearXNG locally: 'docker run -d -p 8787:8080 searxng/searxng'")
