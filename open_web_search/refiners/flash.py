import torch
from typing import List
from loguru import logger
from open_web_search.schemas.results import FetchedPage, EvidenceChunk
from open_web_search.refiners.base import BaseRefiner
from open_web_search.refiners.keyword import KeywordRefiner
from open_web_search.config import LinkerConfig

class FlashRefiner(BaseRefiner):
    """
    FlashRanker: SLM/Cross-Encoder based Reranker (ADR 004).
    Replaces the lightweight Bi-Encoder with a heavier but more accurate Cross-Encoder.
    Designed for "Lazy Loading" to save resources when not used.
    """
    def __init__(self, config: LinkerConfig):
        self.config = config
        self.model = None
        self._is_loaded = False
        # Use KeywordRefiner for efficient chunking (min_relevance=0 to keep all chunks)
        self.chunker = KeywordRefiner(chunk_size=config.chunk_size, min_relevance=0.0)

    def _lazy_load(self):
        """
        Loads the Cross-Encoder model only on first use.
        """
        if self._is_loaded:
            return

        model_name = self.config.reranker_model
        logger.info(f"⚡ [FlashRanker] Lazy loading Cross-Encoder: {model_name}...")
        
        try:
            from sentence_transformers import CrossEncoder
            
            # Determine Device based on Config
            device = self.config.device
            
            if device == "auto":
                if torch.cuda.is_available():
                    device = "cuda"
                elif torch.backends.mps.is_available():
                    device = "mps"
                else:
                    device = "cpu"
            
            logger.info(f"⚡ [FlashRanker] Device Selected: {device} (Config: {self.config.device})")

            self.model = CrossEncoder(model_name, device=device, trust_remote_code=True)
            self._is_loaded = True
            logger.info("⚡ [FlashRanker] Model loaded successfully.")
            
        except ImportError as e:
            logger.error("❌ [FlashRanker] sentence-transformers not installed.")
            raise ImportError("Please install `sentence-transformers` to use FlashRanker.") from e
        except Exception as e:
            logger.error(f"❌ [FlashRanker] Failed to load model: {e}")
            raise e

    async def refine(self, pages: List[FetchedPage], query: str) -> List[EvidenceChunk]:
        """
        Reranks chunks using the Cross-Encoder.
        """
        # 1. Chunking Phase
        # We use KeywordRefiner to split pages into manageable chunks first
        # This handles the raw text -> chunks conversion
        all_chunks = await self.chunker.refine(pages, query)

        if not all_chunks:
            logger.warning("No chunks available for FlashRanker.")
            return []

        # 2. Lazy Load Model
        self._lazy_load()

        # 3. Prepare Pairs for Cross-Encoder [Query, Text]
        # CrossEncoder expects a list of tuples/lists: [[query, doc1], [query, doc2], ...]
        pairs = [[query, chunk.content] for chunk in all_chunks]
        
        # 4. Predict
        logger.info(f"⚡ [FlashRanker] Scoring {len(pairs)} chunks...")
        # Use batch_size to avoid OOM on large sets if needed, but default is usually fine for <100 chunks
        scores = self.model.predict(pairs)

        # 5. Assign Scores & Sort
        for chunk, score in zip(all_chunks, scores):
            chunk.relevance_score = float(score)

        # Sort descending
        ranked_chunks = sorted(all_chunks, key=lambda x: x.relevance_score, reverse=True)
        
        # 6. Filter Top K
        top_k = ranked_chunks[:self.config.max_evidence]
        
        # 7. Identify Smart Snippets (Context)
        # If score > 0.85 (Cross-Encoder is very confident), mark as answer
        for chunk in top_k:
            if chunk.relevance_score > 0.85:
                chunk.is_answer = True
                logger.info(f"⚡ [FlashRanker] Found High-Confidence Answer: {chunk.relevance_score:.4f}")
        
        if top_k:
            logger.info(f"⚡ [FlashRanker] Top chunk score: {top_k[0].relevance_score:.4f}")
            
        return top_k
