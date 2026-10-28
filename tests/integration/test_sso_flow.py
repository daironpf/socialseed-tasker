import os
import requests
import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.requires_api,
    pytest.mark.requires_sso,
]


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_sso_session_cookie_and_api_access():
    _skip_if_not_integration()
    keycloak = os.getenv("TASKER_KEYCLOAK_URL", "http://localhost:8082")
    api = os.getenv("TASKER_API_URL", "http://localhost:8000")
    token_url = f"{keycloak}/realms/tasker-dev/protocol/openid-connect/token"
    data = {
        "grant_type": "password",
        "client_id": "tasker-frontend",
        "username": "reader",
        "password": "readertoken123",
        "scope": "openid",
    }
    r = requests.post(token_url, data=data, timeout=5)
    assert r.status_code == 200
    tokens = r.json()
    id_token = tokens.get("id_token")
    assert id_token is not None
    backend_session_create = f"{api}/test/create_session"
    r2 = requests.post(
        backend_session_create,
        json={
            "id_token": id_token,
            "access_token": tokens.get("access_token"),
            "refresh_token": tokens.get("refresh_token"),
        },
        timeout=5,
    )
    assert r2.status_code == 200
    assert "set-cookie" in r2.headers or r2.cookies
    cookies = r2.cookies
    r3 = requests.get(f"{api}/api/v1/whoami", cookies=cookies, timeout=5)
    assert r3.status_code == 200
    j = r3.json()["data"]
    assert j.get("username") == "reader"
