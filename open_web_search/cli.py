import argparse
import subprocess
import sys
import shutil
import time
import os
from pathlib import Path

def check_docker():
    """Check if docker is installed and running."""
    if not shutil.which("docker"):
        print("Error: Docker is not installed or not in PATH.")
        return False
    try:
        subprocess.run(["docker", "ps"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print("Error: Docker daemon is not running.")
        return False

def get_compose_file():
    """Get the path to the bundled docker-compose.yml."""
    cwd_compose = Path("docker-compose.yml")
    if cwd_compose.exists():
        return cwd_compose
    
    # Fallback: Create one in the current directory if missing
    print("Creating default docker-compose.yml for Linker-Search...")
    content = """
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    ports:
      - "8080:8080"
    environment:
      - BASE_URL=http://localhost:8080/
      - INSTANCE_NAME=Linker-Search-Scout
      - SEARXNG_LIMITER=false
      - SEARXNG_PUBLIC_INSTANCE=false
      - SEARXNG_SEARCH_FORMATS=html,json
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
      - DAC_OVERRIDE
    logging:
      driver: "json-file"
      options:
        max-size: "1m"
        max-file: "1"
"""
    cwd_compose.write_text(content.strip())
    return cwd_compose

def setup():
    if not check_docker():
        return
    
    print("Setting up Linker-Search Engine (SearXNG)...")
    compose_file = get_compose_file()
    
    try:
        # Force stop and remove old one
        subprocess.run(["docker", "compose", "-f", str(compose_file), "down"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        subprocess.run(["docker", "compose", "-f", str(compose_file), "up", "-d"], check=True)
        print("Waiting for SearXNG to be healthy...")
        time.sleep(5)
        print("Linker-Search Engine is ready! You can now use 'engine_provider=\"searxng\"'.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start SearXNG: {e}")

def status():
    if not check_docker():
        return
    
    print("Checking Linker-Search Engine status...")
    try:
        result = subprocess.run(["docker", "ps", "--filter", "name=searxng", "--format", "{{.Status}}"], capture_output=True, text=True)
        if "Up" in result.stdout:
            print(f"SearXNG is RUNNING: {result.stdout.strip()}")
        else:
            print("SearXNG is NOT running.")
    except Exception:
        print("Error checking status.")

def stop():
    if not check_docker():
        return
    print("Stopping Linker-Search Engine...")
    subprocess.run(["docker", "stop", "searxng"], check=False)
    subprocess.run(["docker", "rm", "searxng"], check=False)
    print("Stopped.")

def serve(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    try:
        import uvicorn
        print(f"Starting Linker-Search API Server...")
        print(f"Listening on: http://{host}:{port}")
        print(f"Tavily Endpoint: http://{host}:{port}/search")
        
        uvicorn.run("open_web_search.server.app:app", host=host, port=port, reload=reload)
    except ImportError:
        print("Error: FastAPI/Uvicorn not installed.")
        print("Run: pip install 'linker-search[server]' or 'pip install fastapi uvicorn'")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Linker-Search Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    subparsers.add_parser("setup", help="Setup and start the local search engine (SearXNG)")
    subparsers.add_parser("status", help="Check status of the search engine")
    subparsers.add_parser("stop", help="Stop the search engine")
    
    serve_parser = subparsers.add_parser("serve", help="Start the Universal API Server (Tavily Mock)")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup()
    elif args.command == "status":
        status()
    elif args.command == "stop":
        stop()
    elif args.command == "serve":
        serve(host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    main()
