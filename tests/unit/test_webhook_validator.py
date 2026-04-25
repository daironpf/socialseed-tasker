"""Tests for webhook signature validator service."""

import pytest
from unittest.mock import patch
from socialseed_tasker.core.services.webhook_validator import (
    WebhookSignatureValidator,
    validate_signature,
    get_webhook_validator,
)


class TestWebhookSignatureValidator:
    """Test cases for WebhookSignatureValidator class."""

    def test_validate_with_no_secret_returns_false(self):
        """Should return False when no secret is configured (security requirement)."""
        validator = WebhookSignatureValidator(secret="")
        payload = b'{"action": "opened"}'
        signature = "sha256=abc123"

        result = validator.validate(payload, signature)

        assert result is False

    def test_validate_with_valid_signature(self):
        """Should return True for valid HMAC-SHA256 signature."""
        import hmac
        import hashlib

        secret = "test-secret"
        payload = b'{"action": "opened"}'

        expected_sig = f"sha256={hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()}"

        validator = WebhookSignatureValidator(secret=secret)
        result = validator.validate(payload, expected_sig)

        assert result is True

    def test_validate_with_invalid_signature(self):
        """Should return False for invalid signature."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'
        signature = "sha256=invalidsignature"

        result = validator.validate(payload, signature)

        assert result is False

    def test_validate_with_missing_signature(self):
        """Should return False when no signature provided."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'

        result = validator.validate(payload, "")

        assert result is False

    def test_validate_with_missing_signature_prefix(self):
        """Should return False when signature lacks sha256= prefix."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'
        signature = "abc123"

        result = validator.validate(payload, signature)

        assert result is False

    def test_rejected_log_records_failed_validations(self):
        """Should log rejected webhook requests."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'

        validator.validate(payload, "sha256=invalid")
        validator.validate(payload, "sha256=also-invalid")

        log = validator.get_rejected_log()

        assert len(log) == 2
        assert log[0]["reason"] == "Invalid signature"
        assert log[1]["reason"] == "Invalid signature"

    def test_rejected_log_limits_size(self):
        """Should limit rejected log to 100 entries."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'

        for i in range(150):
            validator.validate(payload, f"sha256=invalid-{i}")

        log = validator.get_rejected_log()

        assert len(log) == 100

    def test_clear_rejected_log(self):
        """Should clear the rejected log."""
        validator = WebhookSignatureValidator(secret="test-secret")
        payload = b'{"action": "opened"}'

        validator.validate(payload, "sha256=invalid")
        validator.clear_rejected_log()

        log = validator.get_rejected_log()

        assert len(log) == 0

    def test_is_configured_property(self):
        """Should correctly report if secret is configured."""
        validator_no_secret = WebhookSignatureValidator(secret="")
        validator_with_secret = WebhookSignatureValidator(secret="test")

        assert validator_no_secret.is_configured is False
        assert validator_with_secret.is_configured is True

    def test_secret_property(self):
        """Should expose the secret."""
        validator = WebhookSignatureValidator(secret="my-secret")

        assert validator.secret == "my-secret"

    @patch.dict("os.environ", {"GITHUB_WEBHOOK_SECRET": "env-secret"})
    def test_uses_environment_variable(self):
        """Should use GITHUB_WEBHOOK_SECRET from environment."""
        validator = WebhookSignatureValidator()

        assert validator.secret == "env-secret"

    @patch.dict("os.environ", {}, clear=True)
    def test_defaults_to_empty_string_without_env(self):
        """Should default to empty string without environment variable."""
        validator = WebhookSignatureValidator()

        assert validator.secret == ""


class TestValidateSignatureFunction:
    """Test cases for standalone validate_signature function."""

    def test_valid_signature_returns_true(self):
        """Should return True for valid signature."""
        import hmac
        import hashlib

        secret = "test-secret"
        payload = b'{"action": "opened"}'
        expected_sig = f"sha256={hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()}"

        result = validate_signature(payload, secret, expected_sig)

        assert result is True

    def test_empty_secret_returns_false(self):
        """Should return False when secret is empty (security requirement)."""
        result = validate_signature(b"payload", "", "sha256=signature")

        assert result is False

    def test_empty_signature_returns_false(self):
        """Should return False when signature is empty (security requirement)."""
        result = validate_signature(b"payload", "secret", "")

        assert result is False

    def test_invalid_signature_returns_false(self):
        """Should return False for invalid signature."""
        result = validate_signature(b"payload", "secret", "sha256=wrong")

        assert result is False


class TestGetWebhookValidatorSingleton:
    """Test cases for get_webhook_validator singleton."""

    def test_returns_same_instance(self):
        """Should return the same instance on multiple calls."""
        validator1 = get_webhook_validator()
        validator2 = get_webhook_validator()

        assert validator1 is validator2
