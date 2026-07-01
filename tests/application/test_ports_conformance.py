"""Conformance tests for application port Protocols.

Verifies that minimal concrete stubs satisfy each Protocol using
runtime_checkable isinstance checks and mypy-friendly type annotations.
"""

from socialseed_tasker.application import exceptions, ports


class DummyGraph:
    def create_node(self, label: str, properties: dict) -> str:
        return "node-1"

    def get_node(self, node_id: str):
        return None

    def run_cypher(self, query: str, params=None):
        return ports.QueryResult(records=[])

    def delete_node(self, node_id: str) -> None:
        return None


def test_graph_port_runtime_checkable():
    g = DummyGraph()
    assert isinstance(g, ports.GraphPort)


class DummyParser:
    def parse_file(self, path: str) -> dict:
        return {"type": "module", "body": []}

    def extract_symbols(self, ast: dict) -> list[dict]:
        return [{"name": "foo", "kind": "function", "line": 1}]

    def extract_imports(self, ast: dict) -> list[str]:
        return ["os", "sys"]


def test_parser_port_runtime_checkable():
    p = DummyParser()
    assert isinstance(p, ports.ParserPort)


class DummyGit:
    def list_changed_files(self, ref: str) -> list[str]:
        return ["src/main.py"]

    def read_file_at_ref(self, path: str, ref: str) -> str:
        return "print('hello')"

    def current_branch(self) -> str:
        return "main"


def test_git_port_runtime_checkable():
    g = DummyGit()
    assert isinstance(g, ports.GitPort)


class DummyEmbed:
    def embed_text(self, text: str) -> list[float]:
        return [0.0] * 8

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] * 8 for _ in texts]


def test_embedding_port_runtime_checkable():
    e = DummyEmbed()
    assert isinstance(e, ports.EmbeddingPort)


class DummyStorage:
    def put(self, key: str, value: bytes, ttl_seconds: int | None = None) -> None:
        return None

    def get(self, key: str) -> bytes | None:
        return None

    def delete(self, key: str) -> None:
        return None

    def list_keys(self) -> list[str]:
        return []


def test_storage_port_runtime_checkable():
    s = DummyStorage()
    assert isinstance(s, ports.StoragePort)


class DummyLogger:
    def info(self, message: str, **fields) -> None:
        pass

    def debug(self, message: str, **fields) -> None:
        pass

    def warning(self, message: str, **fields) -> None:
        pass

    def error(self, message: str, **fields) -> None:
        pass


def test_logger_port_runtime_checkable():
    logger = DummyLogger()
    assert isinstance(logger, ports.LoggerPort)


def test_embedding_port_signature():
    e: ports.EmbeddingPort = DummyEmbed()
    assert isinstance(e, ports.EmbeddingPort)


def test_exceptions_importable():
    assert exceptions.GraphPortError is not None
    assert exceptions.ParserError is not None
    assert exceptions.GitError is not None
    assert exceptions.EmbeddingError is not None
    assert exceptions.StorageError is not None
