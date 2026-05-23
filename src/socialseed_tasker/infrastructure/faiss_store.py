from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

import numpy as np

try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except Exception:
    _FAISS_AVAILABLE = False


class FaissStore:
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
            self._index = None
            self._vectors = np.zeros((0, dim), dtype="float32")

    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict] = None) -> None:
        vec = np.array(vector, dtype="float32").reshape(1, -1)
        if _FAISS_AVAILABLE:
            if self._index.ntotal == 0:
                self._index.add(vec)
                self._id_list.append(id)
            else:
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
            if not self._id_list:
                self._index = faiss.IndexFlatL2(self.dim)
            else:
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
