import asyncio
import open_web_search as ows

async def main():
    print("🚀 Testing API Level 1: Zero-Config")
    # This uses the default 'balanced' mode and global pipeline
    try:
        # Simple query
        results = await ows.search("What is the capital of South Korea?")
        print(f"Answer: {results.answer or 'No direct answer found.'}")
        print(f"Top Source: {results.results[0].url if results.results else 'None'}")
    except Exception as e:
        print(f"❌ Level 1 Failed: {e}")

    print("\n🚀 Testing API Level 2: Parameter Override")
    try:
        # Override mode to 'fast' and use 'fast' reranker (effectively Level 2)
        # Note: We can pass any LinkerConfig param here
        results_fast = await ows.search(
            "Quick pasta recipe", 
            mode="fast", 
            reranker_type="fast",
            max_evidence=3
        )
        print(f"Fast Mode Steps: {len(results_fast.results)} raw results found.")
        print(f"Fast Mode Evidence: {len(results_fast.evidence)} chunks selected.")
    except Exception as e:
        print(f"❌ Level 2 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
