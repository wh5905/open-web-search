from typing import List
import numpy as np
from loguru import logger
from open_web_search.refiners.base import BaseRefiner
from open_web_search.refiners.keyword import KeywordRefiner
from open_web_search.schemas.results import FetchedPage, EvidenceChunk
from open_web_search.security.authority import SourceAuthority

# Try importing sentence_transformers, graceful fallback if not installed
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class HybridRefiner(BaseRefiner):
    def __init__(self, chunk_size: int = 500, min_relevance: float = 0.1, model_name: str = "all-MiniLM-L6-v2"):
        self.keyword_refiner = KeywordRefiner(chunk_size=chunk_size, min_relevance=0.0) # Keyword used for chunking only mostly
        self.min_relevance = min_relevance
        self.authority = SourceAuthority()
        self.model = None
        
        if HAS_SENTENCE_TRANSFORMERS:
            try:
                logger.info(f"Loading semantic model: {model_name}")
                self.model = SentenceTransformer(model_name)
            except Exception as e:
                logger.error(f"Failed to load sentence-transformers: {e}")
        else:
            logger.warning("sentence-transformers not installed. HybridRefiner will degrade to KeywordRefiner.")

    async def refine(self, pages: List[FetchedPage], query: str) -> List[EvidenceChunk]:
        # 1. First use KeywordRefiner to chunk the text (reuse logic)
        # We set min_relevance=0 to get all chunks, then we re-score.
        base_chunks = await self.keyword_refiner.refine(pages, query)
        
        if not self.model or not base_chunks:
            # Fallback to pure keyword if no model or no chunks
            return [c for c in base_chunks if c.relevance_score >= 0.1] # Explicit threshold

        # --- OPTIMIZATION: Filter-First Strategy (LiteRanker) ---
        # Only semantically encode the top K chunks based on keyword score.
        # This saves massive CPU time on low-end hardware.
        PRE_FILTER_LIMIT = 20
        SAFETY_NET_COUNT = 5 # Keep first 5 chunks (Intro/Summary) regardless of score
        
        # 1. Selection Strategy
        # A. Top Keyword Matches (Best Guess)
        stats_sorted = sorted(base_chunks, key=lambda x: x.relevance_score, reverse=True)
        top_keyword_chunks = stats_sorted[:PRE_FILTER_LIMIT]
        
        # B. Safety Net (First few chunks usually contain abstract/intro)
        # This protects against "Synonym Blindness" where intro uses generic terms
        first_chunks = base_chunks[:SAFETY_NET_COUNT]
        
        # Merge and Deduplicate (preserving order of relevance)
        target_ids = set()
        target_chunks = []
        
        for c in top_keyword_chunks + first_chunks:
            if c.chunk_id not in target_ids:
                target_chunks.append(c)
                target_ids.add(c.chunk_id)

        # Cap at Limit (if merge exceeded it significantly, though usually it overlaps)
        # Actually, let's allow slightly more than limit if safety net adds new ones
        # to ensure we don't drop high-score ones. 
        # But for strict performance, let's just use the merged list (max 25 chunks).
        
        logger.debug(f"HybridRefiner: Optimized {len(base_chunks)} -> {len(target_chunks)} chunks (w/ Safety Net).")
        
        if not target_chunks:
            return []

        # 2. Semantic Scoring
        chunk_texts = [c.content for c in target_chunks]
        
        try:
            # Encode query and chunks
            query_embedding = self.model.encode(query)
            chunk_embeddings = self.model.encode(chunk_texts)
            
            # Cosine similarity
            # (1, D) . (N, D).T = (1, N)
            scores = np.dot(chunk_embeddings, query_embedding) / (
                np.linalg.norm(chunk_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )
            
            # 3. Combine Scores (Hybrid)
            # Simple average: 0.3 * keyword_score + 0.7 * semantic_score
            combined_scores = []
            
            for i, chunk in enumerate(target_chunks):
                semantic = float(scores[i])
                keyword = chunk.relevance_score # Already normalized 0-1
                
                # Boost keyword slightly to ensure exact matches are valued
                raw_score = (0.3 * keyword) + (0.7 * semantic)
                
                # Apply Authority Boost/Penalty
                auth_score = self.authority.get_score(chunk.url)
                final_score = raw_score * (1 + (auth_score - 0.5))
                
                chunk.relevance_score = min(max(final_score, 0.0), 1.0)
                combined_scores.append(final_score)

            # 4. MMR Selection (Diversity Enforcement)
            # We want to select chunks that are high relevance but low similarity to already selected chunks.
            
            selected_indices = []
            candidate_indices = list(range(len(target_chunks)))
            
            source_counts = {} # limit max chunks per URL
            MAX_PER_SOURCE = 3
            TARGET_COUNT = 15 # select top 15 diverse chunks
            
            # MMR Hyperparameter (0.7 = prefer relevance, 0.3 = prefer diversity)
            LAMBDA = 0.7 
            
            while len(selected_indices) < TARGET_COUNT and candidate_indices:
                best_mmr = -1.0
                best_idx = -1
                
                for idx in candidate_indices:
                    # Check source cap
                    url = target_chunks[idx].url
                    if source_counts.get(url, 0) >= MAX_PER_SOURCE:
                        continue

                    # Relevance part
                    relevance = combined_scores[idx]
                    
                    # Diversity part
                    if not selected_indices:
                        diversity = 0.0
                    else:
                        # Similarity to already selected
                        # We need the embedding for current chunk (idx) and selected chunks
                        # cosine sim is (A . B) / (|A|*|B|)
                        # Pre-calculated in chunk_embeddings
                        
                        # Get embedding for current candidate
                        cand_emb = chunk_embeddings[idx]
                        
                        # Get embeddings for selected
                        sel_embs = chunk_embeddings[selected_indices]
                        
                        # Compute max similarity to any selected chunk
                        sims = np.dot(sel_embs, cand_emb) / (
                            np.linalg.norm(sel_embs, axis=1) * np.linalg.norm(cand_emb)
                        )
                        diversity = np.max(sims)
                    
                    # MMR Score
                    mmr = (LAMBDA * relevance) - ((1 - LAMBDA) * diversity)
                    
                    if mmr > best_mmr:
                        best_mmr = mmr
                        best_idx = idx
                
                # If we found a valid candidate
                if best_idx != -1:
                    selected_indices.append(best_idx)
                    candidate_indices.remove(best_idx)
                    
                    url = target_chunks[best_idx].url
                    source_counts[url] = source_counts.get(url, 0) + 1
                else:
                    # No more valid candidates (e.g. all hit source caps)
                    break 
            
            return [target_chunks[i] for i in selected_indices]
            
        except Exception as e:
            logger.error(f"Semantic refinement failed: {e}")
            return base_chunks # Fallback to keyword sort if semantic fails
