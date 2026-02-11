import unittest
from open_web_search.config import LinkerConfig, SecurityConfig
from open_web_search.security.guards import SecurityGuard

class TestEnterpriseMode(unittest.TestCase):
    def test_public_mode_blocks_private_ip(self):
        print("\n[Test] Public Mode (Default) vs Private IPs")
        config = LinkerConfig(
            security=SecurityConfig(network_profile="public")
        )
        guard = SecurityGuard(config.security)
        
        # Test Cases
        blocked = [
            "http://192.168.1.1",
            "http://127.0.0.1:8000",
            "http://localhost",
            "http://10.0.0.5"
        ]
        
        allowed = [
            "http://google.com",
            "http://8.8.8.8" 
        ]
        
        for url in blocked:
            is_allowed = guard.is_allowed_url(url)
            print(f"  Checking {url} -> Allowed? {is_allowed}")
            self.assertFalse(is_allowed, f"Public mode should BLOCK {url}")
            
        for url in allowed:
            is_allowed = guard.is_allowed_url(url)
            print(f"  Checking {url} -> Allowed? {is_allowed}")
            self.assertTrue(is_allowed, f"Public mode should ALLOW {url}")
            
    def test_enterprise_mode_allows_private_ip(self):
        print("\n[Test] Enterprise Mode vs Private IPs")
        config = LinkerConfig(
            security=SecurityConfig(network_profile="enterprise")
        )
        guard = SecurityGuard(config.security)
        
        # Test Cases (Should be ALLOWED now)
        target = "http://192.168.1.1"
        is_allowed = guard.is_allowed_url(target)
        print(f"  Checking {target} -> Allowed? {is_allowed}")
        self.assertTrue(is_allowed, f"Enterprise mode should ALLOW {target}")

    def test_custom_headers_propagation(self):
        print("\n[Test] Custom Headers Propagation")
        headers = {"Authorization": "Bearer SecretToken"}
        config = LinkerConfig(custom_headers=headers)
        
        # Check TrafilaturaReader
        from open_web_search.readers.trafilatura_reader import TrafilaturaReader
        reader = TrafilaturaReader(custom_headers=config.custom_headers)
        generated_headers = reader._get_headers()
        
        print(f"  Reader Headers: {generated_headers}")
        self.assertEqual(generated_headers.get("Authorization"), "Bearer SecretToken")
        self.assertIn("User-Agent", generated_headers)

if __name__ == "__main__":
    unittest.main()
