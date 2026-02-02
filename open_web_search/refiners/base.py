from abc import ABC, abstractmethod
from typing import List
from open_web_search.schemas.results import FetchedPage, EvidenceChunk

class BaseRefiner(ABC):
    @abstractmethod
    async def refine(self, pages: List[FetchedPage], query: str) -> List[EvidenceChunk]:
        pass
