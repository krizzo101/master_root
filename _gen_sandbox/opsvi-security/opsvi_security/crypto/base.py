"""Crypto base for opsvi-security.

Provides an abstract-but-usable base class for symmetric cryptographic
operations. This module intentionally keeps dependencies minimal and does
not perform real cryptography by default — subclasses should override
methods to provide robust implementations.
"""
from __future__ import annotations

from typing import Optional


class Crypto:
    """Lightweight base class for crypto operations.

    The default implementation is effectively a no-op (identity) and is
    provided mainly for testing or as a clear interface. Subclasses
    should override encrypt/decrypt/sign/verify to provide secure
    algorithms.
    """

    def encrypt(self, data: bytes) -> bytes:
        """Return an encrypted representation of ``data``.

        Default implementation returns the input unchanged.
        """
        return data

    def decrypt(self, token: bytes) -> bytes:
        """Return the decrypted representation of ``token``.

        Default implementation returns the input unchanged.
        """
        return token

    def sign(self, data: bytes) -> bytes:
        """Return a signature for ``data``.

        Default implementation returns an empty signature (b'').
        """
        return b""

    def verify(self, data: bytes, signature: bytes) -> bool:
        """Verify that ``signature`` is valid for ``data``.

        Default implementation treats empty signature as valid only when
        the data is unchanged (i.e. signature == b''). Subclasses should
        implement proper verification and not rely on this.
        """
        return signature == b""


class SimpleXorCrypto(Crypto):
    """A tiny, illustrative XOR-based cipher (NOT secure).

    This class is suitable for tests and examples where deterministic and
    reversible byte transformations are useful, but it MUST NOT be used
    for real security purposes.
    """

    def __init__(self, key: bytes) -> None:
        if not key:
            raise ValueError("key must be non-empty")
        self._key = key

    def _apply_xor(self, data: bytes) -> bytes:
        k = self._key
        return bytes(b ^ k[i % len(k)] for i, b in enumerate(data))

    def encrypt(self, data: bytes) -> bytes:
        return self._apply_xor(data)

    def decrypt(self, token: bytes) -> bytes:
        # XOR is symmetric
        return self._apply_xor(token)

    def sign(self, data: bytes) -> bytes:
        # Simple HMAC-like signature using XOR plus length — NOT secure.
        digest = self._apply_xor(data)
        length = len(data) & 0xFF
        return bytes([length]) + digest[:4]

    def verify(self, data: bytes, signature: bytes) -> bool:
        expected = self.sign(data)
        return signature == expected
