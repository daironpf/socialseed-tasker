from __future__ import annotations

import hashlib
import math
import os
from typing import List

from socialseed_tasker.application.ports import EmbeddingPort

FALLBACK_DIM = int(os.getenv("TASKER_EMBED_DIM", "64"))


class EmbeddingsAdapter(EmbeddingPort):
    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or FALLBACK_DIM

    def _text_to_vector(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode("utf-8")).digest()
        repeats = (self.dim * 4 + len(h) - 1) // len(h)
        data = (h * repeats)[: self.dim * 4]
        vec = []
        for i in range(self.dim):
            chunk = data[i * 4 : i * 4 + 4]
            val = int.from_bytes(chunk, "big", signed=False)
            vec.append(float(val))
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_text(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]
