import time
import torch
import numpy as np
from sentence_transformers import SentenceTransformer

def benchmark_cpu_inference():
    print(f"Torch Version: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    
    # Force CPU for this test
    device = "cpu"
    print(f"Benchmarking on: {device}")
    
    # 1. Measure Load Time
    start = time.time()
    model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
    load_time = time.time() - start
    print(f"Model Load Time: {load_time:.4f}s")
    
    # Mock Data (100 chunks of ~150 words)
    chunks = ["Python 3.15 includes generic type aliases, new warning control, and improved error messages." * 5] * 100
    query = "What are the new features in Python 3.15?"
    
    # 2. Measure Full Inference (100 chunks)
    start = time.time()
    embeddings = model.encode(chunks)
    q_emb = model.encode(query)
    full_time = time.time() - start
    print(f"Full Inference (100 chunks): {full_time:.4f}s (Avg: {full_time/100*1000:.2f}ms/chunk)")
    
    # 3. Measure Filtered Inference (Top 20 chunks)
    # Simulating a keyword filter that passes only 20%
    filtered_chunks = chunks[:20]
    start = time.time()
    embeddings_s = model.encode(filtered_chunks)
    q_emb_s = model.encode(query)
    filtered_time = time.time() - start
    print(f"Filtered Inference (20 chunks): {filtered_time:.4f}s")
    
    # 4. Impact Analysis
    print("\n--- Optimization Analysis ---")
    print(f"Speedup: {full_time / filtered_time:.2f}x")
    print(f"Latency Saved: {full_time - filtered_time:.4f}s")

if __name__ == "__main__":
    benchmark_cpu_inference()
