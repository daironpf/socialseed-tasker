#!/usr/bin/env python3
import json
import os
from pathlib import Path

from socialseed_tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter
from socialseed_tasker.infrastructure.faiss_store import FaissStore

DOCS = [
    {"id": "d1", "text": "Tasker is a tool to analyze code and issues."},
    {"id": "d2", "text": "Neo4j stores nodes and relationships for issues and code symbols."},
    {"id": "d3", "text": "FAISS provides fast nearest neighbor search for vectors."},
]

OUTPUT = Path(__file__).parent / "rag_output.json"


def main():
    dim = int(os.getenv("TASKER_EMBED_DIM", "64"))
    emb = EmbeddingsAdapter(dim=dim)
    store = FaissStore(dim=dim)
    for d in DOCS:
        v = emb.embed_text(d["text"])
        store.upsert(d["id"], v, metadata={"text": d["text"]})
    query = "How does Tasker store relationships?"
    qv = emb.embed_text(query)
    results = store.query(qv, top_k=3)
    out = {"query": query, "results": results}
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("Wrote RAG demo output to", OUTPUT)


if __name__ == "__main__":
    main()
