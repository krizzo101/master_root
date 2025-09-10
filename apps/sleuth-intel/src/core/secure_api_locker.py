"""
Secure API Key Locker for Managing Third-Party API Credentials
Based on SecureTokenPool pattern with enhanced security for API keys
"""

import asyncio
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class APICredential:
    """Represents a secure API credential with metadata"""

    provider: str
    key_name: str
    key_value: str
    password: Optional[str] = None
    base_url: Optional[str] = None
    rate_limit: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    last_used: Optional[str] = None
    usage_count: int = 0


class SecureAPILocker:
    """Thread-safe API key locker with secure storage and rotation"""

    def __init__(self, credentials: Optional[List[APICredential]] = None):
        """Initialize API locker with optional credentials"""
        self._credentials: Dict[
            str, List[APICredential]
        ] = {}  # provider -> [credentials]
        self._credential_indices: Dict[str, int] = {}  # provider -> current index
        self._lock = Lock()
        self._usage_stats: Dict[str, Dict] = {}
        self._credential_hashes: Dict[str, str] = {}  # Map hash to safe ID for logging

        # Load credentials from various sources
        if credentials:
            self._add_credentials(credentials)
        else:
            self._load_from_environment()

    def _add_credentials(self, credentials: List[APICredential]):
        """Add credentials to locker with security checks"""
        for cred in credentials:
            if not cred.key_value or len(cred.key_value) < 10:
                logger.warning(f"Skipping invalid credential for {cred.provider}")
                continue

            # Initialize provider list if needed
            if cred.provider not in self._credentials:
                self._credentials[cred.provider] = []
                self._credential_indices[cred.provider] = 0

            # Set creation timestamp if not provided
            if not cred.created_at:
                cred.created_at = datetime.now().isoformat()

            # Store credential
            self._credentials[cred.provider].append(cred)

            # Create hash for safe logging
            cred_hash = self._hash_credential(cred.key_value)
            safe_id = f"{cred.provider}_{len(self._credentials[cred.provider])}"
            self._credential_hashes[cred_hash] = safe_id

            # Initialize usage stats
            self._usage_stats[cred_hash] = {
                "provider": cred.provider,
                "safe_id": safe_id,
                "added_at": cred.created_at,
                "usage_count": 0,
                "last_used": None,
            }

            logger.info(f"Added {safe_id} (hash: {cred_hash[:8]}...)")

    def _hash_credential(self, credential: str) -> str:
        """Create secure hash of credential for logging"""
        return hashlib.sha256(credential.encode()).hexdigest()

    def _load_from_environment(self):
        """Load credentials from environment variables or config file"""
        # Try loading from config file first
        config_path = Path.home() / ".sleuth-intel" / "credentials.json"
        if config_path.exists():
            self._load_from_config_file(config_path)
            return

        # Fall back to environment variables
        self._load_from_env_vars()

    def _load_from_config_file(self, config_path: Path):
        """Load credentials from JSON config file"""
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)

            credentials = []
            for provider, provider_data in config_data.items():
                if isinstance(provider_data, list):
                    # Multiple credentials for provider
                    for cred_data in provider_data:
                        cred = APICredential(
                            provider=provider,
                            key_name=cred_data.get("key_name", "default"),
                            key_value=cred_data["key_value"],
                            password=cred_data.get("password"),
                            base_url=cred_data.get("base_url"),
                            rate_limit=cred_data.get("rate_limit"),
                            metadata=cred_data.get("metadata", {}),
                        )
                        credentials.append(cred)
                elif isinstance(provider_data, dict):
                    # Single credential for provider
                    cred = APICredential(
                        provider=provider,
                        key_name=provider_data.get("key_name", "default"),
                        key_value=provider_data["key_value"],
                        password=provider_data.get("password"),
                        base_url=provider_data.get("base_url"),
                        rate_limit=provider_data.get("rate_limit"),
                        metadata=provider_data.get("metadata", {}),
                    )
                    credentials.append(cred)

            self._add_credentials(credentials)
            logger.info(f"Loaded {len(credentials)} credentials from config file")

        except Exception as e:
            logger.error(f"Failed to load config file {config_path}: {e}")

    def _load_from_env_vars(self):
        """Load credentials from environment variables"""
        # Look for common API key patterns
        env_patterns = {
            "enformion": ["ENFORMION_KEY", "ENFORMION_PASSWORD"],
            "truepeoplesearch": ["TRUEPEOPLESEARCH_KEY"],
            "ipqualityscore": ["IPQS_KEY", "IPQUALITYSCORE_KEY"],
            "trestle": ["TRESTLE_KEY", "TRESTLE_API_KEY"],
            "numverify": ["NUMVERIFY_KEY"],
        }

        credentials = []
        for provider, env_keys in env_patterns.items():
            for env_key in env_keys:
                key_value = os.environ.get(env_key)
                if key_value:
                    # Check for corresponding password
                    password = os.environ.get(f"{env_key}_PASSWORD")

                    cred = APICredential(
                        provider=provider,
                        key_name=env_key.lower(),
                        key_value=key_value,
                        password=password,
                    )
                    credentials.append(cred)
                    break  # Only take first found key per provider

        if credentials:
            self._add_credentials(credentials)
            logger.info(f"Loaded {len(credentials)} credentials from environment")

    def add_credential(self, credential: APICredential):
        """Add a single credential to the locker"""
        self._add_credentials([credential])

    def get_credential(self, provider: str) -> Optional[APICredential]:
        """Get next available credential for provider with round-robin rotation
        Returns: APICredential or None if no credentials available
        """
        with self._lock:
            if provider not in self._credentials or not self._credentials[provider]:
                logger.warning(f"No credentials available for provider: {provider}")
                return None

            # Get current credential
            provider_creds = self._credentials[provider]
            current_index = self._credential_indices[provider]
            credential = provider_creds[current_index]

            # Create hash for tracking
            cred_hash = self._hash_credential(credential.key_value)

            # Update usage stats
            if cred_hash in self._usage_stats:
                self._usage_stats[cred_hash]["usage_count"] += 1
                self._usage_stats[cred_hash]["last_used"] = datetime.now().isoformat()

            # Update credential usage
            credential.usage_count += 1
            credential.last_used = datetime.now().isoformat()

            # Rotate to next credential
            self._credential_indices[provider] = (current_index + 1) % len(
                provider_creds
            )

            safe_id = self._credential_hashes.get(cred_hash, "unknown")
            logger.debug(f"Allocated {safe_id} (usage #{credential.usage_count})")

            return credential

    def get_all_credentials(self, provider: str) -> List[APICredential]:
        """Get all credentials for a provider"""
        with self._lock:
            return self._credentials.get(provider, []).copy()

    def get_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self._credentials.keys())

    def get_credential_count(self, provider: Optional[str] = None) -> int:
        """Get number of credentials (total or for specific provider)"""
        if provider:
            return len(self._credentials.get(provider, []))
        return sum(len(creds) for creds in self._credentials.values())

    def get_usage_stats(self, provider: Optional[str] = None) -> Dict[str, Dict]:
        """Get usage statistics (safe for logging)"""
        with self._lock:
            stats = {}
            for cred_hash, stat_data in self._usage_stats.items():
                if provider and stat_data["provider"] != provider:
                    continue
                safe_id = stat_data["safe_id"]
                stats[safe_id] = stat_data.copy()
            return stats

    def save_credentials_encrypted(
        self, filepath: Path, encryption_key: Optional[str] = None
    ):
        """Save credentials to encrypted file"""
        if not encryption_key:
            encryption_key = os.environ.get(
                "SLEUTH_INTEL_ENCRYPTION_KEY", "default-change-me"
            )

        # Prepare data for encryption
        data = {
            "version": "1.0",
            "encrypted": True,
            "created_at": datetime.now().isoformat(),
            "providers": {},
        }

        # Encrypt credentials by provider
        for provider, creds in self._credentials.items():
            encrypted_creds = []
            for cred in creds:
                encrypted_cred = {
                    "key_name": cred.key_name,
                    "key_value": self._encrypt_string(cred.key_value, encryption_key),
                    "password": self._encrypt_string(cred.password, encryption_key)
                    if cred.password
                    else None,
                    "base_url": cred.base_url,
                    "rate_limit": cred.rate_limit,
                    "metadata": cred.metadata,
                    "created_at": cred.created_at,
                }
                encrypted_creds.append(encrypted_cred)
            data["providers"][provider] = encrypted_creds

        # Save to file
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        # Set restrictive permissions
        os.chmod(filepath, 0o600)
        logger.info(
            f"Saved {self.get_credential_count()} encrypted credentials to {filepath}"
        )

    def load_credentials_encrypted(
        self, filepath: Path, encryption_key: Optional[str] = None
    ):
        """Load credentials from encrypted file"""
        if not filepath.exists():
            logger.warning(f"Credential file not found: {filepath}")
            return

        if not encryption_key:
            encryption_key = os.environ.get(
                "SLEUTH_INTEL_ENCRYPTION_KEY", "default-change-me"
            )

        try:
            with open(filepath) as f:
                data = json.load(f)

            if not data.get("encrypted"):
                logger.error("File is not encrypted - refusing to load")
                return

            credentials = []
            for provider, encrypted_creds in data.get("providers", {}).items():
                for encrypted_cred in encrypted_creds:
                    cred = APICredential(
                        provider=provider,
                        key_name=encrypted_cred["key_name"],
                        key_value=self._decrypt_string(
                            encrypted_cred["key_value"], encryption_key
                        ),
                        password=self._decrypt_string(
                            encrypted_cred["password"], encryption_key
                        )
                        if encrypted_cred.get("password")
                        else None,
                        base_url=encrypted_cred.get("base_url"),
                        rate_limit=encrypted_cred.get("rate_limit"),
                        metadata=encrypted_cred.get("metadata", {}),
                        created_at=encrypted_cred.get("created_at"),
                    )
                    credentials.append(cred)

            self._add_credentials(credentials)
            logger.info(f"Loaded {len(credentials)} credentials from {filepath}")

        except Exception as e:
            logger.error(f"Failed to load encrypted credentials: {e}")

    def _encrypt_string(self, text: str, key: str) -> str:
        """Encrypt string using AES (simplified for demo - use proper crypto in production)"""
        if not text:
            return ""

        import base64

        # Simple XOR encryption (replace with AES in production)
        result = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return base64.b64encode("".join(result).encode()).decode()

    def _decrypt_string(self, encrypted: str, key: str) -> str:
        """Decrypt string"""
        if not encrypted:
            return ""

        import base64

        # Simple XOR decryption
        text = base64.b64decode(encrypted.encode()).decode()
        result = []
        for i, char in enumerate(text):
            key_char = key[i % len(key)]
            result.append(chr(ord(char) ^ ord(key_char)))
        return "".join(result)


class APILockerManager:
    """Singleton manager for API credentials"""

    _instance: Optional["APILockerManager"] = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global API locker"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.locker = SecureAPILocker()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "APILockerManager":
        """Get singleton instance"""
        return cls()

    def initialize_with_credentials(self, credentials: List[APICredential]):
        """Initialize locker with provided credentials"""
        for cred in credentials:
            self.locker.add_credential(cred)

    def get_credential(self, provider: str) -> Optional[APICredential]:
        """Get next credential for provider"""
        return self.locker.get_credential(provider)

    def get_locker_status(self) -> Dict:
        """Get locker status for monitoring"""
        return {
            "providers": self.locker.get_providers(),
            "total_credentials": self.locker.get_credential_count(),
            "provider_counts": {
                provider: self.locker.get_credential_count(provider)
                for provider in self.locker.get_providers()
            },
            "usage_stats": self.locker.get_usage_stats(),
        }


# Global instance for easy access
api_locker_manager = APILockerManager.get_instance()


def initialize_default_credentials():
    """Initialize with credentials from environment or config"""
    # Check for credentials file (try both names for compatibility)
    sleuth_dir = Path.home() / ".sleuth-intel"
    creds_files = [sleuth_dir / "api_keys.enc", sleuth_dir / "credentials.enc"]

    for creds_file in creds_files:
        if creds_file.exists():
            api_locker_manager.locker.load_credentials_encrypted(creds_file)
            break

    # Load from environment
    api_locker_manager.locker._load_from_environment()

    status = api_locker_manager.get_locker_status()
    logger.info(
        f"Sleuth Intel API Locker initialized: {status['total_credentials']} credentials for {len(status['providers'])} providers"
    )


# Auto-initialize on import
initialize_default_credentials()
