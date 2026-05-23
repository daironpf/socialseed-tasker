from unittest.mock import MagicMock

from socialseed_tasker.cli.rate_limit_cli import check_cli_rate


def test_cli_rate_limit_denies():
    container = MagicMock()
    rl = MagicMock()
    rl.allow.return_value = False
    container.rate_limiter = rl
    assert not check_cli_rate(container, user_id="u1")
