import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from socialseed_tasker.secrets.crypto import decrypt, encrypt


def test_encrypt_decrypt_roundtrip():
    b = b"supersecret"
    c = encrypt(b)
    p = decrypt(c)
    assert p == b


def test_encrypt_decrypt_empty():
    b = b""
    c = encrypt(b)
    p = decrypt(c)
    assert p == b


def test_encrypt_decrypt_long():
    b = b"x" * 10000
    c = encrypt(b)
    p = decrypt(c)
    assert p == b


def test_encrypt_produces_different_ciphertexts():
    b = b"secret"
    c1 = encrypt(b)
    c2 = encrypt(b)
    # With random nonce, ciphertexts differ
    assert c1 != c2


def test_decrypt_wrong_ciphertext_fails():
    import pytest

    b = b"secret"
    c = encrypt(b)
    tampered = bytearray(c)
    tampered[0] ^= 0xFF
    with pytest.raises(Exception):
        decrypt(bytes(tampered))
