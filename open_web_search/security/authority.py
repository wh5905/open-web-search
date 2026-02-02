from typing import List, Dict, Optional
from urllib.parse import urlparse

class SourceAuthority:
    """
    Evaluates the authority and credibility of sources.
    """
    
    HIGH_AUTHORITY_DOMAINS = {
        "wikipedia.org", "arxiv.org", "nih.gov", "nasa.gov", "reuters.com",
        "bloomberg.com", "nytimes.com", "wsj.com", "bbc.com", "nature.com",
        "sciencemag.org", "ieee.org", "acm.org", "github.com", "stackoverflow.com",
        "python.org", "mozilla.org"
    }
    
    LOW_AUTHORITY_MARKERS = [
        "best-", "top10", "review-", "coupon", "promo", "affiliate", "scam"
    ]

    def __init__(self):
        pass

    def get_score(self, url: str) -> float:
        """
        Returns a score between 0.0 and 1.0 for the domain.
        - 1.0: High Authority (Whitelisted)
        - 0.5: Neutral (Unknown)
        - 0.1: Low Authority (Spam markers)
        """
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            
            # Check for high authority
            if domain in self.HIGH_AUTHORITY_DOMAINS:
                return 1.0
            for auth_domain in self.HIGH_AUTHORITY_DOMAINS:
                 if domain.endswith("." + auth_domain): # Subdomains of trusted
                     return 0.9

            # Check for low authority markers in domain
            for marker in self.LOW_AUTHORITY_MARKERS:
                if marker in domain:
                    return 0.2
            
            return 0.5 # Default neutral score
            
        except Exception:
            return 0.5
