"""
Configuration loading for Supabase client.

Handles environment variable parsing and configuration
defaults for Supabase client initialization.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class SupabaseConfig:
    """Configuration for Supabase client."""

    # Connection settings
    url: str
    key: str
    db_url: str | None
    enabled: bool

    # Pool configuration
    pool_min_size: int
    pool_max_size: int
    pool_idle_timeout: int

    # Timeout configuration
    read_timeout: float
    write_timeout: float
    connectivity_test_timeout: float
    max_retries: int
    max_concurrent_operations: int


def load_config() -> SupabaseConfig:
    """
    Load Supabase configuration from environment variables.

    Returns:
        SupabaseConfig with all settings loaded from environment

    """
    return SupabaseConfig(
        url=os.getenv("SUPABASE_URL", ""),
        key=os.getenv("SUPABASE_KEY", ""),
        db_url=os.getenv("SUPABASE_DB_URL"),
        enabled=os.getenv("SUPABASE_ENABLED", "true").lower() == "true",
        pool_min_size=int(os.getenv("SUPABASE_POOL_MIN_SIZE", "2")),
        pool_max_size=int(os.getenv("SUPABASE_POOL_MAX_SIZE", "10")),
        pool_idle_timeout=int(os.getenv("SUPABASE_POOL_IDLE_TIMEOUT", "300")),
        read_timeout=float(os.getenv("DATABASE_READ_TIMEOUT", "2.0")),
        write_timeout=float(os.getenv("DATABASE_WRITE_TIMEOUT", "5.0")),
        connectivity_test_timeout=float(os.getenv("SUPABASE_CONNECTIVITY_TEST_TIMEOUT", "5.0")),
        max_retries=int(os.getenv("SUPABASE_MAX_RETRIES", "1")),
        max_concurrent_operations=int(os.getenv("SUPABASE_MAX_CONCURRENT_OPERATIONS", "10")),
    )
