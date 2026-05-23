from __future__ import annotations
import json
from typing import List, Dict, Any
from socialseed_tasker.workers.app import create_celery

celery = create_celery()

@celery.task(name="tasker.parse_and_index_files")
def parse_and_index_files(file_paths: List[str]) -> Dict[str, Any]:
    from socialseed_tasker.infrastructure.parser_adapter import TreeSitterParser
    from socialseed_tasker.cli.wiring import build_default_container

    container = build_default_container()
    parser = container.parser
    results = {"parsed": 0, "errors": []}
    for p in file_paths:
        try:
            ast = parser.parse_file(p)
            symbols = parser.extract_symbols(ast)
            results["parsed"] += 1
        except Exception as exc:
            results["errors"].append({"path": p, "error": str(exc)})
    return results

@celery.task(name="tasker.batch_embed_and_store")
def batch_embed_and_store(docs: List[Dict[str, Any]], store_key: str) -> Dict[str, Any]:
    from socialseed_tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter
    from socialseed_tasker.infrastructure.faiss_store import FaissStore
    import tempfile
    import os
    dim = int(os.getenv("TASKER_EMBED_DIM", "64"))
    emb = EmbeddingsAdapter(dim=dim)
    store = FaissStore(dim=dim)
    for d in docs:
        v = emb.embed_text(d["text"])
        store.upsert(d["id"], v, metadata={"text": d.get("text")})
    path = os.path.join(tempfile.gettempdir(), f"faiss_{store_key}")
    store.persist(path)
    return {"stored": len(docs), "path": path}

@celery.task(name="tasker.run_graph_analysis")
def run_graph_analysis(issue_id: str, depth: int = 3) -> Dict[str, Any]:
    from socialseed_tasker.infrastructure.neo4j_adapter import Neo4jGraphAdapter
    from socialseed_tasker.infrastructure.neo4j_graph_repository import Neo4jGraphRepository
    graph = Neo4jGraphAdapter()
    repo = Neo4jGraphRepository(graph)
    impacted = list(repo.find_impact_set(issue_id, max_depth=depth))
    graph.close()
    return {"issue_id": issue_id, "impact_set": sorted(set(impacted))}
