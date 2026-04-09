"""Webhook signature validator for secure webhook processing.

Provides HMAC-SHA256 signature validation to prevent spoofing attacks.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class WebhookSignatureValidator:
    """Validates webhook signatures to prevent spoofing attacks."""

    def __init__(self, secret: str | None = None) -> None:
        self._secret = secret or os.environ.get("GITHUB_WEBHOOK_SECRET", "")
        self._rejected_log: list[dict] = []
        self._max_rejected_log_size = 100

    @property
    def secret(self) -> str:
        return self._secret

    @property
    def is_configured(self) -> bool:
        """Check if webhook secret is configured."""
        return bool(self._secret)

    def validate(self, payload: bytes, signature: str) -> bool:
        """Validate webhook signature.

        Args:
            payload: Raw request body
            signature: Signature from X-Hub-Signature-256 header

        Returns:
            True if signature is valid or no secret configured
        """
        if not self._secret:
            logger.warning("Webhook signature validation skipped - no secret configured")
            return True

        if not signature:
            self._log_rejected("missing", "No signature provided")
            return False

        expected = f"sha256={hmac.new(self._secret.encode(), payload, hashlib.sha256).hexdigest()}"

        if not hmac.compare_digest(expected, signature):
            self._log_rejected(signature, "Invalid signature")
            return False

        return True

    def _log_rejected(self, signature: str, reason: str) -> None:
        """Log rejected webhook requests for security auditing."""
        entry = {
            "timestamp": _now().isoformat(),
            "reason": reason,
            "signature_prefix": signature[:20] if signature else "none",
        }

        self._rejected_log.append(entry)

        if len(self._rejected_log) > self._max_rejected_log_size:
            self._rejected_log.pop(0)

        logger.warning(f"Webhook rejected: {reason}")

    def get_rejected_log(self) -> list[dict]:
        """Get log of rejected webhook requests."""
        return self._rejected_log.copy()

    def clear_rejected_log(self) -> None:
        """Clear the rejected requests log."""
        self._rejected_log.clear()


def validate_signature(payload: bytes, secret: str, signature: str) -> bool:
    """Standalone function for signature validation.

    Args:
        payload: Raw request body
        secret: Webhook secret
        signature: Signature from header

    Returns:
        True if signature is valid
    """
    if not secret or not signature:
        return True

    expected = f"sha256={hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()}"
    return hmac.compare_digest(expected, signature)


_validator_instance: WebhookSignatureValidator | None = None


def get_webhook_validator() -> WebhookSignatureValidator:
    """Get the global webhook signature validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = WebhookSignatureValidator()
    return _validator_instance
