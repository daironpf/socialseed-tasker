"""System initialization entities and value objects.

Defines the data structures used during the scaffolding process,
including scaffold results, file operations, and template metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ScaffoldStatus(str, Enum):
    """Status of a scaffolded file operation."""

    CREATED = "created"
    SKIPPED = "skipped"
    OVERWRITTEN = "overwritten"
    ERROR = "error"


@dataclass
class FileOperation:
    """Result of a single file operation during scaffolding."""

    source: Path
    destination: Path
    status: ScaffoldStatus
    error_message: str = ""


@dataclass
class ScaffoldResult:
    """Aggregate result of a full scaffolding operation."""

    target_dir: Path
    operations: list[FileOperation] = field(default_factory=list)
    success: bool = True

    @property
    def created_count(self) -> int:
        return sum(1 for op in self.operations if op.status == ScaffoldStatus.CREATED)

    @property
    def overwritten_count(self) -> int:
        return sum(1 for op in self.operations if op.status == ScaffoldStatus.OVERWRITTEN)

    @property
    def skipped_count(self) -> int:
        return sum(1 for op in self.operations if op.status == ScaffoldStatus.SKIPPED)

    @property
    def error_count(self) -> int:
        return sum(1 for op in self.operations if op.status == ScaffoldStatus.ERROR)

    def add_operation(self, operation: FileOperation) -> None:
        """Record a file operation and update overall success status."""
        self.operations.append(operation)
        if operation.status == ScaffoldStatus.ERROR:
            self.success = False
