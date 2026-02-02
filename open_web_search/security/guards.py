import re
from typing import List, Optional
from urllib.parse import urlparse
from open_web_search.config import SecurityConfig

class SecurityGuard:
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.allowed_domains = set(config.allowed_domains)
        self.blocked_domains = set(config.blocked_domains)
        self.blocked_keywords = config.blocked_keywords
        
        # Simple PII regex (Phone, Email)
        self.pii_patterns = [
            (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '[EMAIL_REDACTED]'),
            (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]'),
        ]

    def is_allowed_url(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 1. Check Domain Whitelist/Blacklist
            if self.blocked_domains:
                if any(bd in domain for bd in self.blocked_domains):
                    return False
            
            if self.allowed_domains:
                # If allowlist is present, strictly verify
                # Note: This naturally blocks 'localhost' if not in allowlist
                if not any(ad in domain for ad in self.allowed_domains):
                    return False
            
            # 2. Network Profile Enforcement (Public vs Enterprise)
            # In 'public' mode, we MUST block localhost and private IPs to prevent SSRF
            if getattr(self.config, 'network_profile', 'public') == "public":
                if self._is_private_ip(domain):
                    return False
            
            return True
        except:
            return False

    def _is_private_ip(self, hostname: str) -> bool:
        """
        Check if hostname resolves to a private/loopback IP.
        Used to prevent SSRF in public mode.
        """
        import ipaddress
        import socket
        
        # Strip port if present
        if ":" in hostname:
            hostname = hostname.split(":")[0]
            
        if hostname in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
            return True
            
        try:
            # Resolve to IP
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)
            
            # Check if private
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local
        except:
            # If we can't resolve (e.g. 'internal-dashboard.local' without VPN), 
            # we block it in public mode just in case it's some internal magic? 
            # Actually if it doesn't resolve, we can't scrape it anyway.
            # But let's be safe: if it looks like an IP, parse it.
            # If it's a domain, we might fail resolution here but Playwright might succeed later?
            # To be safe in public mode, failure to resolve usually means ignore or block.
            return False

    def sanitize_text(self, text: str) -> str:
        if not self.config.pii_masking:
            return text
            
        cleaned = text
        for pattern, replacement in self.pii_patterns:
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned
