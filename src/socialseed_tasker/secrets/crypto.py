from __future__ import annotations

import hashlib
import os

_CRYPTO_AVAILABLE = False
AESGCM = None

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM

    AESGCM = _AESGCM
    _CRYPTO_AVAILABLE = True
except Exception:
    pass

MASTER_KEY_HEX = os.getenv("TASKER_SECRETS_MASTER_KEY", "")
if not MASTER_KEY_HEX:
    MASTER_KEY = hashlib.sha256(b"default-tasker-secrets-key").digest()
else:
    MASTER_KEY = bytes.fromhex(MASTER_KEY_HEX)


def _derive_nonce(suffix: bytes) -> bytes:
    h = hashlib.sha256(suffix).digest()
    return h[:12]


def encrypt(
    plaintext: bytes, associated_data: bytes | None = None
) -> bytes:
    if AESGCM is None:
        msg = "cryptography package not available. Install with: pip install cryptography"
        raise ImportError(msg)
    aes = AESGCM(MASTER_KEY)
    use_random = os.getenv("TASKER_SECRETS_USE_RANDOM_NONCE", "1") == "1"
    nonce = os.urandom(12) if use_random else _derive_nonce(plaintext)
    ct = aes.encrypt(nonce, plaintext, associated_data)
    return nonce + ct


def decrypt(
    ciphertext: bytes, associated_data: bytes | None = None
) -> bytes:
    if AESGCM is None:
        msg = "cryptography package not available. Install with: pip install cryptography"
        raise ImportError(msg)
    aes = AESGCM(MASTER_KEY)
    nonce = ciphertext[:12]
    ct = ciphertext[12:]
    return aes.decrypt(nonce, ct, associated_data)
