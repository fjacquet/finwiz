"""
Encryption utilities for sensitive data in Supabase.

Provides field-level encryption for portfolio holdings and values.
"""

import base64
import logging
import os
from typing import Any

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Raised when encryption/decryption operations fail."""

    pass


class EncryptionService:
    """Service for encrypting and decrypting sensitive portfolio data."""

    # Fields that should be encrypted in portfolio data
    SENSITIVE_FIELDS = {"holdings", "total_value", "quantity", "current_value", "cost_basis", "unrealized_gain_loss"}

    def __init__(self):
        """Initialize encryption service with key from environment."""
        self.encryption_key = self._get_encryption_key()
        self.cipher = self._initialize_cipher()

    def _get_encryption_key(self) -> str:
        """
        Get encryption key from environment variable.

        Returns:
            Encryption key string

        Raises:
            EncryptionError: If encryption key is not configured

        """
        key = os.getenv("SUPABASE_ENCRYPTION_KEY")
        if not key:
            raise EncryptionError("SUPABASE_ENCRYPTION_KEY environment variable not set. Encryption is required for sensitive portfolio data.")

        # Validate key length (minimum 32 characters for security)
        if len(key) < 32:
            raise EncryptionError("SUPABASE_ENCRYPTION_KEY must be at least 32 characters long")

        return key

    def _initialize_cipher(self) -> Fernet:
        """
        Initialize Fernet cipher with derived key.

        Returns:
            Fernet cipher instance

        """
        # Derive a proper Fernet key from the encryption key
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"finwiz_supabase_salt",  # Static salt for consistency
            iterations=100000,
        )
        key_bytes = kdf.derive(self.encryption_key.encode())
        fernet_key = base64.urlsafe_b64encode(key_bytes)

        return Fernet(fernet_key)

    def encrypt_value(self, value: Any) -> str:
        """
        Encrypt a single value.

        Args:
            value: Value to encrypt (will be converted to string)

        Returns:
            Base64-encoded encrypted string

        Raises:
            EncryptionError: If encryption fails

        """
        try:
            # Convert value to string for encryption
            value_str = str(value)
            value_bytes = value_str.encode("utf-8")

            # Encrypt and return base64-encoded string
            encrypted_bytes = self.cipher.encrypt(value_bytes)
            return encrypted_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Failed to encrypt value: {e}") from e

    def decrypt_value(self, encrypted_value: str) -> str:
        """
        Decrypt a single value.

        Args:
            encrypted_value: Base64-encoded encrypted string

        Returns:
            Decrypted string value

        Raises:
            EncryptionError: If decryption fails

        """
        try:
            # Decrypt from base64-encoded string
            encrypted_bytes = encrypted_value.encode("utf-8")
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)

            return decrypted_bytes.decode("utf-8")

        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise EncryptionError(f"Failed to decrypt value: {e}") from e

    def encrypt_sensitive_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Encrypt sensitive fields in portfolio data.

        Args:
            data: Dictionary containing portfolio data

        Returns:
            Dictionary with sensitive fields encrypted

        Example:
            >>> service = EncryptionService()
            >>> portfolio = {"ticker": "AAPL", "quantity": 100, "current_value": 15000.50}
            >>> encrypted = service.encrypt_sensitive_fields(portfolio)
            >>> # quantity and current_value are now encrypted strings

        """
        encrypted_data = data.copy()

        for field in self.SENSITIVE_FIELDS:
            if field in encrypted_data and encrypted_data[field] is not None:
                try:
                    # Handle nested dictionaries (like holdings)
                    if isinstance(encrypted_data[field], dict):
                        encrypted_data[field] = self._encrypt_dict(encrypted_data[field])
                    # Handle lists (like array of holdings)
                    elif isinstance(encrypted_data[field], list):
                        encrypted_data[field] = self._encrypt_list(encrypted_data[field])
                    # Handle simple values
                    else:
                        encrypted_data[field] = self.encrypt_value(encrypted_data[field])

                except EncryptionError as e:
                    logger.warning(f"Failed to encrypt field '{field}': {e}")
                    # Keep original value if encryption fails
                    continue

        return encrypted_data

    def decrypt_sensitive_fields(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Decrypt sensitive fields in portfolio data.

        Args:
            data: Dictionary containing encrypted portfolio data

        Returns:
            Dictionary with sensitive fields decrypted

        Example:
            >>> service = EncryptionService()
            >>> encrypted_portfolio = {
            ...     "ticker": "AAPL",
            ...     "quantity": "gAAAAABf...",  # encrypted
            ...     "current_value": "gAAAAABf...",  # encrypted
            ... }
            >>> decrypted = service.decrypt_sensitive_fields(encrypted_portfolio)
            >>> # quantity and current_value are now original values

        """
        decrypted_data = data.copy()

        for field in self.SENSITIVE_FIELDS:
            if field in decrypted_data and decrypted_data[field] is not None:
                try:
                    # Handle nested dictionaries
                    if isinstance(decrypted_data[field], dict):
                        decrypted_data[field] = self._decrypt_dict(decrypted_data[field])
                    # Handle lists
                    elif isinstance(decrypted_data[field], list):
                        decrypted_data[field] = self._decrypt_list(decrypted_data[field])
                    # Handle simple values (encrypted strings)
                    elif isinstance(decrypted_data[field], str):
                        decrypted_value = self.decrypt_value(decrypted_data[field])
                        # Try to convert back to original type
                        decrypted_data[field] = self._parse_decrypted_value(decrypted_value)

                except EncryptionError as e:
                    logger.warning(f"Failed to decrypt field '{field}': {e}")
                    # Keep encrypted value if decryption fails
                    continue

        return decrypted_data

    def _encrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively encrypt sensitive fields in nested dictionary."""
        encrypted = {}
        for key, value in data.items():
            if key in self.SENSITIVE_FIELDS and value is not None:
                if isinstance(value, dict):
                    encrypted[key] = self._encrypt_dict(value)
                elif isinstance(value, list):
                    encrypted[key] = self._encrypt_list(value)
                else:
                    encrypted[key] = self.encrypt_value(value)
            else:
                encrypted[key] = value
        return encrypted

    def _decrypt_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively decrypt sensitive fields in nested dictionary."""
        decrypted = {}
        for key, value in data.items():
            if key in self.SENSITIVE_FIELDS and value is not None:
                if isinstance(value, dict):
                    decrypted[key] = self._decrypt_dict(value)
                elif isinstance(value, list):
                    decrypted[key] = self._decrypt_list(value)
                elif isinstance(value, str):
                    decrypted_value = self.decrypt_value(value)
                    decrypted[key] = self._parse_decrypted_value(decrypted_value)
                else:
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted

    def _encrypt_list(self, data: list[Any]) -> list[Any]:
        """Encrypt items in a list."""
        encrypted = []
        for item in data:
            if isinstance(item, dict):
                encrypted.append(self._encrypt_dict(item))
            elif isinstance(item, list):
                encrypted.append(self._encrypt_list(item))
            else:
                encrypted.append(self.encrypt_value(item))
        return encrypted

    def _decrypt_list(self, data: list[Any]) -> list[Any]:
        """Decrypt items in a list."""
        decrypted = []
        for item in data:
            if isinstance(item, dict):
                decrypted.append(self._decrypt_dict(item))
            elif isinstance(item, list):
                decrypted.append(self._decrypt_list(item))
            elif isinstance(item, str):
                decrypted_value = self.decrypt_value(item)
                decrypted.append(self._parse_decrypted_value(decrypted_value))
            else:
                decrypted.append(item)
        return decrypted

    def _parse_decrypted_value(self, value: str) -> Any:
        """
        Parse decrypted string back to original type.

        Args:
            value: Decrypted string value

        Returns:
            Value converted to appropriate type (int, float, or str)

        """
        # Try to convert to numeric types
        try:
            # Try integer first
            if "." not in value:
                return int(value)
            # Try float
            return float(value)
        except ValueError:
            # Return as string if not numeric
            return value


# Global encryption service instance
_encryption_service: EncryptionService | None = None


def get_encryption_service() -> EncryptionService:
    """
    Get or create global encryption service instance.

    Returns:
        EncryptionService instance

    Raises:
        EncryptionError: If encryption key is not configured

    """
    global _encryption_service

    if _encryption_service is None:
        _encryption_service = EncryptionService()

    return _encryption_service


def encrypt_sensitive_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to encrypt sensitive fields.

    Args:
        data: Dictionary containing portfolio data

    Returns:
        Dictionary with sensitive fields encrypted

    """
    service = get_encryption_service()
    return service.encrypt_sensitive_fields(data)


def decrypt_sensitive_fields(data: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to decrypt sensitive fields.

    Args:
        data: Dictionary containing encrypted portfolio data

    Returns:
        Dictionary with sensitive fields decrypted

    """
    service = get_encryption_service()
    return service.decrypt_sensitive_fields(data)
