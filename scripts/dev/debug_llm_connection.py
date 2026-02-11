import asyncio
import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load Env
load_dotenv(".env")

LLM_BASE = os.getenv("LLM_BASE_URL", "http://192.168.0.10:8101/v1")
LLM_KEY = os.getenv("LLM_API_KEY", "EMPTY")
MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")

async def test_direct_connection():
    print(f"\n[1] Testing Direct Connection to {LLM_BASE}...")
    client = AsyncOpenAI(base_url=LLM_BASE, api_key=LLM_KEY)
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Hello! Are you working? Reply with 'YES'."}],
            max_tokens=10
        )
        print(f"✅ Success! Response: {response.choices[0].message.content}")
        return True
    except Exception as e:
        print(f"❌ Failed! Error: {e}")
        return False

async def test_planner_direct():
    print(f"\n[2] Testing Planner Class directly...")
    try:
        from open_web_search.config import LinkerConfig
        from open_web_search.core.planner import Planner
        
        config = LinkerConfig(
            llm_base_url=LLM_BASE,
            llm_api_key=LLM_KEY,
            llm_model=MODEL
        )
        planner = Planner(config)
        queries = await planner.plan("Python 3.12 features")
        print(f"✅ Success! Plan: {queries}")
    except Exception as e:
        print(f"❌ FAILED! Error: {e}")

if __name__ == "__main__":
    print(f"Debug Target: {LLM_BASE} (Model: {MODEL})")
    asyncio.run(test_direct_connection())
    asyncio.run(test_planner_direct())
