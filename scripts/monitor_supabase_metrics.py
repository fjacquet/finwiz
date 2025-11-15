#!/usr/bin/env python3
"""
Supabase Metrics Monitoring Script

Monitors Supabase performance metrics in real-time:
- Timeout rates
- Success rates
- Response times
- Circuit breaker state
- Cache performance

Usage:
    python scripts/monitor_supabase_metrics.py --duration 3600  # Monitor for 1 hour
    python scripts/monitor_supabase_metrics.py --continuous     # Monitor continuously
    python scripts/monitor_supabase_metrics.py --report         # Generate report from logs
"""

import argparse
import asyncio
import logging
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finwiz.supabase.client import SupabaseClient
from finwiz.supabase.repositories.analysis_repository import AnalysisRepository
from finwiz.supabase.services.cache_service import CacheService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class MetricsMonitor:
    """Monitors Supabase metrics in real-time."""

    def __init__(self):
        """Initialize monitor."""
        self.client = SupabaseClient()
        self.repository = AnalysisRepository(self.client)
        self.cache_service = CacheService(self.repository, self.client)

        self.start_time = datetime.now()
        self.samples = []
        self.alerts = []

    async def collect_sample(self) -> dict:
        """
        Collect current metrics sample.

        Returns:
            Dictionary with current metrics

        """
        health = self.client.get_health_status()
        cache_metrics = self.cache_service.get_metrics()

        sample = {
            "timestamp": datetime.now(),
            "supabase": {
                "available": health.is_available,
                "success_rate": health.success_rate,
                "avg_response_time": health.avg_response_time,
                "circuit_breaker_open": health.circuit_breaker_open,
                "timeout_count": health.timeout_count,
                "total_operations": health.total_operations,
                "successful_operations": health.successful_operations,
                "failed_operations": health.failed_operations,
            },
            "cache": {
                "hits": cache_metrics["cache_hits"],
                "misses": cache_metrics["cache_misses"],
                "hit_rate": cache_metrics["hit_rate"],
                "total_requests": cache_metrics["total_requests"],
            },
        }

        return sample

    def check_alerts(self, sample: dict):
        """
        Check for alert conditions.

        Args:
            sample: Metrics sample to check

        """
        supabase = sample["supabase"]

        # Alert: High timeout rate
        if supabase["total_operations"] > 0:
            timeout_rate = supabase["timeout_count"] / supabase["total_operations"]
            if timeout_rate > 0.10:
                alert = {
                    "timestamp": sample["timestamp"],
                    "level": "WARNING",
                    "message": f"High timeout rate: {timeout_rate:.1%} (threshold: 10%)",
                    "metric": "timeout_rate",
                    "value": timeout_rate,
                }
                self.alerts.append(alert)
                logger.warning(f"⚠️ ALERT: {alert['message']}")

        # Alert: Low success rate
        if supabase["success_rate"] < 0.90 and supabase["total_operations"] > 10:
            alert = {
                "timestamp": sample["timestamp"],
                "level": "WARNING",
                "message": f"Low success rate: {supabase['success_rate']:.1%} (threshold: 90%)",
                "metric": "success_rate",
                "value": supabase["success_rate"],
            }
            self.alerts.append(alert)
            logger.warning(f"⚠️ ALERT: {alert['message']}")

        # Alert: Circuit breaker open
        if supabase["circuit_breaker_open"]:
            alert = {
                "timestamp": sample["timestamp"],
                "level": "CRITICAL",
                "message": "Circuit breaker is OPEN - Supabase operations suspended",
                "metric": "circuit_breaker",
                "value": True,
            }
            self.alerts.append(alert)
            logger.error(f"🚨 ALERT: {alert['message']}")

        # Alert: Supabase unavailable
        if not supabase["available"]:
            alert = {"timestamp": sample["timestamp"], "level": "WARNING", "message": "Supabase is unavailable - caching disabled", "metric": "availability", "value": False}
            self.alerts.append(alert)
            logger.warning(f"⚠️ ALERT: {alert['message']}")

    def print_sample(self, sample: dict):
        """
        Print metrics sample.

        Args:
            sample: Metrics sample to print

        """
        supabase = sample["supabase"]
        cache = sample["cache"]

        # Calculate timeout rate
        timeout_rate = 0.0
        if supabase["total_operations"] > 0:
            timeout_rate = supabase["timeout_count"] / supabase["total_operations"]

        logger.info("=" * 80)
        logger.info(f"Metrics Sample - {sample['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 80)

        logger.info("Supabase:")
        logger.info(f"  Available: {supabase['available']}")
        logger.info(f"  Success Rate: {supabase['success_rate']:.1%}")
        logger.info(f"  Timeout Rate: {timeout_rate:.1%}")
        logger.info(f"  Avg Response Time: {supabase['avg_response_time']:.1f}ms")
        logger.info(f"  Circuit Breaker: {'OPEN' if supabase['circuit_breaker_open'] else 'CLOSED'}")
        logger.info(
            f"  Operations: {supabase['total_operations']} (Success: {supabase['successful_operations']}, Failed: {supabase['failed_operations']}, Timeouts: {supabase['timeout_count']})"
        )

        logger.info("Cache:")
        logger.info(f"  Hit Rate: {cache['hit_rate']:.1%}")
        logger.info(f"  Requests: {cache['total_requests']} (Hits: {cache['hits']}, Misses: {cache['misses']})")

    async def monitor(self, duration: int = None, interval: int = 60):
        """
        Monitor metrics for specified duration.

        Args:
            duration: Duration in seconds (None for continuous)
            interval: Sample interval in seconds

        """
        logger.info("Starting metrics monitoring...")
        logger.info(f"Sample interval: {interval}s")
        if duration:
            logger.info(f"Duration: {duration}s ({duration / 60:.1f} minutes)")
        else:
            logger.info("Duration: Continuous (Ctrl+C to stop)")

        # Initialize cache service
        await self.cache_service.initialize()

        end_time = None
        if duration:
            end_time = datetime.now() + timedelta(seconds=duration)

        try:
            while True:
                # Collect sample
                sample = await self.collect_sample()
                self.samples.append(sample)

                # Print sample
                self.print_sample(sample)

                # Check alerts
                self.check_alerts(sample)

                # Check if duration exceeded
                if end_time and datetime.now() >= end_time:
                    break

                # Wait for next sample
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            logger.info("\nMonitoring stopped by user")

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print monitoring summary."""
        if not self.samples:
            logger.info("No samples collected")
            return

        duration = (datetime.now() - self.start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("MONITORING SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.0f}s ({duration / 60:.1f} minutes)")
        logger.info(f"Samples: {len(self.samples)}")
        logger.info(f"Alerts: {len(self.alerts)}")

        # Calculate aggregate metrics
        total_ops = sum(s["supabase"]["total_operations"] for s in self.samples)
        total_timeouts = sum(s["supabase"]["timeout_count"] for s in self.samples)
        total_cache_requests = sum(s["cache"]["total_requests"] for s in self.samples)

        if total_ops > 0:
            avg_success_rate = sum(s["supabase"]["success_rate"] for s in self.samples) / len(self.samples)
            avg_timeout_rate = total_timeouts / total_ops if total_ops > 0 else 0
            avg_response_time = sum(s["supabase"]["avg_response_time"] for s in self.samples) / len(self.samples)

            logger.info("\nAggregate Metrics:")
            logger.info(f"  Avg Success Rate: {avg_success_rate:.1%}")
            logger.info(f"  Avg Timeout Rate: {avg_timeout_rate:.1%}")
            logger.info(f"  Avg Response Time: {avg_response_time:.1f}ms")
            logger.info(f"  Total Operations: {total_ops}")
            logger.info(f"  Total Timeouts: {total_timeouts}")

        if total_cache_requests > 0:
            avg_cache_hit_rate = sum(s["cache"]["hit_rate"] for s in self.samples) / len(self.samples)
            logger.info(f"  Avg Cache Hit Rate: {avg_cache_hit_rate:.1%}")
            logger.info(f"  Total Cache Requests: {total_cache_requests}")

        # Alert summary
        if self.alerts:
            logger.info("\nAlerts:")
            alert_counts = defaultdict(int)
            for alert in self.alerts:
                alert_counts[alert["level"]] += 1

            for level, count in alert_counts.items():
                logger.info(f"  {level}: {count}")

            logger.info("\nRecent Alerts:")
            for alert in self.alerts[-5:]:
                logger.info(f"  [{alert['timestamp'].strftime('%H:%M:%S')}] {alert['level']}: {alert['message']}")

        # Success criteria check
        logger.info("\nSuccess Criteria:")
        if total_ops > 0:
            timeout_rate = total_timeouts / total_ops
            success = timeout_rate < 0.10
            logger.info(f"  Timeout Rate < 10%: {'✅ PASS' if success else '❌ FAIL'} ({timeout_rate:.1%})")

        logger.info("=" * 80)

    def analyze_logs(self, log_file: str):
        """
        Analyze metrics from log file.

        Args:
            log_file: Path to log file

        """
        logger.info(f"Analyzing logs from: {log_file}")

        # Patterns to extract
        metrics_pattern = re.compile(
            r"Supabase Metrics: Available=(\w+), Success Rate=([\d.]+)%, "
            r"Avg Response Time=([\d.]+)ms, Circuit Breaker=(\w+), "
            r"Total Ops=(\d+), Successful=(\d+), Failed=(\d+), Timeouts=(\d+)"
        )

        cache_pattern = re.compile(
            r"Cache Metrics: Hits=(\d+), Misses=(\d+), Hit Rate=([\d.]+)%, "
            r"Total=(\d+), TTL=(\d+)h"
        )

        timeout_pattern = re.compile(r"Database operation timed out")

        metrics_samples = []
        cache_samples = []
        timeout_count = 0

        try:
            with open(log_file) as f:
                for line in f:
                    # Extract Supabase metrics
                    match = metrics_pattern.search(line)
                    if match:
                        metrics_samples.append(
                            {
                                "available": match.group(1) == "True",
                                "success_rate": float(match.group(2)) / 100,
                                "avg_response_time": float(match.group(3)),
                                "circuit_breaker": match.group(4),
                                "total_ops": int(match.group(5)),
                                "successful": int(match.group(6)),
                                "failed": int(match.group(7)),
                                "timeouts": int(match.group(8)),
                            }
                        )

                    # Extract cache metrics
                    match = cache_pattern.search(line)
                    if match:
                        cache_samples.append({"hits": int(match.group(1)), "misses": int(match.group(2)), "hit_rate": float(match.group(3)) / 100, "total": int(match.group(4))})

                    # Count timeouts
                    if timeout_pattern.search(line):
                        timeout_count += 1

        except FileNotFoundError:
            logger.error(f"Log file not found: {log_file}")
            return

        # Print analysis
        logger.info("\n" + "=" * 80)
        logger.info("LOG ANALYSIS REPORT")
        logger.info("=" * 80)
        logger.info(f"Metrics Samples: {len(metrics_samples)}")
        logger.info(f"Cache Samples: {len(cache_samples)}")
        logger.info(f"Timeout Events: {timeout_count}")

        if metrics_samples:
            latest = metrics_samples[-1]
            logger.info("\nLatest Metrics:")
            logger.info(f"  Available: {latest['available']}")
            logger.info(f"  Success Rate: {latest['success_rate']:.1%}")
            logger.info(f"  Avg Response Time: {latest['avg_response_time']:.1f}ms")
            logger.info(f"  Circuit Breaker: {latest['circuit_breaker']}")
            logger.info(f"  Total Operations: {latest['total_ops']}")
            logger.info(f"  Timeouts: {latest['timeouts']}")

            if latest["total_ops"] > 0:
                timeout_rate = latest["timeouts"] / latest["total_ops"]
                logger.info(f"  Timeout Rate: {timeout_rate:.1%}")

        if cache_samples:
            latest = cache_samples[-1]
            logger.info("\nLatest Cache Metrics:")
            logger.info(f"  Hit Rate: {latest['hit_rate']:.1%}")
            logger.info(f"  Total Requests: {latest['total']}")
            logger.info(f"  Hits: {latest['hits']}")
            logger.info(f"  Misses: {latest['misses']}")

        logger.info("=" * 80)


async def main():
    """Main monitoring entry point."""
    parser = argparse.ArgumentParser(description="Monitor Supabase metrics")
    parser.add_argument("--duration", type=int, help="Monitoring duration in seconds")
    parser.add_argument("--interval", type=int, default=60, help="Sample interval in seconds (default: 60)")
    parser.add_argument("--continuous", action="store_true", help="Monitor continuously until interrupted")
    parser.add_argument("--report", type=str, help="Generate report from log file")

    args = parser.parse_args()

    monitor = MetricsMonitor()

    if args.report:
        # Analyze logs
        monitor.analyze_logs(args.report)
    else:
        # Live monitoring
        duration = args.duration if not args.continuous else None
        await monitor.monitor(duration=duration, interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
