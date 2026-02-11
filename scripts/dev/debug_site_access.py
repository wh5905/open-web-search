import asyncio
import random
from typing import Dict
from playwright.async_api import async_playwright
import httpx

TARGETS = [
    "https://www.reddit.com/r/rust/comments/18x6qm1/best_practices_for_error_handling/",
    "https://medium.com/@geekculture/7-rust-error-handling-best-practices-2024-5d5b3c3c6f62", # Fake URL pattern for test
    "https://news.ycombinator.com/item?id=38876543"
]

UA_DESKTOP = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
UA_MOBILE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"

async def test_httpx(url: str, ua: str, label: str):
    print(f"[{label}] Probing {url}...")
    try:
        async with httpx.AsyncClient(headers={"User-Agent": ua}, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"  -> Status: {resp.status_code}, Len: {len(resp.text)}")
            if resp.status_code == 403 or "captcha" in resp.text.lower():
                print("  -> BLOCKED")
            elif resp.status_code == 200:
                print("  -> SUCCESS")
    except Exception as e:
        print(f"  -> ERROR: {e}")

async def test_playwright(url: str, headless: bool, stealth: bool, label: str):
    print(f"[{label}] Probing {url} (Headless={headless}, Stealth={stealth})...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        
        # Context Setup
        if stealth:
            # Minimal Stealth Emulation
            context = await browser.new_context(
                user_agent=UA_DESKTOP,
                locale="en-US",
                viewport={"width": 1920, "height": 1080},
                device_scale_factor=1,
            )
            await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        else:
            context = await browser.new_context()
            
        page = await context.new_page()
        try:
            resp = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
            status = resp.status
            content = await page.content()
            print(f"  -> Status: {status}, Len: {len(content)}")
            
            # Simple Block Detection
            if "cf-challenge" in content or "Cloudflare" in await page.title():
                 print("  -> BLOCKED (Cloudflare)")
            elif status == 403:
                 print("  -> BLOCKED (403)")
            else:
                 print("  -> SUCCESS (Maybe)")
                 
        except Exception as e:
            print(f"  -> ERROR: {e}")
        finally:
            await browser.close()

async def main():
    print("# Universality Probe Tool\n")
    
    # Target: Reddit (Notorious for blocking headless)
    reddit = "https://www.reddit.com/r/rust/"
    await test_httpx(reddit, UA_DESKTOP, "HTTPX-Desktop")
    # await test_httpx(reddit + ".json", UA_DESKTOP, "HTTPX-JSON-API") # Trick?
    await test_playwright(reddit, headless=True, stealth=True, label="PW-Stealth")
    
    # Target: Medium (Cloudflare usually)
    medium = "https://medium.com/"
    await test_httpx(medium, UA_DESKTOP, "HTTPX-Desktop")
    await test_playwright(medium, headless=True, stealth=True, label="PW-Stealth")

if __name__ == "__main__":
    asyncio.run(main())
