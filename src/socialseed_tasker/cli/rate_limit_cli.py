from __future__ import annotations

from typing import Optional


def check_cli_rate(container, user_id: Optional[str]) -> bool:
    limiter = getattr(container, "rate_limiter", None)
    if limiter is None:
        return True
    if user_id:
        key = f"user:{user_id}"
    else:
        import socket
        key = f"cli:{socket.gethostname()}"
    return limiter.allow(key, tokens=1)
