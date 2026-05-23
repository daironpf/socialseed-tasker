from socialseed_tasker.infrastructure.embeddings_adapter import EmbeddingsAdapter


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
