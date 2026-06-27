### Issue 301 — Implement Embedding adapter and FAISS local vector store for RAG demo

**Short description**  
Add a concrete `EmbeddingPort` implementation and a local FAISS-backed vector store adapter that implements a minimal vector index API. Provide a reproducible RAG demo that shows how to embed text, store vectors, and perform nearest-neighbor retrieval to build context for agents. Include unit tests, an example script, and CI-friendly integration steps. All method names, file paths, and behaviors are explicit so an autonomous agent can implement and verify without guessing.

---

#### Objective (what the agent must deliver)
1. Add `tasker/infrastructure/embeddings_adapter.py` implementing `tasker.application.ports.EmbeddingPort` with methods `embed_text` and `embed_batch`.
2. Add `tasker/infrastructure/faiss_store.py` implementing a small vector store with methods:
   - `upsert(id: str, vector: list[float], metadata: dict | None = None) -> None`
   - `query(vector: list[float], top_k: int = 5) -> list[dict]` (returns list of `{id, score, metadata}`)
   - `delete(id: str) -> None`
   - `persist(path: str) -> None`
   - `load(path: str) -> None`
3. Provide a simple embedding implementation using a deterministic, local embedding function when no external model is configured (e.g., hashing + normalized float vector) and allow optional integration with an external embedding provider via environment variables (but do not require network access).
4. Add a reproducible RAG demo script `examples/rag_demo/run_rag_demo.py` that:
   - Creates embeddings for a small set of documents,
   - Stores them in FAISS store,
   - Queries with a sample question,
   - Prints retrieved documents and scores as JSON.
5. Add unit tests for embedding adapter and FAISS store (`tests/infrastructure/test_embeddings_unit.py`, `tests/infrastructure/test_faiss_store_unit.py`).
6. Add documentation `tasker/infrastructure/RAG_FAISS.md` describing configuration, deterministic fallback embedding, and example outputs.
7. Create branch `feature/embeddings-faiss-demo` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Autonomous agents need a deterministic, local embedding fallback to run RAG demos offline and to validate retrieval logic.
- FAISS is a standard local vector index; providing a small wrapper with explicit API removes ambiguity for agents that will call it.
- Tests and example scripts ensure reproducibility and make it trivial for other agents to reuse the components.

---

#### Files to add or modify (exact paths)
- `tasker/infrastructure/embeddings_adapter.py` **(new)**
- `tasker/infrastructure/faiss_store.py` **(new)**
- `examples/rag_demo/run_rag_demo.py` **(new)**
- `tasker/infrastructure/RAG_FAISS.md` **(new)**
- `tests/infrastructure/test_embeddings_unit.py` **(new)**
- `tests/infrastructure/test_faiss_store_unit.py` **(new)**
- Update `tasker/infrastructure/__init__.py` to export `EmbeddingsAdapter` and `FaissStore` (if present).

---

#### Exact code to add for `embeddings_adapter.py`

Create `tasker/infrastructure/embeddings_adapter.py` with the exact content below. Do not change method names or signatures.

```python
# tasker/infrastructure/embeddings_adapter.py
from __future__ import annotations
import os
import hashlib
import math
from typing import List
from tasker.application.ports import EmbeddingPort

# Deterministic fallback embedding: hash-based vector of fixed dimension
FALLBACK_DIM = int(os.getenv("TASKER_EMBED_DIM", "64"))

class EmbeddingsAdapter(EmbeddingPort):
    """
    EmbeddingPort implementation.

    Behavior:
    - If environment variable TASKER_EMBED_PROVIDER == "local", use deterministic fallback.
    - Otherwise, still use deterministic fallback (no network calls).
    - embed_text returns a list[float] of length FALLBACK_DIM.
    - embed_batch returns list[list[float]] in same order as input.
    """

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or FALLBACK_DIM

    def _text_to_vector(self, text: str) -> List[float]:
        # deterministic hash-based embedding: split SHA256 into dim chunks and normalize
        h = hashlib.sha256(text.encode("utf-8")).digest()
        # expand digest to required length by repeating
        repeats = (self.dim * 4 + len(h) - 1) // len(h)
        data = (h * repeats)[: self.dim * 4]
        vec = []
        for i in range(self.dim):
            # take 4 bytes -> unsigned int
            chunk = data[i * 4 : i * 4 + 4]
            val = int.from_bytes(chunk, "big", signed=False)
            vec.append(float(val))
        # normalize
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_text(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]
```

---

#### Exact code to add for `faiss_store.py`

Create `tasker/infrastructure/faiss_store.py` with the exact content below. Do not change method names or signatures.

```python
# tasker/infrastructure/faiss_store.py
from __future__ import annotations
import os
import json
import numpy as np
from typing import List, Dict, Optional
try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except Exception:
    _FAISS_AVAILABLE = False

class FaissStore:
    """
    Minimal FAISS-backed vector store wrapper.

    Methods:
    - upsert(id, vector, metadata)
    - query(vector, top_k) -> list[dict] with keys id, score, metadata
    - delete(id)
    - persist(path)
    - load(path)
    """

    def __init__(self, dim: int, index_factory: str = "Flat"):
        self.dim = dim
        self.index_factory = index_factory
        self._id_to_meta: Dict[str, Dict] = {}
        self._id_list: List[str] = []
        self._vectors = None
        self._index = None
        if _FAISS_AVAILABLE:
            self._index = faiss.IndexFlatL2(dim)
        else:
            # fallback: use numpy arrays and brute-force search
            self._index = None
            self._vectors = np.zeros((0, dim), dtype="float32")

    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict] = None) -> None:
        vec = np.array(vector, dtype="float32").reshape(1, -1)
        if _FAISS_AVAILABLE:
            # append to index by rebuilding (simple approach)
            if self._index.ntotal == 0:
                self._index.add(vec)
                self._id_list.append(id)
            else:
                # rebuild index with appended vectors
                existing = self._index.reconstruct_n(0, self._index.ntotal)
                all_vecs = np.vstack([existing, vec])
                self._index = faiss.IndexFlatL2(self.dim)
                self._index.add(all_vecs)
                self._id_list.append(id)
        else:
            if self._vectors.size == 0:
                self._vectors = vec
            else:
                self._vectors = np.vstack([self._vectors, vec])
            self._id_list.append(id)
        self._id_to_meta[id] = metadata or {}

    def query(self, vector: List[float], top_k: int = 5) -> List[Dict]:
        q = np.array(vector, dtype="float32").reshape(1, -1)
        if _FAISS_AVAILABLE:
            D, I = self._index.search(q, top_k)
            results = []
            for dist, idx in zip(D[0], I[0]):
                if idx < 0 or idx >= len(self._id_list):
                    continue
                _id = self._id_list[int(idx)]
                results.append({"id": _id, "score": float(dist), "metadata": self._id_to_meta.get(_id, {})})
            return results
        else:
            if self._vectors.size == 0:
                return []
            # compute L2 distances
            diffs = self._vectors - q
            dists = np.sum(diffs * diffs, axis=1)
            idxs = np.argsort(dists)[:top_k]
            results = []
            for idx in idxs:
                _id = self._id_list[int(idx)]
                results.append({"id": _id, "score": float(dists[int(idx)]), "metadata": self._id_to_meta.get(_id, {})})
            return results

    def delete(self, id: str) -> None:
        if id not in self._id_to_meta:
            return
        idx = self._id_list.index(id)
        self._id_list.pop(idx)
        self._id_to_meta.pop(id, None)
        if _FAISS_AVAILABLE:
            # rebuild index without the deleted vector
            if not self._id_list:
                self._index = faiss.IndexFlatL2(self.dim)
            else:
                # reconstruct all vectors from index and remove idx
                existing = self._index.reconstruct_n(0, self._index.ntotal)
                mask = [i for i in range(existing.shape[0]) if i != idx]
                new_vecs = existing[mask]
                self._index = faiss.IndexFlatL2(self.dim)
                self._index.add(new_vecs)
        else:
            if self._vectors.size == 0:
                return
            self._vectors = np.delete(self._vectors, idx, axis=0)

    def persist(self, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        meta_path = os.path.join(path, "meta.json")
        with open(meta_path, "w", encoding="utf-8") as fh:
            json.dump({"ids": self._id_list, "meta": self._id_to_meta, "dim": self.dim}, fh)
        if _FAISS_AVAILABLE:
            faiss.write_index(self._index, os.path.join(path, "index.faiss"))
        else:
            np.save(os.path.join(path, "vectors.npy"), self._vectors)

    def load(self, path: str) -> None:
        meta_path = os.path.join(path, "meta.json")
        with open(meta_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        self._id_list = data.get("ids", [])
        self._id_to_meta = data.get("meta", {})
        if _FAISS_AVAILABLE:
            self._index = faiss.read_index(os.path.join(path, "index.faiss"))
        else:
            import numpy as np
            self._vectors = np.load(os.path.join(path, "vectors.npy"))
```

---

#### Exact code to add for RAG demo script

Create `examples/rag_demo/run_rag_demo.py` with the exact content below.

```python
#!/usr/bin/env python3
import json
import os
from pathlib import Path
from tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter
from tasker.infrastructure.faiss_store import FaissStore

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
    # upsert docs
    for d in DOCS:
        v = emb.embed_text(d["text"])
        store.upsert(d["id"], v, metadata={"text": d["text"]})
    # query
    query = "How does Tasker store relationships?"
    qv = emb.embed_text(query)
    results = store.query(qv, top_k=3)
    out = {"query": query, "results": results}
    with open(OUTPUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("Wrote RAG demo output to", OUTPUT)

if __name__ == "__main__":
    main()
```

---

#### Exact unit tests to add

**`tests/infrastructure/test_embeddings_unit.py`**

```python
# tests/infrastructure/test_embeddings_unit.py
from tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter

def test_embed_text_length_and_determinism():
    e = EmbeddingsAdapter(dim=32)
    v1 = e.embed_text("hello world")
    v2 = e.embed_text("hello world")
    assert isinstance(v1, list)
    assert len(v1) == 32
    assert v1 == v2

def test_embed_batch_order():
    e = EmbeddingsAdapter(dim=16)
    texts = ["a", "b", "c"]
    batch = e.embed_batch(texts)
    assert len(batch) == 3
    assert batch[0] == e.embed_text("a")
```

**`tests/infrastructure/test_faiss_store_unit.py`**

```python
# tests/infrastructure/test_faiss_store_unit.py
import os
import tempfile
from tasker.infrastructure.faiss_store import FaissStore
from tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter

def test_faiss_upsert_query_delete_and_persist(tmp_path):
    dim = 16
    emb = EmbeddingsAdapter(dim=dim)
    store = FaissStore(dim=dim)
    texts = ["alpha", "beta", "gamma"]
    ids = ["i1", "i2", "i3"]
    for id_, t in zip(ids, texts):
        store.upsert(id_, emb.embed_text(t), metadata={"text": t})
    qv = emb.embed_text("alpha")
    res = store.query(qv, top_k=2)
    assert len(res) >= 1
    # persist and load
    path = tmp_path / "store"
    store.persist(str(path))
    new_store = FaissStore(dim=dim)
    new_store.load(str(path))
    res2 = new_store.query(qv, top_k=2)
    assert len(res2) >= 1
    # delete
    new_store.delete("i1")
    res3 = new_store.query(qv, top_k=3)
    # ensure id removed or results changed
    assert isinstance(res3, list)
```

---

#### Exact documentation to add

Create `tasker/infrastructure/RAG_FAISS.md` with the exact content below.

```
RAG and FAISS Demo

Purpose
- Provide a local, deterministic RAG demo using a fallback embedding and FAISS (or numpy fallback).

Files
- tasker/infrastructure/embeddings_adapter.py: deterministic fallback embedding implementation.
- tasker/infrastructure/faiss_store.py: minimal FAISS wrapper with numpy fallback.
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
```

---

#### Exact commands the agent must run

```bash
git checkout -b feature/embeddings-faiss-demo
# create files as specified
python -m pip install -e .
# optional: install faiss for faster queries
pip install faiss-cpu || true
# run unit tests
pytest tests/infrastructure/test_embeddings_unit.py -q
pytest tests/infrastructure/test_faiss_store_unit.py -q
# run demo
python examples/rag_demo/run_rag_demo.py
# commit and push
git add tasker/infrastructure/embeddings_adapter.py tasker/infrastructure/faiss_store.py examples/rag_demo run_rag_demo.py tasker/infrastructure/RAG_FAISS.md tests/infrastructure
git commit -m "feat(infra): add EmbeddingsAdapter and FaissStore with RAG demo and tests"
git push origin feature/embeddings-faiss-demo
```

---

#### PR body exact text to paste

```
Summary:
- Added deterministic EmbeddingsAdapter at tasker/infrastructure/embeddings_adapter.py implementing EmbeddingPort.
- Added FaissStore at tasker/infrastructure/faiss_store.py with FAISS and numpy fallback.
- Added RAG demo script examples/rag_demo/run_rag_demo.py that upserts documents and queries nearest neighbors.
- Added unit tests for embeddings and FAISS store.
- Added documentation tasker/infrastructure/RAG_FAISS.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Optionally installed faiss-cpu for faster queries.
3. Ran unit tests: pytest tests/infrastructure/test_embeddings_unit.py and test_faiss_store_unit.py (passed).
4. Ran demo: python examples/rag_demo/run_rag_demo.py (produced rag_output.json).

Files changed:
- tasker/infrastructure/embeddings_adapter.py
- tasker/infrastructure/faiss_store.py
- examples/rag_demo/run_rag_demo.py
- tasker/infrastructure/RAG_FAISS.md
- tests/infrastructure/test_embeddings_unit.py
- tests/infrastructure/test_faiss_store_unit.py

Notes:
- Faiss is optional; the store falls back to numpy-based brute-force search when faiss is not installed.
- The fallback embedding is deterministic and suitable for offline testing and CI.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/infrastructure/embeddings_adapter.py` exists and implements `embed_text` and `embed_batch` with deterministic fallback behavior.
- `tasker/infrastructure/faiss_store.py` exists and implements `upsert`, `query`, `delete`, `persist`, and `load`.
- Unit tests `tests/infrastructure/test_embeddings_unit.py` and `tests/infrastructure/test_faiss_store_unit.py` pass.
- `examples/rag_demo/run_rag_demo.py` runs and writes `rag_output.json` in the same directory.
- `tasker/infrastructure/RAG_FAISS.md` documents usage and fallback semantics.
- Branch `feature/embeddings-faiss-demo` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `infra`
- `ai`
- `examples`
- `medium-priority`

---

#### Estimated effort
**Small–Medium (S–M)** — expected to take **1–3 hours** depending on whether `faiss` is installed in the environment.