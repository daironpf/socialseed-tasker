from __future__ import annotations


def check_cli_rate(container, user_id: str | None) -> bool:
    limiter = getattr(container, "rate_limiter", None)
    if limiter is None:
        return True
    if user_id:
        key = f"user:{user_id}"
    else:
        import socket
        key = f"cli:{socket.gethostname()}"
    allowed = limiter.allow(key, tokens=1)
    if not allowed:
        return False
    state = getattr(limiter, "get_state", None)
    if state:
        try:
            s = state(key)
            tokens = s.get("tokens", 0)
            burst = s.get("burst", 20)
            if tokens <= burst * 0.2:
                from socialseed_tasker.cli.app import console
                console.print(f"[warning]Rate limit warning: only {tokens:.0f}/{burst} tokens remaining.[/warning]")
        except Exception:
            pass
    return True
