"""
Hashing utilities for OPSVI Foundation.

Provides comprehensive hashing functionality with multiple algorithms.
"""

import hashlib
import hmac
import logging
import secrets
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

import argon2
import bcrypt

logger = logging.getLogger(__name__)


class HashAlgorithm(Enum):
    """Supported hashing algorithms."""

    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    SHA512 = "sha512"
    BLAKE2B = "blake2b"
    BLAKE2S = "blake2s"
    SHA3_256 = "sha3_256"
    SHA3_512 = "sha3_512"
    BCRYPT = "bcrypt"
    ARGON2 = "argon2"


class HashingError(Exception):
    """Exception raised when hashing operations fail."""


class HashVerificationError(Exception):
    """Exception raised when hash verification fails."""


class Hasher(ABC):
    """Abstract base class for hashers."""

    def __init__(self, algorithm: HashAlgorithm) -> None:
        self.algorithm = algorithm

    @abstractmethod
    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data."""

    @abstractmethod
    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against hash."""

    @abstractmethod
    def is_secure(self) -> bool:
        """Check if the hashing algorithm is secure for passwords."""


class MD5Hasher(Hasher):
    """MD5 hasher implementation (not secure for passwords)."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.MD5)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using MD5."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.md5(data).hexdigest()
        except Exception as e:
            raise HashingError(f"MD5 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against MD5 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"MD5 verification failed: {e}")

    def is_secure(self) -> bool:
        """MD5 is not secure for passwords."""
        return False


class SHA1Hasher(Hasher):
    """SHA1 hasher implementation (not secure for passwords)."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.SHA1)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using SHA1."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.sha1(data).hexdigest()
        except Exception as e:
            raise HashingError(f"SHA1 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against SHA1 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"SHA1 verification failed: {e}")

    def is_secure(self) -> bool:
        """SHA1 is not secure for passwords."""
        return False


class SHA256Hasher(Hasher):
    """SHA256 hasher implementation."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.SHA256)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using SHA256."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.sha256(data).hexdigest()
        except Exception as e:
            raise HashingError(f"SHA256 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against SHA256 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"SHA256 verification failed: {e}")

    def is_secure(self) -> bool:
        """SHA256 is secure for general hashing but not for passwords."""
        return False


class SHA512Hasher(Hasher):
    """SHA512 hasher implementation."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.SHA512)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using SHA512."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.sha512(data).hexdigest()
        except Exception as e:
            raise HashingError(f"SHA512 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against SHA512 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"SHA512 verification failed: {e}")

    def is_secure(self) -> bool:
        """SHA512 is secure for general hashing but not for passwords."""
        return False


class Blake2bHasher(Hasher):
    """Blake2b hasher implementation."""

    def __init__(self, digest_size: int = 64) -> None:
        super().__init__(HashAlgorithm.BLAKE2B)
        self.digest_size = digest_size

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using Blake2b."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            digest_size = kwargs.get("digest_size", self.digest_size)
            return hashlib.blake2b(data, digest_size=digest_size).hexdigest()
        except Exception as e:
            raise HashingError(f"Blake2b hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against Blake2b hash."""
        try:
            computed_hash = self.hash(data, **kwargs)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"Blake2b verification failed: {e}")

    def is_secure(self) -> bool:
        """Blake2b is secure for general hashing but not for passwords."""
        return False


class Blake2sHasher(Hasher):
    """Blake2s hasher implementation."""

    def __init__(self, digest_size: int = 32) -> None:
        super().__init__(HashAlgorithm.BLAKE2S)
        self.digest_size = digest_size

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using Blake2s."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            digest_size = kwargs.get("digest_size", self.digest_size)
            return hashlib.blake2s(data, digest_size=digest_size).hexdigest()
        except Exception as e:
            raise HashingError(f"Blake2s hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against Blake2s hash."""
        try:
            computed_hash = self.hash(data, **kwargs)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"Blake2s verification failed: {e}")

    def is_secure(self) -> bool:
        """Blake2s is secure for general hashing but not for passwords."""
        return False


class SHA3_256Hasher(Hasher):
    """SHA3-256 hasher implementation."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.SHA3_256)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using SHA3-256."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.sha3_256(data).hexdigest()
        except Exception as e:
            raise HashingError(f"SHA3-256 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against SHA3-256 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"SHA3-256 verification failed: {e}")

    def is_secure(self) -> bool:
        """SHA3-256 is secure for general hashing but not for passwords."""
        return False


class SHA3_512Hasher(Hasher):
    """SHA3-512 hasher implementation."""

    def __init__(self) -> None:
        super().__init__(HashAlgorithm.SHA3_512)

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using SHA3-512."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            return hashlib.sha3_512(data).hexdigest()
        except Exception as e:
            raise HashingError(f"SHA3-512 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against SHA3-512 hash."""
        try:
            computed_hash = self.hash(data)
            return hmac.compare_digest(computed_hash, hash_value)
        except Exception as e:
            raise HashVerificationError(f"SHA3-512 verification failed: {e}")

    def is_secure(self) -> bool:
        """SHA3-512 is secure for general hashing but not for passwords."""
        return False


class BcryptHasher(Hasher):
    """Bcrypt hasher implementation (secure for passwords)."""

    def __init__(self, rounds: int = 12) -> None:
        super().__init__(HashAlgorithm.BCRYPT)
        self.rounds = rounds

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using bcrypt."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            rounds = kwargs.get("rounds", self.rounds)
            salt = bcrypt.gensalt(rounds=rounds)
            return bcrypt.hashpw(data, salt).decode("utf-8")
        except Exception as e:
            raise HashingError(f"Bcrypt hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against bcrypt hash."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")
            if isinstance(hash_value, str):
                hash_value = hash_value.encode("utf-8")
            return bcrypt.checkpw(data, hash_value)
        except Exception as e:
            raise HashVerificationError(f"Bcrypt verification failed: {e}")

    def is_secure(self) -> bool:
        """Bcrypt is secure for passwords."""
        return True


class Argon2Hasher(Hasher):
    """Argon2 hasher implementation (secure for passwords)."""

    def __init__(
        self,
        time_cost: int = 3,
        memory_cost: int = 65536,
        parallelism: int = 4,
    ) -> None:
        super().__init__(HashAlgorithm.ARGON2)
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self._hasher = argon2.PasswordHasher(
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
        )

    def hash(self, data: str | bytes, **kwargs) -> str:
        """Hash data using Argon2."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            return self._hasher.hash(data)
        except Exception as e:
            raise HashingError(f"Argon2 hashing failed: {e}")

    def verify(self, data: str | bytes, hash_value: str, **kwargs) -> bool:
        """Verify data against Argon2 hash."""
        try:
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            self._hasher.verify(hash_value, data)
            return True
        except argon2.exceptions.VerifyMismatchError:
            return False
        except Exception as e:
            raise HashVerificationError(f"Argon2 verification failed: {e}")

    def is_secure(self) -> bool:
        """Argon2 is secure for passwords."""
        return True


class HashingManager:
    """Manager for handling multiple hashing algorithms."""

    def __init__(self) -> None:
        self.hashers: dict[HashAlgorithm, Hasher] = {
            HashAlgorithm.MD5: MD5Hasher(),
            HashAlgorithm.SHA1: SHA1Hasher(),
            HashAlgorithm.SHA256: SHA256Hasher(),
            HashAlgorithm.SHA512: SHA512Hasher(),
            HashAlgorithm.BLAKE2B: Blake2bHasher(),
            HashAlgorithm.BLAKE2S: Blake2sHasher(),
            HashAlgorithm.SHA3_256: SHA3_256Hasher(),
            HashAlgorithm.SHA3_512: SHA3_512Hasher(),
            HashAlgorithm.BCRYPT: BcryptHasher(),
            HashAlgorithm.ARGON2: Argon2Hasher(),
        }
        self._default_algorithm = HashAlgorithm.SHA256

    def get_hasher(self, algorithm: HashAlgorithm) -> Hasher:
        """Get a hasher for the specified algorithm."""
        if algorithm not in self.hashers:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
        return self.hashers[algorithm]

    def register_hasher(self, algorithm: HashAlgorithm, hasher: Hasher) -> None:
        """Register a custom hasher."""
        self.hashers[algorithm] = hasher
        logger.info(f"Registered custom hasher for algorithm: {algorithm}")

    def set_default_algorithm(self, algorithm: HashAlgorithm) -> None:
        """Set the default hashing algorithm."""
        if algorithm not in self.hashers:
            raise ValueError(f"Unsupported hashing algorithm: {algorithm}")
        self._default_algorithm = algorithm
        logger.info(f"Set default hashing algorithm: {algorithm}")

    def get_default_algorithm(self) -> HashAlgorithm:
        """Get the default hashing algorithm."""
        return self._default_algorithm

    def hash(
        self,
        data: str | bytes,
        algorithm: HashAlgorithm | None = None,
        **kwargs,
    ) -> str:
        """Hash data using the specified algorithm."""
        algorithm = algorithm or self._default_algorithm
        hasher = self.get_hasher(algorithm)
        return hasher.hash(data, **kwargs)

    def verify(
        self,
        data: str | bytes,
        hash_value: str,
        algorithm: HashAlgorithm | None = None,
        **kwargs,
    ) -> bool:
        """Verify data against hash using the specified algorithm."""
        algorithm = algorithm or self._default_algorithm
        hasher = self.get_hasher(algorithm)
        return hasher.verify(data, hash_value, **kwargs)

    def get_secure_algorithms(self) -> list[HashAlgorithm]:
        """Get list of algorithms secure for password hashing."""
        return [algo for algo in self.hashers.keys() if self.hashers[algo].is_secure()]


# Global hashing manager
hashing_manager = HashingManager()


# Convenience functions


def hash_data(
    data: str | bytes,
    algorithm: HashAlgorithm | None = None,
    **kwargs,
) -> str:
    """Hash data using the global hashing manager."""
    return hashing_manager.hash(data, algorithm, **kwargs)


def verify_hash(
    data: str | bytes,
    hash_value: str,
    algorithm: HashAlgorithm | None = None,
    **kwargs,
) -> bool:
    """Verify hash using the global hashing manager."""
    return hashing_manager.verify(data, hash_value, algorithm, **kwargs)


def hash_password(
    password: str,
    algorithm: HashAlgorithm = HashAlgorithm.ARGON2,
    **kwargs,
) -> str:
    """Hash a password using a secure algorithm."""
    if not hashing_manager.get_hasher(algorithm).is_secure():
        raise HashingError(f"Algorithm {algorithm} is not secure for passwords")
    return hashing_manager.hash(password, algorithm, **kwargs)


def verify_password(
    password: str,
    hash_value: str,
    algorithm: HashAlgorithm = HashAlgorithm.ARGON2,
    **kwargs,
) -> bool:
    """Verify a password against its hash."""
    if not hashing_manager.get_hasher(algorithm).is_secure():
        raise HashingError(f"Algorithm {algorithm} is not secure for passwords")
    return hashing_manager.verify(password, hash_value, algorithm, **kwargs)


def generate_salt(length: int = 32) -> str:
    """Generate a random salt."""
    return secrets.token_hex(length)


def generate_hmac(
    data: str | bytes,
    key: str | bytes,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
) -> str:
    """Generate HMAC for data with key."""
    try:
        if isinstance(data, str):
            data = data.encode("utf-8")
        if isinstance(key, str):
            key = key.encode("utf-8")

        if algorithm == HashAlgorithm.SHA256:
            return hmac.new(key, data, hashlib.sha256).hexdigest()
        if algorithm == HashAlgorithm.SHA512:
            return hmac.new(key, data, hashlib.sha512).hexdigest()
        if algorithm == HashAlgorithm.SHA1:
            return hmac.new(key, data, hashlib.sha1).hexdigest()
        raise ValueError(f"HMAC not supported for algorithm: {algorithm}")
    except Exception as e:
        raise HashingError(f"HMAC generation failed: {e}")


def verify_hmac(
    data: str | bytes,
    key: str | bytes,
    hmac_value: str,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
) -> bool:
    """Verify HMAC for data with key."""
    try:
        computed_hmac = generate_hmac(data, key, algorithm)
        return hmac.compare_digest(computed_hmac, hmac_value)
    except Exception as e:
        raise HashVerificationError(f"HMAC verification failed: {e}")


# File hashing utilities


def hash_file(
    file_path: str,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
    chunk_size: int = 8192,
) -> str:
    """Hash a file using the specified algorithm."""
    try:
        hasher = hashing_manager.get_hasher(algorithm)

        if algorithm in [HashAlgorithm.BCRYPT, HashAlgorithm.ARGON2]:
            raise HashingError(
                f"Algorithm {algorithm} is not suitable for file hashing",
            )

        # Use the underlying hashlib object for streaming
        if algorithm == HashAlgorithm.SHA256:
            hash_obj = hashlib.sha256()
        elif algorithm == HashAlgorithm.SHA512:
            hash_obj = hashlib.sha512()
        elif algorithm == HashAlgorithm.SHA1:
            hash_obj = hashlib.sha1()
        elif algorithm == HashAlgorithm.MD5:
            hash_obj = hashlib.md5()
        elif algorithm == HashAlgorithm.BLAKE2B:
            hash_obj = hashlib.blake2b()
        elif algorithm == HashAlgorithm.BLAKE2S:
            hash_obj = hashlib.blake2s()
        elif algorithm == HashAlgorithm.SHA3_256:
            hash_obj = hashlib.sha3_256()
        elif algorithm == HashAlgorithm.SHA3_512:
            hash_obj = hashlib.sha3_512()
        else:
            raise ValueError(f"Unsupported algorithm for file hashing: {algorithm}")

        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()
    except Exception as e:
        raise HashingError(f"File hashing failed: {e}")


def verify_file_hash(
    file_path: str,
    expected_hash: str,
    algorithm: HashAlgorithm = HashAlgorithm.SHA256,
) -> bool:
    """Verify a file's hash."""
    try:
        actual_hash = hash_file(file_path, algorithm)
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception as e:
        raise HashVerificationError(f"File hash verification failed: {e}")


# Hash analysis utilities


def analyze_hash(hash_value: str) -> dict[str, Any]:
    """Analyze a hash value to determine its properties."""
    analysis = {
        "length": len(hash_value),
        "format": "unknown",
        "algorithm": "unknown",
        "likely_secure": False,
    }

    # Try to identify the algorithm based on length and format
    if len(hash_value) == 32 and all(
        c in "0123456789abcdef" for c in hash_value.lower()
    ):
        analysis["format"] = "hex"
        analysis["algorithm"] = "MD5"
        analysis["likely_secure"] = False
    elif len(hash_value) == 40 and all(
        c in "0123456789abcdef" for c in hash_value.lower()
    ):
        analysis["format"] = "hex"
        analysis["algorithm"] = "SHA1"
        analysis["likely_secure"] = False
    elif len(hash_value) == 64 and all(
        c in "0123456789abcdef" for c in hash_value.lower()
    ):
        analysis["format"] = "hex"
        analysis["algorithm"] = "SHA256"
        analysis["likely_secure"] = False
    elif len(hash_value) == 128 and all(
        c in "0123456789abcdef" for c in hash_value.lower()
    ):
        analysis["format"] = "hex"
        analysis["algorithm"] = "SHA512"
        analysis["likely_secure"] = False
    elif hash_value.startswith("$2b$") or hash_value.startswith("$2a$"):
        analysis["format"] = "bcrypt"
        analysis["algorithm"] = "BCRYPT"
        analysis["likely_secure"] = True
    elif hash_value.startswith("$argon2"):
        analysis["format"] = "argon2"
        analysis["algorithm"] = "ARGON2"
        analysis["likely_secure"] = True

    return analysis


def is_secure_hash(hash_value: str) -> bool:
    """Check if a hash appears to be from a secure algorithm."""
    analysis = analyze_hash(hash_value)
    return analysis["likely_secure"]


def get_hash_info(hash_value: str) -> dict[str, Any]:
    """Get detailed information about a hash value."""
    analysis = analyze_hash(hash_value)

    # Add additional information
    info = {
        "hash": hash_value,
        "length": analysis["length"],
        "format": analysis["format"],
        "algorithm": analysis["algorithm"],
        "secure_for_passwords": analysis["likely_secure"],
        "recommendations": [],
    }

    if not analysis["likely_secure"]:
        info["recommendations"].append(
            "Consider using Argon2 or bcrypt for password hashing",
        )

    if analysis["algorithm"] in ["MD5", "SHA1"]:
        info["recommendations"].append("This algorithm is cryptographically broken")

    return info
