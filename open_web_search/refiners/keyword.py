import hashlib
from typing import List
from open_web_search.refiners.base import BaseRefiner
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

class KeywordRefiner(BaseRefiner):
    def __init__(self, chunk_size: int = 500, min_relevance: float = 0.1):
        self.chunk_size = chunk_size
        self.min_relevance = min_relevance

    def _simple_chunk(self, text: str) -> List[str]:
        # Improved chunking: split by paragraphs, then sentences if too large
        paragraphs = text.split('\n\n')
        if len(paragraphs) == 1:
            paragraphs = text.split('\n')
            
        chunks = []
        current_chunk = []
        current_len = 0
        
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
                
            # If a single paragraph is huge, split it by sentence
            if len(p) > self.chunk_size:
                # Flush current
                if current_chunk:
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                # Split huge para
                sentences = p.replace(". ", ".\n").split('\n')
                for s in sentences:
                    if len(s) > self.chunk_size:
                        # Hard chop if sentence is still huge
                        for i in range(0, len(s), self.chunk_size):
                             chunks.append(s[i:i+self.chunk_size])
                    else:
                        if current_len + len(s) > self.chunk_size:
                             chunks.append("\n".join(current_chunk))
                             current_chunk = [s]
                             current_len = len(s)
                        else:
                             current_chunk.append(s)
                             current_len += len(s)
            
            # Normal paragraph handling
            elif current_len + len(p) > self.chunk_size:
                chunks.append("\n".join(current_chunk))
                current_chunk = [p]
                current_len = len(p)
            else:
                current_chunk.append(p)
                current_len += len(p)
        
        if current_chunk:
            chunks.append("\n".join(current_chunk))
            
        return chunks

    def _score_chunk(self, chunk: str, query_terms: List[str]) -> float:
        text_lower = chunk.lower()
        score = 0.0
        match_count = 0
        
        # Stop words to ignore (simple list)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'current', 'latest', 'recent'}
        
        valid_terms = [t for t in query_terms if t not in stop_words and len(t) > 2]
        
        if not valid_terms:
            # If all terms were stop words, fall back to original
            valid_terms = query_terms
            
        for term in valid_terms:
            if term in text_lower:
                score += 1.0
                match_count += 1
        
        # Boost if multiple different terms are present
        coverage = match_count / len(valid_terms) if valid_terms else 0
        
        # Final score is mix of term frequency (implied) and coverage
        # But here we just count existence. 
        # Let's boost meaningful terms.
        
        return coverage # Returns 0.0 to 1.0 representing "how many of the query terms are in this chunk"

    async def refine(self, pages: List[FetchedPage], query: str) -> List[EvidenceChunk]:
        evidence = []
        query_terms = [t.lower() for t in query.split() if len(t) > 2]
        
        for page in pages:
            if not page.text_plain:
                continue
            
            chunks = self._simple_chunk(page.text_plain)
            for idx, chunk_text in enumerate(chunks):
                score = self._score_chunk(chunk_text, query_terms)
                
                if score >= self.min_relevance:
                    chunk_id = hashlib.md5(f"{page.url}_{idx}".encode()).hexdigest()
                    evidence.append(EvidenceChunk(
                        url=page.url,
                        chunk_id=chunk_id,
                        content=chunk_text,
                        relevance_score=score,
                        title=page.title
                    ))
        
        # Sort by score desc
        evidence.sort(key=lambda x: x.relevance_score, reverse=True)
        return evidence
