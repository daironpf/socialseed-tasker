"""Issue #583: ``_session()`` must accept wrapper and raw driver shapes.

``_session`` is shared by every Neo4j mixin/repository. Historically it
assumed a wrapper (``driver.driver`` + ``driver.database``), which blew up with
``AttributeError`` when a raw Bolt driver arrived (code-graph endpoints, whose
dependency unwraps ``app.state.driver``). Both shapes must keep working.
"""

from __future__ import annotations

from typing import Any

from socialseed_tasker.infrastructure.neo4j_impl.shared import _session


class _RecordingSession:
    def __init__(self) -> None:
        self.entered = True

    def __enter__(self) -> _RecordingSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _RawDriver:
    def __init__(self) -> None:
        self.databases: list[str] = []

    def session(self, database: str | None = None) -> _RecordingSession:
        self.databases.append(database or "")
        return _RecordingSession()


class _Wrapper:
    def __init__(self, inner: _RawDriver, database: str = "neo4j") -> None:
        self.driver = inner
        self.database = database


def test_session_with_wrapper_uses_inner_driver_and_wrapper_database() -> None:
    raw = _RawDriver()
    with _session(_Wrapper(raw, database="team-db")):
        pass
    assert raw.databases == ["team-db"]


def test_session_with_raw_driver_falls_back_to_default_database() -> None:
    raw = _RawDriver()
    with _session(raw):
        pass
    assert raw.databases == ["neo4j"]


def test_session_with_wrapper_without_database_defaults_to_neo4j() -> None:
    raw = _RawDriver()

    class _DriverOnlyWrapper:
        def __init__(self) -> None:
            self.driver = raw

    with _session(_DriverOnlyWrapper()):
        pass
    assert raw.databases == ["neo4j"]
