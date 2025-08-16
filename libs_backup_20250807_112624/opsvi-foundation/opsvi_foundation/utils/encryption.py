"""
Encryption utilities for OPSVI Foundation.

Provides comprehensive encryption and decryption functionality.
"""

import base64
import logging
import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms."""

    AES = "aes"
    RSA = "rsa"
    FERNET = "fernet"
    CHACHA20 = "chacha20"


class EncryptionMode(Enum):
    """Supported encryption modes."""

    CBC = "cbc"
    GCM = "gcm"
    CTR = "ctr"


class EncryptionError(Exception):
    """Exception raised when encryption operations fail."""


class DecryptionError(Exception):
    """Exception raised when decryption operations fail."""


class KeyGenerationError(Exception):
    """Exception raised when key generation fails."""


class Encryptor(ABC):
    """Abstract base class for encryptors."""

    def __init__(self, algorithm: EncryptionAlgorithm) -> None:
        self.algorithm = algorithm

    @abstractmethod
    def generate_key(self, **kwargs) -> bytes:
        """Generate an encryption key."""

    @abstractmethod
    def encrypt(self, data: str | bytes, key: bytes, **kwargs) -> bytes:
        """Encrypt data."""

    @abstractmethod
    def decrypt(self, data: bytes, key: bytes, **kwargs) -> str | bytes:
        """Decrypt data."""

    @abstractmethod
    def is_symmetric(self) -> bool:
        """Check if the encryption is symmetric."""


class AESEncryptor(Encryptor):
    """AES encryptor implementation."""

    def __init__(
        self,
        key_size: int = 256,
        mode: EncryptionMode = EncryptionMode.GCM,
    ) -> None:
        super().__init__(EncryptionAlgorithm.AES)
        self.key_size = key_size
        self.mode = mode

    def generate_key(self, **kwargs) -> bytes:
        """Generate an AES key."""
        try:
            key_size = kwargs.get("key_size", self.key_size)
            if key_size not in [128, 192, 256]:
                raise ValueError("AES key size must be 128, 192, or 256 bits")

            return os.urandom(key_size // 8)
        except Exception as e:
            raise KeyGenerationError(f"AES key generation failed: {e}")

    def encrypt(self, data: str | bytes, key: bytes, **kwargs) -> bytes:
        """Encrypt data using AES."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            mode = kwargs.get("mode", self.mode)

            if mode == EncryptionMode.GCM:
                return self._encrypt_gcm(data, key)
            if mode == EncryptionMode.CBC:
                return self._encrypt_cbc(data, key)
            if mode == EncryptionMode.CTR:
                return self._encrypt_ctr(data, key)
            raise ValueError(f"Unsupported AES mode: {mode}")
        except Exception as e:
            raise EncryptionError(f"AES encryption failed: {e}")

    def decrypt(self, data: bytes, key: bytes, **kwargs) -> str | bytes:
        """Decrypt data using AES."""
        try:
            mode = kwargs.get("mode", self.mode)

            if mode == EncryptionMode.GCM:
                decrypted = self._decrypt_gcm(data, key)
            elif mode == EncryptionMode.CBC:
                decrypted = self._decrypt_cbc(data, key)
            elif mode == EncryptionMode.CTR:
                decrypted = self._decrypt_ctr(data, key)
            else:
                raise ValueError(f"Unsupported AES mode: {mode}")

            # Try to decode as string if possible
            try:
                return decrypted.decode("utf-8")
            except UnicodeDecodeError:
                return decrypted
        except Exception as e:
            raise DecryptionError(f"AES decryption failed: {e}")

    def _encrypt_gcm(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-GCM."""
        iv = os.urandom(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(data) + encryptor.finalize()
        tag = encryptor.tag

        # Combine IV, ciphertext, and tag
        return iv + tag + ciphertext

    def _decrypt_gcm(self, data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-GCM."""
        if len(data) < 28:  # IV (12) + tag (16)
            raise DecryptionError("Invalid encrypted data length")

        iv = data[:12]
        tag = data[12:28]
        ciphertext = data[28:]

        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag))
        decryptor = cipher.decryptor()

        return decryptor.update(ciphertext) + decryptor.finalize()

    def _encrypt_cbc(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-CBC."""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Pad data to block size
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padded_data = data + bytes([padding_length] * padding_length)

        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return iv + ciphertext

    def _decrypt_cbc(self, data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-CBC."""
        if len(data) < 16:  # IV
            raise DecryptionError("Invalid encrypted data length")

        iv = data[:16]
        ciphertext = data[16:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove padding
        padding_length = padded_data[-1]
        return padded_data[:-padding_length]

    def _encrypt_ctr(self, data: bytes, key: bytes) -> bytes:
        """Encrypt data using AES-CTR."""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
        encryptor = cipher.encryptor()

        ciphertext = encryptor.update(data) + encryptor.finalize()
        return iv + ciphertext

    def _decrypt_ctr(self, data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-CTR."""
        if len(data) < 16:  # IV
            raise DecryptionError("Invalid encrypted data length")

        iv = data[:16]
        ciphertext = data[16:]

        cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
        decryptor = cipher.decryptor()

        return decryptor.update(ciphertext) + decryptor.finalize()

    def is_symmetric(self) -> bool:
        """AES is symmetric encryption."""
        return True


class RSAEncryptor(Encryptor):
    """RSA encryptor implementation."""

    def __init__(self, key_size: int = 2048) -> None:
        super().__init__(EncryptionAlgorithm.RSA)
        self.key_size = key_size

    def generate_key(self, **kwargs) -> bytes:
        """Generate an RSA key pair."""
        try:
            key_size = kwargs.get("key_size", self.key_size)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=key_size,
            )

            # Return private key in PEM format
            return private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        except Exception as e:
            raise KeyGenerationError(f"RSA key generation failed: {e}")

    def generate_public_key(self, private_key_pem: bytes) -> bytes:
        """Generate public key from private key."""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
            )
            public_key = private_key.public_key()

            return public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        except Exception as e:
            raise KeyGenerationError(f"RSA public key generation failed: {e}")

    def encrypt(self, data: str | bytes, key: bytes, **kwargs) -> bytes:
        """Encrypt data using RSA (public key)."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            # Load public key
            public_key = serialization.load_pem_public_key(key)

            # RSA encryption
            ciphertext = public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            return ciphertext
        except Exception as e:
            raise EncryptionError(f"RSA encryption failed: {e}")

    def decrypt(self, data: bytes, key: bytes, **kwargs) -> str | bytes:
        """Decrypt data using RSA (private key)."""
        try:
            # Load private key
            private_key = serialization.load_pem_private_key(key, password=None)

            # RSA decryption
            plaintext = private_key.decrypt(
                data,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )

            # Try to decode as string if possible
            try:
                return plaintext.decode("utf-8")
            except UnicodeDecodeError:
                return plaintext
        except Exception as e:
            raise DecryptionError(f"RSA decryption failed: {e}")

    def is_symmetric(self) -> bool:
        """RSA is asymmetric encryption."""
        return False


class FernetEncryptor(Encryptor):
    """Fernet encryptor implementation."""

    def __init__(self) -> None:
        super().__init__(EncryptionAlgorithm.FERNET)

    def generate_key(self, **kwargs) -> bytes:
        """Generate a Fernet key."""
        try:
            return Fernet.generate_key()
        except Exception as e:
            raise KeyGenerationError(f"Fernet key generation failed: {e}")

    def encrypt(self, data: str | bytes, key: bytes, **kwargs) -> bytes:
        """Encrypt data using Fernet."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            fernet = Fernet(key)
            return fernet.encrypt(data)
        except Exception as e:
            raise EncryptionError(f"Fernet encryption failed: {e}")

    def decrypt(self, data: bytes, key: bytes, **kwargs) -> str | bytes:
        """Decrypt data using Fernet."""
        try:
            fernet = Fernet(key)
            decrypted = fernet.decrypt(data)

            # Try to decode as string if possible
            try:
                return decrypted.decode("utf-8")
            except UnicodeDecodeError:
                return decrypted
        except Exception as e:
            raise DecryptionError(f"Fernet decryption failed: {e}")

    def is_symmetric(self) -> bool:
        """Fernet is symmetric encryption."""
        return True


class ChaCha20Encryptor(Encryptor):
    """ChaCha20 encryptor implementation."""

    def __init__(self) -> None:
        super().__init__(EncryptionAlgorithm.CHACHA20)

    def generate_key(self, **kwargs) -> bytes:
        """Generate a ChaCha20 key."""
        try:
            return os.urandom(32)  # 256-bit key
        except Exception as e:
            raise KeyGenerationError(f"ChaCha20 key generation failed: {e}")

    def encrypt(self, data: str | bytes, key: bytes, **kwargs) -> bytes:
        """Encrypt data using ChaCha20."""
        try:
            if isinstance(data, str):
                data = data.encode("utf-8")

            nonce = os.urandom(12)
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
            encryptor = cipher.encryptor()

            ciphertext = encryptor.update(data)
            return nonce + ciphertext
        except Exception as e:
            raise EncryptionError(f"ChaCha20 encryption failed: {e}")

    def decrypt(self, data: bytes, key: bytes, **kwargs) -> str | bytes:
        """Decrypt data using ChaCha20."""
        try:
            if len(data) < 12:  # nonce
                raise DecryptionError("Invalid encrypted data length")

            nonce = data[:12]
            ciphertext = data[12:]

            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None)
            decryptor = cipher.decryptor()

            decrypted = decryptor.update(ciphertext)

            # Try to decode as string if possible
            try:
                return decrypted.decode("utf-8")
            except UnicodeDecodeError:
                return decrypted
        except Exception as e:
            raise DecryptionError(f"ChaCha20 decryption failed: {e}")

    def is_symmetric(self) -> bool:
        """ChaCha20 is symmetric encryption."""
        return True


class EncryptionManager:
    """Manager for handling multiple encryption algorithms."""

    def __init__(self) -> None:
        self.encryptors: dict[EncryptionAlgorithm, Encryptor] = {
            EncryptionAlgorithm.AES: AESEncryptor(),
            EncryptionAlgorithm.RSA: RSAEncryptor(),
            EncryptionAlgorithm.FERNET: FernetEncryptor(),
            EncryptionAlgorithm.CHACHA20: ChaCha20Encryptor(),
        }
        self._default_algorithm = EncryptionAlgorithm.AES

    def get_encryptor(self, algorithm: EncryptionAlgorithm) -> Encryptor:
        """Get an encryptor for the specified algorithm."""
        if algorithm not in self.encryptors:
            raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        return self.encryptors[algorithm]

    def register_encryptor(
        self,
        algorithm: EncryptionAlgorithm,
        encryptor: Encryptor,
    ) -> None:
        """Register a custom encryptor."""
        self.encryptors[algorithm] = encryptor
        logger.info(f"Registered custom encryptor for algorithm: {algorithm}")

    def set_default_algorithm(self, algorithm: EncryptionAlgorithm) -> None:
        """Set the default encryption algorithm."""
        if algorithm not in self.encryptors:
            raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        self._default_algorithm = algorithm
        logger.info(f"Set default encryption algorithm: {algorithm}")

    def get_default_algorithm(self) -> EncryptionAlgorithm:
        """Get the default encryption algorithm."""
        return self._default_algorithm

    def generate_key(
        self,
        algorithm: EncryptionAlgorithm | None = None,
        **kwargs,
    ) -> bytes:
        """Generate a key for the specified algorithm."""
        algorithm = algorithm or self._default_algorithm
        encryptor = self.get_encryptor(algorithm)
        return encryptor.generate_key(**kwargs)

    def encrypt(
        self,
        data: str | bytes,
        key: bytes,
        algorithm: EncryptionAlgorithm | None = None,
        **kwargs,
    ) -> bytes:
        """Encrypt data using the specified algorithm."""
        algorithm = algorithm or self._default_algorithm
        encryptor = self.get_encryptor(algorithm)
        return encryptor.encrypt(data, key, **kwargs)

    def decrypt(
        self,
        data: bytes,
        key: bytes,
        algorithm: EncryptionAlgorithm | None = None,
        **kwargs,
    ) -> str | bytes:
        """Decrypt data using the specified algorithm."""
        algorithm = algorithm or self._default_algorithm
        encryptor = self.get_encryptor(algorithm)
        return encryptor.decrypt(data, key, **kwargs)

    def get_symmetric_algorithms(self) -> list[EncryptionAlgorithm]:
        """Get list of symmetric encryption algorithms."""
        return [
            algo
            for algo in self.encryptors.keys()
            if self.encryptors[algo].is_symmetric()
        ]

    def get_asymmetric_algorithms(self) -> list[EncryptionAlgorithm]:
        """Get list of asymmetric encryption algorithms."""
        return [
            algo
            for algo in self.encryptors.keys()
            if not self.encryptors[algo].is_symmetric()
        ]


# Global encryption manager
encryption_manager = EncryptionManager()


# Convenience functions


def generate_key(algorithm: EncryptionAlgorithm | None = None, **kwargs) -> bytes:
    """Generate an encryption key using the global encryption manager."""
    return encryption_manager.generate_key(algorithm, **kwargs)


def encrypt_data(
    data: str | bytes,
    key: bytes,
    algorithm: EncryptionAlgorithm | None = None,
    **kwargs,
) -> bytes:
    """Encrypt data using the global encryption manager."""
    return encryption_manager.encrypt(data, key, algorithm, **kwargs)


def decrypt_data(
    data: bytes,
    key: bytes,
    algorithm: EncryptionAlgorithm | None = None,
    **kwargs,
) -> str | bytes:
    """Decrypt data using the global encryption manager."""
    return encryption_manager.decrypt(data, key, algorithm, **kwargs)


def encrypt_aes(
    data: str | bytes,
    key: bytes,
    mode: EncryptionMode = EncryptionMode.GCM,
) -> bytes:
    """Encrypt data using AES."""
    encryptor = AESEncryptor()
    return encryptor.encrypt(data, key, mode=mode)


def decrypt_aes(
    data: bytes,
    key: bytes,
    mode: EncryptionMode = EncryptionMode.GCM,
) -> str | bytes:
    """Decrypt data using AES."""
    encryptor = AESEncryptor()
    return encryptor.decrypt(data, key, mode=mode)


def generate_rsa_key_pair(key_size: int = 2048) -> tuple[bytes, bytes]:
    """Generate RSA key pair."""
    encryptor = RSAEncryptor()
    private_key = encryptor.generate_key(key_size=key_size)
    public_key = encryptor.generate_public_key(private_key)
    return private_key, public_key


def encrypt_rsa(data: str | bytes, public_key: bytes) -> bytes:
    """Encrypt data using RSA."""
    encryptor = RSAEncryptor()
    return encryptor.encrypt(data, public_key)


def decrypt_rsa(data: bytes, private_key: bytes) -> str | bytes:
    """Decrypt data using RSA."""
    encryptor = RSAEncryptor()
    return encryptor.decrypt(data, private_key)


def encrypt_fernet(data: str | bytes, key: bytes) -> bytes:
    """Encrypt data using Fernet."""
    encryptor = FernetEncryptor()
    return encryptor.encrypt(data, key)


def decrypt_fernet(data: bytes, key: bytes) -> str | bytes:
    """Decrypt data using Fernet."""
    encryptor = FernetEncryptor()
    return encryptor.decrypt(data, key)


def encrypt_chacha20(data: str | bytes, key: bytes) -> bytes:
    """Encrypt data using ChaCha20."""
    encryptor = ChaCha20Encryptor()
    return encryptor.encrypt(data, key)


def decrypt_chacha20(data: bytes, key: bytes) -> str | bytes:
    """Decrypt data using ChaCha20."""
    encryptor = ChaCha20Encryptor()
    return encryptor.decrypt(data, key)


# Key derivation utilities


def derive_key_from_password(
    password: str,
    salt: bytes | None = None,
    key_length: int = 32,
) -> tuple[bytes, bytes]:
    """Derive a key from a password using PBKDF2."""
    if salt is None:
        salt = os.urandom(16)

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=key_length,
        salt=salt,
        iterations=100000,
    )

    key = kdf.derive(password.encode("utf-8"))
    return key, salt


def derive_key_from_password_with_encryption(
    password: str,
    data: str | bytes,
    salt: bytes | None = None,
) -> bytes:
    """Derive a key from password and encrypt data."""
    key, salt = derive_key_from_password(password, salt)
    encrypted_data = encrypt_data(data, key)

    # Combine salt and encrypted data
    return salt + encrypted_data


def decrypt_with_password(
    password: str,
    encrypted_data: bytes,
    salt_length: int = 16,
) -> str | bytes:
    """Decrypt data using a password."""
    if len(encrypted_data) <= salt_length:
        raise DecryptionError("Invalid encrypted data length")

    salt = encrypted_data[:salt_length]
    data = encrypted_data[salt_length:]

    key, _ = derive_key_from_password(password, salt)
    return decrypt_data(data, key)


# Encoding utilities


def encode_key(key: bytes) -> str:
    """Encode a key to base64 string."""
    return base64.b64encode(key).decode("utf-8")


def decode_key(key_str: str) -> bytes:
    """Decode a key from base64 string."""
    return base64.b64decode(key_str.encode("utf-8"))


def encode_encrypted_data(data: bytes) -> str:
    """Encode encrypted data to base64 string."""
    return base64.b64encode(data).decode("utf-8")


def decode_encrypted_data(data_str: str) -> bytes:
    """Decode encrypted data from base64 string."""
    return base64.b64decode(data_str.encode("utf-8"))


# File encryption utilities


def encrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES,
) -> None:
    """Encrypt a file."""
    try:
        with open(input_path, "rb") as input_file:
            data = input_file.read()

        encrypted_data = encrypt_data(data, key, algorithm)

        with open(output_path, "wb") as output_file:
            output_file.write(encrypted_data)

        logger.info(f"Encrypted {input_path} to {output_path}")
    except Exception as e:
        raise EncryptionError(f"File encryption failed: {e}")


def decrypt_file(
    input_path: str,
    output_path: str,
    key: bytes,
    algorithm: EncryptionAlgorithm = EncryptionAlgorithm.AES,
) -> None:
    """Decrypt a file."""
    try:
        with open(input_path, "rb") as input_file:
            encrypted_data = input_file.read()

        decrypted_data = decrypt_data(encrypted_data, key, algorithm)

        if isinstance(decrypted_data, str):
            mode = "w"
            encoding = "utf-8"
        else:
            mode = "wb"
            encoding = None

        with open(output_path, mode, encoding=encoding) as output_file:
            output_file.write(decrypted_data)

        logger.info(f"Decrypted {input_path} to {output_path}")
    except Exception as e:
        raise DecryptionError(f"File decryption failed: {e}")


# Security utilities


def is_secure_algorithm(algorithm: EncryptionAlgorithm) -> bool:
    """Check if an encryption algorithm is considered secure."""
    secure_algorithms = [
        EncryptionAlgorithm.AES,
        EncryptionAlgorithm.RSA,
        EncryptionAlgorithm.FERNET,
        EncryptionAlgorithm.CHACHA20,
    ]
    return algorithm in secure_algorithms


def get_algorithm_info(algorithm: EncryptionAlgorithm) -> dict[str, Any]:
    """Get information about an encryption algorithm."""
    encryptor = encryption_manager.get_encryptor(algorithm)

    info = {
        "algorithm": algorithm.value,
        "symmetric": encryptor.is_symmetric(),
        "secure": is_secure_algorithm(algorithm),
        "description": "",
    }

    if algorithm == EncryptionAlgorithm.AES:
        info["description"] = "Advanced Encryption Standard - symmetric block cipher"
    elif algorithm == EncryptionAlgorithm.RSA:
        info["description"] = "Rivest-Shamir-Adleman - asymmetric encryption"
    elif algorithm == EncryptionAlgorithm.FERNET:
        info["description"] = "Fernet - symmetric authenticated encryption"
    elif algorithm == EncryptionAlgorithm.CHACHA20:
        info["description"] = "ChaCha20 - symmetric stream cipher"

    return info
