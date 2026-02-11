import sys
from pathlib import Path
from dotenv import load_dotenv
import os

print("🔍 Starting Verification...")

# 1. Path Check
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
print(f"📂 Resolved Root: {PROJECT_ROOT}")

if (PROJECT_ROOT / "open_web_search").exists():
    print("✅ Root seems correct (found open_web_search package)")
else:
    print("❌ Root seems WRONG!")

# 2. Import Check
sys.path.append(str(PROJECT_ROOT))
try:
    import open_web_search
    print(f"✅ Import Successful: {open_web_search}")
except ImportError as e:
    print(f"❌ Import Failed: {e}")

# 3. Env Check
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    load_dotenv(env_path)
    # Check for a known key if possible, or just report success
    print("✅ .env found and loaded")
    # print(f"DEBUG: LLM_BASE_URL={os.getenv('LLM_BASE_URL')}") 
else:
    print("❌ .env NOT found!")

print("🎉 Verification Complete.")
