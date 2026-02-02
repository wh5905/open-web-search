from typing import List, Optional
from loguru import logger
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.core.synthesizer import AnswerSynthesizer
from open_web_search.config import LinkerConfig
from open_web_search.schemas.results import PipelineOutput, EvidenceChunk

class DeepResearchLoop:
    """
    Orchestrates the research process: Plan -> Search -> Refine -> Synthesize.
    Now supports ADAPTIVE / ITERATIVE research (Phase 5 Complete).
    """
    def __init__(self, config: Optional[LinkerConfig] = None):
        self.config = config or LinkerConfig()
        self.pipeline = AsyncPipeline(self.config)
        self.synthesizer = AnswerSynthesizer(self.config)
        self.max_depth = 2 # Allow 1 follow-up round by default

    async def run(self, query: str) -> PipelineOutput:
        """
        Executes the full research loop with adaptive iteration.
        """
        logger.info(f"Starting Deep Research for: {query}")
        
        final_output = PipelineOutput(query=query)
        accumulated_evidence = []
        accumulated_blocked = set()
        
        current_depth = 0
        
        while current_depth < self.max_depth:
            current_depth += 1
            logger.info(f"--- Deep Research Round {current_depth} ---")
            
            # Prepare context for this round
            # blocked_domains are cumulative
            context = {
                "blocked_domains": list(accumulated_blocked)
            }
            
            # Run Pipeline
            output = await self.pipeline.run(query, context=context)
            
            # Accumulate Results
            accumulated_evidence.extend(output.evidence)
            if output.blocked_domains:
                for d in output.blocked_domains:
                    accumulated_blocked.add(d)
                logger.warning(f"Accumulated blocked domains: {accumulated_blocked}")
            
            # Merge into final output container
            final_output.results.extend(output.results)
            final_output.pages.extend(output.pages)
            
            # Enrich trace with queries
            round_trace = output.trace
            round_trace["rewritten_queries"] = output.rewritten_queries
            final_output.trace[f"round_{current_depth}"] = round_trace
            
            # Keep latest rewritten queries for visibility
            final_output.rewritten_queries = output.rewritten_queries 

            # Check Sufficiency
            # Heuristic: Do we have at least 3 strong chunks?
            strong_evidence = [c for c in accumulated_evidence if c.relevance_score > 0.4]
            logger.info(f"Round {current_depth} Stats: Total Evidence={len(accumulated_evidence)}, Strong={len(strong_evidence)}")
            
            if len(strong_evidence) >= 3:
                logger.info("Sufficient evidence found. Proceeding to synthesis.")
                break
                
            if current_depth >= self.max_depth:
                logger.info("Max depth reached. Proceeding to synthesis.")
                break
                
            logger.info(f"Evidence insufficient. Planning follow-up (avoiding {list(accumulated_blocked)})...")
            # The next iteration of pipeline.run will use the updated context

        # 3. Synthesize final answer
        final_output.evidence = accumulated_evidence
        if final_output.evidence:
             # Limit context window for synthesis (handled by synthesizer but good to clip here too)
            final_output.answer = await self.synthesizer.synthesize(final_output.query, final_output.evidence)
        else:
            final_output.answer = "No sufficient evidence found to answer the query."
        
        final_output.blocked_domains = list(accumulated_blocked)
        return final_output
