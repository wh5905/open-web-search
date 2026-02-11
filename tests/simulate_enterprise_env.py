import asyncio
import threading
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from loguru import logger
import sys

# --- 1. The "Corporate Intranet" Simulation ---
# Imitates a secure internal Wiki accessible only via Private IP + Token
app = FastAPI()

@app.get("/wiki/project-titan", response_class=HTMLResponse)
def read_confidential_wiki(x_corp_token: str = Header(None)):
    """
    Accessible only if you have the correct header.
    Hosted on localhost (Private IP).
    """
    if x_corp_token != "s3cr3t-k3y-TOP-SECRET":
        # Simulate a corporate SSO redirect or 403
        raise HTTPException(status_code=403, detail="Access Denied: Missing valid Corporate Token")
    
    return """
    <html>
        <head><title>Project Titan - CONFIDENTIAL</title></head>
        <body>
            <h1>Project Titan: Next-Gen Agentic Framework</h1>
            <div class="confidential-banner">TOP SECRET / INTERNAL USE ONLY</div>
            <p><strong>Executive Summary:</strong> Project Titan aims to integrate 10,000 H100 GPUs.</p>
            <p><strong>Launch Date:</strong> Q4 2026</p>
            <p><strong>Key Contact:</strong> Dr. Antigravity (Director of AI)</p>
        </body>
    </html>
    """

def run_server():
    # Run on localhost:9999
    uvicorn.run(app, host="127.0.0.1", port=9999, log_level="critical")

# --- 2. The Verification Logic ---
from open_web_search.core.pipeline import AsyncPipeline
from open_web_search.config import LinkerConfig, SecurityConfig
from open_web_search.schemas.results import FetchedPage

async def run_simulation():
    # Start the server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    await asyncio.sleep(2) # Wait for startup
    
    target_url = "http://127.0.0.1:9999/wiki/project-titan"
    print(f"\n[Scenario] Target URL: {target_url} (Private IP, Auth Required)")

    # --- Use Case 1: Public Mode (Should Fail) ---
    print("\n--- Test 1: Public Mode (Default) ---")
    print("Agent attempts to access corporate wiki without specific config...")
    
    public_config = LinkerConfig(
        security=SecurityConfig(network_profile="public") # Explicitly Public
    )
    pipeline = AsyncPipeline(config=public_config)
    
    # We cheat and call reader directly to isolate the blocking logic 
    # (Engine won't find localhost URL anyway)
    # Actually, let's use security check directly first
    is_allowed = pipeline.security.is_allowed_url(target_url)
    if not is_allowed:
        print(f"✅ PASSED: Public Mode BLOCKED access to {target_url} (SSRF Protection Active)")
    else:
        print(f"❌ FAILED: Public Mode ALLOWED access to {target_url}!")

    # --- Use Case 2: Linker Enterprise Mode (Should Succeed) ---
    print("\n--- Test 2: Enterprise Mode (With Auth) ---")
    print("Agent activated with network_profile='enterprise' and Custom Headers...")
    
    enterprise_config = LinkerConfig(
        security=SecurityConfig(network_profile="enterprise", allowed_domains=["127.0.0.1"]), # Allow specific or all
        network_profile="enterprise", # Wait, I moved it to SecurityConfig? 
                                      # config.py has it in SecurityConfig now?
                                      # Let's check my previous edit.
                                      # I moved network_profile to SecurityConfig.
                                      # But I removed it from LinkerConfig?
                                      # Yes. But LinkerConfig(network_profile=...) won't work if it's not in LinkerConfig root.
                                      # Wait, LinkerConfig `security` field is `SecurityConfig`.
                                      # So: LinkerConfig(security=SecurityConfig(network_profile='enterprise'))
        custom_headers={
            "X-Corp-Token": "s3cr3t-k3y-TOP-SECRET"
        }
    )
    # Correction: I removed network_profile from LinkerConfig root in Step 3163?
    # No, step 3161 I *added* it to SecurityConfig.
    # Step 3168 I *removed* it from LinkerConfig.
    # So I MUST initialize via security field.
    
    pipeline_ent = AsyncPipeline(config=enterprise_config)
    
    # 1. Check Security Guard
    if pipeline_ent.security.is_allowed_url(target_url):
        print(f"✅ Security Check PASSED: Enterprise Mode allowed private IP.")
    else:
        print(f"❌ Security Check FAILED: Enterprise Mode BLOCKED private IP.")
        return

    # 2. Try Reading (Auth Check)
    print("Attemping to fetch securely...")
    pages = await pipeline_ent.reader.read_many([target_url])
    page = pages[0]
    
    if page.error:
        print(f"❌ Read Failed: {page.error}")
    elif "Project Titan" in (page.text_plain or ""):
        print(f"✅ PASSED: Successfully read confidential content!")
        print(f"   Snippet: {page.text_plain[:100]}...")
    else:
        print(f"❌ Content Mismatch. Got: {page.text_plain}")
        print(f"Status: {page.status_code}")

if __name__ == "__main__":
    asyncio.run(run_simulation())
