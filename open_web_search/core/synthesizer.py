from typing import List, Optional
import os
from openai import AsyncOpenAI
from open_web_search.schemas.results import EvidenceChunk
from open_web_search.config import LinkerConfig

class AnswerSynthesizer:
    """
    Synthesizes a final answer from search evidence using an LLM.
    """
    def __init__(self, config: LinkerConfig):
        self.config = config
        self.client = None
        if config.llm_base_url:
            self.client = AsyncOpenAI(
                base_url=config.llm_base_url,
                api_key=config.llm_api_key
            )
        
    async def synthesize(self, query: str, evidence: List[EvidenceChunk]) -> str:
        """
        Generates an answer based on the provided evidence.
        """
        if not self.client:
            return "LLM not configured. Unable to synthesize answer."

        if not evidence:
            return "No evidence found to answer the query."

        # Dynamic Context Management (v0.5 Adaptive)
        # Calculates token budget and fits as many chunks as possible
        
        # Estimate prompt overhead (system + user template) ~200 chars
        prompt_overhead_chars = 500 
        
        # Heuristic: 1 token ~= 4 chars (Conservative for Korean/Code)
        # We target characters directly for simplicity and speed
        max_chars = self.config.max_context_tokens * 3 
        available_chars = max_chars - prompt_overhead_chars
        
        context_text = ""
        current_chars = 0
        used_count = 0
        
        for i, chunk in enumerate(evidence):
            # Format: Source [N] (URL):\nCONTENT\n\n
            chunk_fmt = f"Source [{i+1}] ({chunk.url}):\n{chunk.content}\n\n"
            chunk_len = len(chunk_fmt)
            
            if current_chars + chunk_len > available_chars:
                # If even one chunk is too big, try to truncate it or just stop
                if used_count == 0:
                     # Must include at least partial first chunk
                     safe_len = available_chars - 100
                     if safe_len > 100:
                         truncated_content = chunk.content[:safe_len] + "...(truncated)"
                         context_text += f"Source [{i+1}] ({chunk.url}):\n{truncated_content}\n\n"
                         used_count += 1
                break
            
            context_text += chunk_fmt
            current_chars += chunk_len
            used_count += 1
            
            if used_count >= self.config.max_evidence:
                break

        system_prompt = (
            "You are a helpful research assistant. "
            "Your task is to answer the user's query using ONLY the provided context. "
            "Cite your sources using [1], [2] notation corresponding to the source numbers provided. "
            "If the context is insufficient, state that clearly."
        )

        user_prompt = f"Query: {query}\n\nContext:\n{context_text}\n\nAnswer:"

        try:
            response = await self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            return response.choices[0].message.content or "Error: Empty response from LLM."
        except Exception as e:
            return f"Error synthesizing answer: {str(e)}"
