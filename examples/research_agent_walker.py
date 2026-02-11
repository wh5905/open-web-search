import asyncio
import os
from dotenv import load_dotenv

# Ensure we use the .venv if running directly
# import sys
# sys.path.append(".")

from open_web_search.crawling.crawler import NeuralCrawler
from open_web_search.crawling.analyzer import LinkAnalyzer
from open_web_search.readers.browser import PlaywrightReader

async def main():
    print("Initializing Neural Web Walker...")
    
    # 1. Setup Components
    reader = PlaywrightReader(headless=True)
    analyzer = LinkAnalyzer(model_name="all-MiniLM-L6-v2") # Uses local heavy model
    crawler = NeuralCrawler(reader=reader, analyzer=analyzer)
    
    # 2. Define Mission
    query = "Python 3.12 pattern matching tutorial" # A topic that usually requires clicking 'tutorials' or 'examples'
    start_urls = [
        "https://docs.python.org/3/whatsnew/3.12.html" # Starting point
    ]
    
    print(f"Mission: Explore '{query}' starting from {start_urls[0]}")
    
    # 3. Start Recursive Crawl
    try:
        pages = await crawler.crawl(start_urls, query, max_pages=3)
        
        print(f"\n[Result] Collected {len(pages)} pages recursively.")
        for i, p in enumerate(pages):
            print(f"[{i+1}] {p.title}")
            print(f"    URL: {p.url}")
            print(f"    Size: {len(p.text_plain or '')} chars")
            
    finally:
        await reader.close()

if __name__ == "__main__":
    asyncio.run(main())
