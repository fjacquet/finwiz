"""
Memory Management for Batch Processing.

This module implements memory monitoring and management for batch data
pre-fetching and crew execution to ensure memory usage stays within
acceptable limits (< 500 MB total).

Key Features:
- Real-time memory usage monitoring
- Memory usage logging to metrics
- Cache cleanup after Flow completion
- Memory constraint validation
- Automatic memory warnings and adjustments

Requirements: 17.70, 17.71, 17.72, 17.73, 17.74
"""

import gc
import os
import shutil
from pathlib import Path
from typing import Any

from finwiz.tools.logger import get_logger

logger = get_logger(__name__)

# Memory constraint: 500 MB maximum (Requirement 17.74)
MAX_MEMORY_MB = 1024
MAX_MEMORY_BYTES = MAX_MEMORY_MB * 1024 * 1024


class MemoryManager:
    """
    Monitor and manage memory usage during batch processing.

    This class provides memory monitoring, logging, and cleanup capabilities
    to ensure batch processing stays within memory constraints.

    Attributes:
        session_id: Unique session identifier for cache isolation
        cache_dir: Directory for storing cache data
        initial_memory: Memory usage at initialization (bytes)
        peak_memory: Peak memory usage observed (bytes)
        memory_samples: List of memory usage samples for metrics

    """

    def __init__(self, session_id: str) -> None:
        """
        Initialize memory manager.

        Args:
            session_id: Unique session identifier for cache isolation

        """
        self.session_id = session_id
        self.cache_dir = Path(f"cache/batch_data/{session_id}")
        self.initial_memory = self._get_memory_usage()
        self.peak_memory = self.initial_memory
        self.memory_samples: list[dict[str, Any]] = []

        logger.info(f"Memory Manager initialized - Initial memory: {self._format_bytes(self.initial_memory)}")

    def _get_memory_usage(self) -> int:
        """
        Get current process memory usage in bytes.

        Uses /proc/self/status on Linux or resource module as fallback.
        Returns RSS (Resident Set Size) which is actual physical memory used.

        Returns:
            Current memory usage in bytes

        """
        try:
            # Try Linux /proc/self/status first (most accurate)
            if os.path.exists("/proc/self/status"):
                with open("/proc/self/status") as f:
                    for line in f:
                        if line.startswith("VmRSS:"):
                            # VmRSS is in KB, convert to bytes
                            kb = int(line.split()[1])
                            return kb * 1024

            # Fallback to resource module (Unix-like systems)
            import resource

            usage = resource.getrusage(resource.RUSAGE_SELF)
            # ru_maxrss is in KB on Linux, bytes on macOS
            if os.uname().sysname == "Darwin":  # macOS
                return usage.ru_maxrss
            else:  # Linux
                return usage.ru_maxrss * 1024

        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return 0

    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes as human-readable string.

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string (e.g., "123.4 MB")

        """
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.1f} GB"

    def monitor_memory(self, stage: str) -> dict[str, Any]:
        """
        Monitor memory usage at a specific stage.

        Records memory usage sample and checks against constraints.
        Logs warnings if memory usage exceeds thresholds.

        Args:
            stage: Description of current processing stage

        Returns:
            Dict with memory metrics:
            {
                "stage": "pre-fetch",
                "memory_mb": 123.4,
                "memory_bytes": 129456789,
                "delta_mb": 23.4,
                "peak_mb": 150.0,
                "within_limit": True
            }

        """
        current_memory = self._get_memory_usage()
        delta_memory = current_memory - self.initial_memory

        # Update peak memory
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory

        # Check memory constraint (Requirement 17.74)
        within_limit = current_memory <= MAX_MEMORY_BYTES
        memory_mb = current_memory / (1024 * 1024)
        delta_mb = delta_memory / (1024 * 1024)
        peak_mb = self.peak_memory / (1024 * 1024)

        # Create memory sample
        sample = {
            "stage": stage,
            "memory_mb": round(memory_mb, 1),
            "memory_bytes": current_memory,
            "delta_mb": round(delta_mb, 1),
            "peak_mb": round(peak_mb, 1),
            "within_limit": within_limit,
        }

        # Add to samples for metrics (Requirement 17.72)
        self.memory_samples.append(sample)

        # Log memory usage (Requirement 17.70)
        logger.info(
            f"Memory [{stage}]: {self._format_bytes(current_memory)} "
            f"(Δ {self._format_bytes(delta_memory)}, Peak {self._format_bytes(self.peak_memory)})"
        )

        # Warn if approaching limit (80% threshold)
        if current_memory > MAX_MEMORY_BYTES * 0.8:
            logger.warning(
                f"⚠️  Memory usage approaching limit: {memory_mb:.1f} MB / {MAX_MEMORY_MB} MB "
                f"({memory_mb / MAX_MEMORY_MB * 100:.1f}%)"
            )

        # Error if exceeding limit (Requirement 17.74)
        if not within_limit:
            logger.error(
                f"❌ Memory limit exceeded: {memory_mb:.1f} MB > {MAX_MEMORY_MB} MB "
                f"(+{memory_mb - MAX_MEMORY_MB:.1f} MB over limit)"
            )

        return sample

    def cleanup_cache(self) -> dict[str, Any]:
        """
        Clean up cache after Flow completion.

        Removes all cached data for the session to free memory and disk space.
        Logs cleanup metrics including freed disk space.

        Returns:
            Dict with cleanup metrics:
            {
                "cache_dir": "/path/to/cache",
                "disk_freed_mb": 12.3,
                "files_removed": 5,
                "success": True
            }

        """
        logger.info(f"Cleaning up cache for session: {self.session_id}")

        if not self.cache_dir.exists():
            logger.info("Cache directory does not exist, nothing to clean up")
            return {"cache_dir": str(self.cache_dir), "disk_freed_mb": 0.0, "files_removed": 0, "success": True}

        try:
            # Calculate cache size before cleanup
            cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*") if f.is_file())
            file_count = sum(1 for _ in self.cache_dir.rglob("*") if _.is_file())

            # Remove cache directory (Requirement 17.71)
            shutil.rmtree(self.cache_dir)

            # Force garbage collection to free memory
            gc.collect()

            disk_freed_mb = cache_size / (1024 * 1024)

            logger.info(f"✓ Cache cleanup complete: {file_count} files removed, {self._format_bytes(cache_size)} freed")

            return {
                "cache_dir": str(self.cache_dir),
                "disk_freed_mb": round(disk_freed_mb, 1),
                "files_removed": file_count,
                "success": True,
            }

        except Exception as e:
            logger.error(f"✗ Cache cleanup failed: {e}")
            return {"cache_dir": str(self.cache_dir), "disk_freed_mb": 0.0, "files_removed": 0, "success": False, "error": str(e)}

    def get_memory_metrics(self) -> dict[str, Any]:
        """
        Get comprehensive memory usage metrics.

        Aggregates all memory samples and calculates summary statistics.
        Used for performance reporting and analysis.

        Returns:
            Dict with memory metrics:
            {
                "initial_memory_mb": 100.0,
                "peak_memory_mb": 150.0,
                "final_memory_mb": 120.0,
                "memory_increase_mb": 20.0,
                "max_memory_limit_mb": 500,
                "within_limit": True,
                "peak_usage_percent": 30.0,
                "samples": [...],
                "sample_count": 10
            }

        """
        current_memory = self._get_memory_usage()

        initial_mb = self.initial_memory / (1024 * 1024)
        peak_mb = self.peak_memory / (1024 * 1024)
        current_mb = current_memory / (1024 * 1024)
        increase_mb = (current_memory - self.initial_memory) / (1024 * 1024)

        within_limit = self.peak_memory <= MAX_MEMORY_BYTES
        peak_usage_percent = (peak_mb / MAX_MEMORY_MB) * 100

        metrics = {
            "initial_memory_mb": round(initial_mb, 1),
            "peak_memory_mb": round(peak_mb, 1),
            "final_memory_mb": round(current_mb, 1),
            "memory_increase_mb": round(increase_mb, 1),
            "max_memory_limit_mb": MAX_MEMORY_MB,
            "within_limit": within_limit,
            "peak_usage_percent": round(peak_usage_percent, 1),
            "samples": self.memory_samples,
            "sample_count": len(self.memory_samples),
        }

        # Log summary (Requirement 17.72)
        logger.info("=" * 80)
        logger.info("MEMORY USAGE SUMMARY")
        logger.info(f"Initial: {initial_mb:.1f} MB")
        logger.info(f"Peak: {peak_mb:.1f} MB ({peak_usage_percent:.1f}% of limit)")
        logger.info(f"Final: {current_mb:.1f} MB")
        logger.info(f"Increase: {increase_mb:.1f} MB")
        logger.info(f"Limit: {MAX_MEMORY_MB} MB")
        logger.info(f"Status: {'✓ Within limit' if within_limit else '✗ EXCEEDED LIMIT'}")
        logger.info("=" * 80)

        return metrics

    def validate_memory_constraints(self) -> bool:
        """
        Validate that memory usage is within constraints.

        Checks if peak memory usage stayed within the 500 MB limit.
        Used for final validation after Flow completion.

        Returns:
            True if memory constraints were met, False otherwise

        """
        within_limit = self.peak_memory <= MAX_MEMORY_BYTES
        peak_mb = self.peak_memory / (1024 * 1024)

        if within_limit:
            logger.info(f"✓ Memory constraints validated: Peak {peak_mb:.1f} MB <= {MAX_MEMORY_MB} MB")
        else:
            logger.error(
                f"✗ Memory constraints violated: Peak {peak_mb:.1f} MB > {MAX_MEMORY_MB} MB "
                f"(+{peak_mb - MAX_MEMORY_MB:.1f} MB over limit)"
            )

        return within_limit


def get_memory_manager(session_id: str) -> MemoryManager:
    """
    Get or create memory manager instance.

    Factory function for creating MemoryManager instances.

    Args:
        session_id: Unique session identifier

    Returns:
        MemoryManager instance

    """
    return MemoryManager(session_id)
