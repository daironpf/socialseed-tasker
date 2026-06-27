from socialseed_tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter
from socialseed_tasker.infrastructure.faiss_store import FaissStore


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
    path = tmp_path / "store"
    store.persist(str(path))
    new_store = FaissStore(dim=dim)
    new_store.load(str(path))
    res2 = new_store.query(qv, top_k=2)
    assert len(res2) >= 1
    new_store.delete("i1")
    res3 = new_store.query(qv, top_k=3)
    assert isinstance(res3, list)
