RAG and FAISS Demo

Purpose
- Provide a local, deterministic RAG demo using a fallback embedding and FAISS (or numpy fallback).

Files
- socialseed_tasker/infrastructure/embeddings_adapter.py: deterministic fallback embedding implementation.
- socialseed_tasker/infrastructure/faiss_store.py: minimal FAISS wrapper with numpy fallback.
- examples/rag_demo/run_rag_demo.py: demo script that creates embeddings, upserts them, and queries.

Configuration
- TASKER_EMBED_DIM: embedding dimension (default 64)
- If faiss is not installed, the store falls back to a numpy-based brute-force search.

How to run
1. Install dependencies:
   python -m pip install -e .
   pip install faiss-cpu  # optional; if not installed, demo still works with numpy fallback
2. Run demo:
   python examples/rag_demo/run_rag_demo.py
3. Inspect output:
   cat examples/rag_demo/rag_output.json

Notes
- The fallback embedding is deterministic and suitable for offline testing and CI.
- For production-quality embeddings, implement an EmbeddingsAdapter that calls an external provider and returns fixed-length vectors.
