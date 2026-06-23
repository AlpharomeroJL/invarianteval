from __future__ import annotations

import pytest

pytestmark = pytest.mark.platform


def test_password_roundtrip():
    from server.auth_password import hash_password, verify_password

    stored = hash_password("admin")
    assert verify_password("admin", stored)
    assert not verify_password("wrong", stored)
