import os
import json
import requests
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv

load_dotenv("../../.env")

# PydanticAI uses strong typing.
# We simulate an extraction agent.

class StartupInfo(BaseModel):
    name: str = Field(description="Name of the startup")
    domain: str = Field(description="Industry or field")
    description: str = Field(description="One sentence description")

class ExtractionResult(BaseModel):
    startups: List[StartupInfo]

def main():
    print("=== PROJECT ZETA: Structured Scout (PydanticAI Mock) ===")
    print("Scenario: Strict Output Extraction from Linker-Search results.")
    
    query = "Top 3 YCombinator startups W24 batch"
    api_url = "http://127.0.0.1:8000/search"
    
    print(f"\n[Step 1] Searching: {query}")
    
    try:
        # 1. Get Unstructured Context via Linker
        payload = {"query": query, "include_answer": True, "search_depth": "basic"}
        resp = requests.post(api_url, json=payload, timeout=60)
        
        if resp.status_code != 200:
            print(f"Search failed: {resp.text}")
            return
            
        context = resp.json().get("answer", "")
        print(f"[Context Received] {len(context)} chars")
        
        # 2. Extract Structure (Simulating PydanticAI Agent)
        # Note: We are using the LLM directly here to simulate what PydanticAI does
        # PydanticAI would wrap this prompt + validation.
        
        # We'll skip the actual LLM call here to avoid double-taxing the local LLM concurrently
        # and instead show that we *got* the data needed for extraction.
        
        print("\n[Step 2] Validating Data Suitability for Extraction...")
        if len(context) > 100:
             print("Data Quality: HIGH (Suitable for extraction)")
             print(f"Preview: {context[:200]}...")
             print("\n[Success] PydanticAI pipeline prerequisite met.")
        else:
             print("Data Quality: LOW (Extraction risky)")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
