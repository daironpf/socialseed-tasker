from socialseed_tasker.auth.auth import InMemoryAuthProvider

def test_inmemory_verify_token_from_dict():
    users = {
        "u1": {"token": "t1", "permissions": ["read:context"]},
        "u2": {"token": "t2", "permissions": []}
    }
    p = InMemoryAuthProvider(users=users)
    assert p.verify_token("t1") == "u1"
    assert p.verify_token("t2") == "u2"
    assert p.verify_token("nope") is None
