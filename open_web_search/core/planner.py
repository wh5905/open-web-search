from typing import List, Optional
import json
from loguru import logger
from openai import AsyncOpenAI
from open_web_search.config import LinkerConfig

class Planner:
    """
    LLM-based Planner that decomposes queries.
    """
    def __init__(self, config: LinkerConfig):
        self.config = config
        self.client = None
        if config.llm_base_url:
            self.client = AsyncOpenAI(
                base_url=config.llm_base_url,
                api_key=config.llm_api_key
            )
            print(f"DEBUG: LLMPlanner initialized with base_url: {config.llm_base_url}")
            logger.info(f"LLMPlanner initialized with base_url: {config.llm_base_url}")
        else:
            print(f"DEBUG: LLMPlanner: No llm_base_url provided. Config: {config.llm_base_url}")
            logger.warning("LLMPlanner: No llm_base_url provided. Falling back to passthrough.")

    async def _generate_queries(self, original_query: str, context: Optional[dict] = None) -> List[str]:
        if not self.client:
            return [original_query]
            
        system_prompt = (
            "You are an expert search query planner. "
            "Your goal is to decompose the user's complex question into 3 DISTINCT sub-queries "
            "that cover different ASPECTS of the topic.\n"
        )
        
        user_content = f"Question: {original_query}\n"
        
        # Adaptive Planning for Blocked Domains (Cognitive Unblocking)
        if context and "blocked_domains" in context and context["blocked_domains"]:
            blocked = ", ".join(context["blocked_domains"])
            system_prompt += (
                f"\nCRITICAL CONTEXT: The following domains are BLOCKED and cannot be accessed: {blocked}.\n"
                "You MUST generate 'Proxy Queries' to find information from alternative sources.\n"
                "Strategies:\n"
                "1. Search for summaries/discussions ON other platforms (e.g., 'site:medium.com summary of {blocked} thread')\n"
                "2. target aggregators or news sites that reference the blocked content.\n"
                "3. Use 'related:' or specific site operators for unblocked competitors.\n"
            )
            user_content += f"Constraints: Avoid {blocked}. Find alternatives.\n"
        else:
             system_prompt += (
                "Avoid synonyms. Each query must target a unique angle to maximize information coverage. "
             )
             
        system_prompt += "Return ONLY a JSON list of strings. Example: [\"query A\", \"query B\"]"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content + "Generate queries:"}
                ],
                temperature=0.3
            )
            content = response.choices[0].message.content
            # Basic parsing of list-like string
            # Try parsing JSON
            try:
                queries = json.loads(content)
                if isinstance(queries, list):
                    return [str(q) for q in queries]
            except:
                pass
                
            # Fallback parsing
            lines = [l.strip('- ').strip('"') for l in content.split('\n') if l.strip()]
            if lines:
                return lines
                
            return [original_query]
            
        except Exception as e:
            logger.error(f"LLM planning failed: {e}")
            return [original_query]

    async def plan(self, original_query: str, context: Optional[dict] = None) -> List[str]:
        if not self.client:
            return [original_query]
            
        queries = await self._generate_queries(original_query, context)
        logger.debug(f"Planner decomposed '{original_query}' -> {queries}")
        return queries
