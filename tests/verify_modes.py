import unittest
from open_web_search.config import LinkerConfig

class TestConfigModes(unittest.TestCase):
    def test_fast_mode(self):
        print("\n[Test] Fast Mode Presets")
        config = LinkerConfig()
        config.set_mode("fast")
        
        self.assertEqual(config.mode, "fast")
        self.assertEqual(config.concurrency, 10, "Fast mode needs high concurrency")
        self.assertEqual(config.reader_timeout, 3, "Fast mode needs short timeout")
        self.assertFalse(config.enable_stealth_escalation, "Fast mode must disable Stealth")
        print("✅ Fast Mode Checked")

    def test_deep_mode(self):
        print("\n[Test] Deep Mode Presets")
        config = LinkerConfig()
        config.set_mode("deep")
        
        self.assertEqual(config.mode, "deep")
        self.assertEqual(config.reader_timeout, 30, "Deep mode needs long timeout")
        self.assertTrue(config.enable_stealth_escalation, "Deep mode must enable Stealth")
        self.assertEqual(config.crawler_max_depth, 2)
        print("✅ Deep Mode Checked")

if __name__ == "__main__":
    unittest.main()
