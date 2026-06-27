"""File integrity checker for self-healing architecture.

Provides file hash verification to ensure the graph stays in sync
with actual source code on disk.
"""

import hashlib
from pathlib import Path
from typing import Any


def compute_file_hash(file_path: Path) -> str | None:
    """Compute MD5 hash of a file's content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash hex string, or None if read fails
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        return hashlib.md5(content.encode()).hexdigest()
    except (UnicodeDecodeError, OSError):
        return None


def verify_file_integrity(
    stored_hash: str | None,
    file_path: Path
) -> bool:
    """Verify a file's integrity by comparing hashes.
    
    Args:
        stored_hash: Hash stored in CodeFile node
        file_path: Path to the file on disk
        
    Returns:
        True if hashes match or file doesn't exist,
        False if mismatch detected
    """
    if not stored_hash:
        return True
    
    if not file_path.exists():
        return True
    
    current_hash = compute_file_hash(file_path)
    return current_hash == stored_hash


def get_stale_files(
    code_files: list[dict[str, Any]],
    repo_path: Path
) -> list[dict[str, Any]]:
    """Find files that have changed since last scan.
    
    Args:
        code_files: List of CodeFile dicts with path and fileHash
        repo_path: Root of the repository
        
    Returns:
        List of stale files that need re-scanning
    """
    stale = []
    
    for cf in code_files:
        stored_hash = cf.get("fileHash")
        file_path = cf.get("path")
        
        if not file_path:
            continue
        
        full_path = repo_path / file_path
        
        if not verify_file_integrity(stored_hash, full_path):
            stale.append({
                "id": cf.get("id"),
                "path": file_path,
                "stored_hash": stored_hash,
                "current_hash": compute_file_hash(full_path),
            })
    
    return stale