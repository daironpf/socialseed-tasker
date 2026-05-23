from socialseed_tasker.auth.rbac import RBAC

def test_rbac_grant_revoke_list_and_check():
    r = RBAC()
    r.grant("alice", "read:context")
    assert r.has_permission("alice", "read:context")
    assert "read:context" in r.list_permissions("alice")
    r.revoke("alice", "read:context")
    assert not r.has_permission("alice", "read:context")
