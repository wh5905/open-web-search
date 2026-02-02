import torch
from typing import List
from loguru import logger
from open_web_search.schemas.results import FetchedPage, EvidenceChunk
from open_web_search.refiners.base import BaseRefiner
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
        self.tokenizer = None
        self._is_loaded = False

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
            
            # Use GPU if available, else CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.debug(f"⚡ [FlashRanker] Device: {device}")

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
        # 1. Collect all chunks from pages
        all_chunks = []
        for p in pages:
            # If pages have chunks already (pre-split), use them
            # Otherwise we might need to split here. 
            # Assuming pages come with chunks from the Reader phase or previous Refiner phase.
            # But BaseRefiner usually takes raw pages. 
            # Let's assume we need to split if not split.
            # For now, let's assume the 'HybridRefiner' logic of splitting first.
            if hasattr(p, 'chunks') and p.chunks:
                all_chunks.extend(p.chunks)
            else:
                # Basic splitting fallback if needed, or assume empty
                pass

        if not all_chunks:
            logger.warning("No chunks available for FlashRanker.")
            return []

        # 2. Lazy Load Model
        self._lazy_load()

        # 3. Prepare Pairs for Cross-Encoder [Query, Text]
        pairs = [[query, chunk.content] for chunk in all_chunks]
        
        # 4. Predict
        logger.info(f"⚡ [FlashRanker] Scoring {len(pairs)} chunks...")
        scores = self.model.predict(pairs)

        # 5. Assign Scores & Sort
        for chunk, score in zip(all_chunks, scores):
            chunk.relevance_score = float(score)

        # Sort descending
        ranked_chunks = sorted(all_chunks, key=lambda x: x.relevance_score, reverse=True)
        
        # 6. Filter Top K
        top_k = ranked_chunks[:self.config.max_evidence]
        
        logger.info(f"⚡ [FlashRanker] Top chunk score: {top_k[0].relevance_score if top_k else 0:.4f}")
        return top_k
