from typing import List, Dict, Optional
import numpy as np
from loguru import logger
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

@dataclass
class LinkCandidate:
    url: str
    text: str
    context: str = ""
    score: float = 0.0

class LinkAnalyzer:
    """
    Evaluates the relevance of hyperlinks to a given research query.
    Uses semantic similarity (SentenceTransformers) if available, 
    otherwise falls back to keyword matching.
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = None
        self.model_name = model_name
        self._load_model()

    def _load_model(self):
        if HAS_SENTENCE_TRANSFORMERS and not self.model:
            try:
                logger.info(f"Loading LinkAnalyzer model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")

    def score_links(self, links: List[LinkCandidate], query: str) -> List[LinkCandidate]:
        """
        Scores a list of links against the query.
        Returns the list sorted by score (descending).
        """
        if not links:
            return []

        # 1. Semantic Scoring (High Quality)
        if self.model:
            # Prepare texts: "Link Text [SEP] Surrounding Context"
            # Context is powerful for ambiguous links like "Click here"
            texts = [f"{link.text} {link.context}".strip() for link in links]
            
            # Embed query and candidates
            # Normalize to enable dot product as cosine similarity
            query_emb = self.model.encode(query, normalize_embeddings=True)
            link_embs = self.model.encode(texts, normalize_embeddings=True)
            
            # Compute scores (Dot product)
            # query_emb: (dim,) link_embs: (N, dim) -> (N,)
            scores = np.dot(link_embs, query_emb)
            
            for i, link in enumerate(links):
                link.score = float(scores[i])

        # 2. Keyword Fallback (Fast / Low Res)
        else:
            query_terms = set(query.lower().split())
            for link in links:
                text_lower = (link.text + " " + link.context).lower()
                # Simple Jaccard-ish overlap
                match_count = sum(1 for term in query_terms if term in text_lower)
                link.score = match_count / len(query_terms) if query_terms else 0.0

        # Sort desc
        links.sort(key=lambda x: x.score, reverse=True)
        return links
