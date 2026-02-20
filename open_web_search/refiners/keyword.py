import hashlib
from typing import List
from open_web_search.refiners.base import BaseRefiner
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

class BM25:
    """Lightweight, offline BM25 implementation for Python."""
    def __init__(self, corpus_tokens: List[List[str]]):
        import math
        from collections import Counter
        
        self.corpus_size = len(corpus_tokens)
        self.avgdl = sum(len(doc) for doc in corpus_tokens) / self.corpus_size if self.corpus_size else 0
        self.doc_freqs = []
        self.idf = {}
        self.doc_len = []
        
        # BM25 Hyperparameters (Standard defaults)
        self.k1 = 1.5
        self.b = 0.75
        
        # Build index
        nd = {}  # word -> number of documents containing it
        for doc in corpus_tokens:
            self.doc_len.append(len(doc))
            frequencies = Counter(doc)
            self.doc_freqs.append(frequencies)
            for word in frequencies:
                nd[word] = nd.get(word, 0) + 1
                
        # Calculate IDF
        for word, freq in nd.items():
            idf_score = math.log(((self.corpus_size - freq + 0.5) / (freq + 0.5)) + 1.0)
            self.idf[word] = idf_score

    def get_score(self, query_tokens: List[str], doc_index: int) -> float:
        score = 0.0
        doc_len = self.doc_len[doc_index]
        frequencies = self.doc_freqs[doc_index]
        
        for word in query_tokens:
            if word not in frequencies:
                continue
            tf = frequencies[word]
            idf = self.idf.get(word, 0)
            
            # TF scaling
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
            score += idf * (numerator / denominator)
            
        return score

class KeywordRefiner(BaseRefiner):
    def __init__(self, chunk_size: int = 500, min_relevance: float = 0.1):
        self.chunk_size = chunk_size
        self.min_relevance = min_relevance
        # Stop words to ignore during tokenization
        self.stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'current', 'latest', 'recent', 'it', 'this', 'that'}

    def _tokenize(self, text: str) -> List[str]:
        # Simple fast tokenization
        import re
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in self.stop_words and len(w) > 1]

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

    async def refine(self, pages: List[FetchedPage], query: str) -> List[EvidenceChunk]:
        evidence = []
        query_tokens = self._tokenize(query)
        
        if not query_tokens:
            return evidence # Edge case: query was just stop words
            
        # 1. Gather all chunks across all pages to build Corpus
        all_chunks_info = [] # (page_url, page_title, chunk_text)
        corpus_tokens = []
        
        for page in pages:
            if not page.text_plain:
                continue
            
            chunks = self._simple_chunk(page.text_plain)
            for chunk_text in chunks:
                all_chunks_info.append((page.url, page.title, chunk_text))
                corpus_tokens.append(self._tokenize(chunk_text))
                
        if not corpus_tokens:
            return evidence
            
        # 2. Build BM25 Index
        bm25 = BM25(corpus_tokens)
        
        # 3. Score against query
        max_score = 0.0
        raw_results = []
        
        for idx, (url, title, chunk_text) in enumerate(all_chunks_info):
            score = bm25.get_score(query_tokens, idx)
            if score > max_score: max_score = score
            
            raw_results.append({
                "url": url,
                "title": title,
                "content": chunk_text,
                "score": score,
                "idx": idx
            })
            
        # 4. Normalize scores to [0, 1] range to match BaseRefiner expectations
        # (HybridRefiner expects min_relevance scaling)
        for r in raw_results:
            normalized = (r["score"] / max_score) if max_score > 0 else 0.0
            if normalized >= self.min_relevance:
                 chunk_id = hashlib.md5(f'{r["url"]}_{r["idx"]}'.encode()).hexdigest()
                 evidence.append(EvidenceChunk(
                     url=r["url"],
                     chunk_id=chunk_id,
                     content=r["content"],
                     relevance_score=normalized,
                     title=r["title"]
                 ))
                 
        # Sort by score desc
        evidence.sort(key=lambda x: x.relevance_score, reverse=True)
        return evidence
