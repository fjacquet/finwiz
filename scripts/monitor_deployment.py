#!/usr/bin/env python3
"""
Deployment monitoring and status checking script.

This script monitors deployment status, checks site health,
and provides deployment history and statistics.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


class DeploymentMonitor:
    """Monitors deployment status and site health."""

    def __init__(self) -> None:
        self.status_file = Path("deployment_status.json")

    def check_status(self, environment: str = "production") -> dict:
        """
        Check current deployment status.

        Args:
            environment: Environment to check

        Returns:
            Dict: Status information

        """
        print(f"🔍 Checking {environment} deployment status...")

        status = {
            "environment": environment,
            "timestamp": datetime.now().isoformat(),
            "site_accessible": False,
            "last_deployment": None,
            "git_info": {},
            "site_info": {},
            "health_checks": {},
        }

        # Get Git information
        status["git_info"] = self._get_git_info(environment)

        # Check site accessibility
        site_url = self._get_site_url(environment)
        if site_url:
            status["site_info"] = self._check_site_health(site_url)
            status["site_accessible"] = status["site_info"].get("accessible", False)

        # Get deployment history
        status["deployment_history"] = self._get_deployment_history(environment)

        # Run health checks
        status["health_checks"] = self._run_health_checks(site_url)

        # Save status
        self._save_status(status)

        return status

    def _get_git_info(self, environment: str) -> dict:
        """Get Git information for the deployment branch."""
        git_info = {}

        try:
            # Determine branch name
            branch = "gh-pages-staging" if environment == "staging" else "gh-pages"

            # Get last commit info
            result = subprocess.run(["git", "log", f"origin/{branch}", "-1", "--format=%H|%an|%ae|%ad|%s"], capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split("|")
                if len(parts) >= 5:
                    git_info = {
                        "branch": branch,
                        "last_commit_hash": parts[0],
                        "last_commit_author": parts[1],
                        "last_commit_email": parts[2],
                        "last_commit_date": parts[3],
                        "last_commit_message": parts[4],
                    }

            # Get repository URL
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True)

            if result.returncode == 0:
                git_info["repository_url"] = result.stdout.strip()

        except Exception as e:
            print(f"⚠️  Could not get Git info: {e}")

        return git_info

    def _get_site_url(self, environment: str) -> str | None:
        """Get site URL for environment."""
        try:
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)

            repo_url = result.stdout.strip()

            if "github.com" in repo_url:
                parts = repo_url.replace(".git", "").split("/")
                if len(parts) >= 2:
                    owner = parts[-2]
                    repo = parts[-1]

                    if environment == "staging":
                        return f"https://{owner}.github.io/{repo}/staging/"
                    else:
                        return f"https://{owner}.github.io/{repo}/"

        except Exception as e:
            print(f"⚠️  Could not determine site URL: {e}")

        return None

    def _check_site_health(self, site_url: str) -> dict:
        """Check site health and performance."""
        site_info = {
            "url": site_url,
            "accessible": False,
            "response_time": None,
            "status_code": None,
            "content_length": None,
            "last_modified": None,
            "content_checks": {},
        }

        try:
            start_time = time.time()

            request = urllib.request.Request(site_url, headers={"User-Agent": "FinWiz-Monitor/1.0"})

            with urllib.request.urlopen(request, timeout=30) as response:
                response_time = time.time() - start_time

                site_info.update(
                    {
                        "accessible": True,
                        "response_time": round(response_time, 3),
                        "status_code": response.status,
                        "content_length": len(response.read()),
                        "last_modified": response.headers.get("Last-Modified"),
                    }
                )

                # Read content for validation
                response.seek(0)
                content = response.read().decode("utf-8")

                # Content checks
                site_info["content_checks"] = {
                    "has_title": "FinWiz Documentation" in content,
                    "has_navigation": 'class="md-nav"' in content or "nav" in content.lower(),
                    "has_search": "search" in content.lower(),
                    "has_footer": "footer" in content.lower(),
                    "content_size_kb": round(len(content) / 1024, 2),
                }

        except urllib.error.HTTPError as e:
            site_info.update({"accessible": False, "status_code": e.code, "error": str(e)})

        except Exception as e:
            site_info.update({"accessible": False, "error": str(e)})

        return site_info

    def _get_deployment_history(self, environment: str) -> list[dict]:
        """Get recent deployment history."""
        history = []

        try:
            branch = "gh-pages-staging" if environment == "staging" else "gh-pages"

            # Get last 10 commits
            result = subprocess.run(["git", "log", f"origin/{branch}", "-10", "--format=%H|%an|%ad|%s", "--date=iso"], capture_output=True, text=True)

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line.strip():
                        parts = line.split("|")
                        if len(parts) >= 4:
                            history.append({"commit_hash": parts[0], "author": parts[1], "date": parts[2], "message": parts[3]})

        except Exception as e:
            print(f"⚠️  Could not get deployment history: {e}")

        return history

    def _run_health_checks(self, site_url: str | None) -> dict:
        """Run comprehensive health checks."""
        health_checks = {"timestamp": datetime.now().isoformat(), "checks": {}}

        if not site_url:
            health_checks["checks"]["site_url"] = {"status": "failed", "message": "Could not determine site URL"}
            return health_checks

        # Check main page
        health_checks["checks"]["main_page"] = self._check_page_health(site_url)

        # Check search functionality
        search_url = f"{site_url}search/search_index.json"
        health_checks["checks"]["search_index"] = self._check_page_health(search_url)

        # Check sitemap
        sitemap_url = f"{site_url}sitemap.xml"
        health_checks["checks"]["sitemap"] = self._check_page_health(sitemap_url)

        return health_checks

    def _check_page_health(self, url: str) -> dict:
        """Check individual page health."""
        check_result = {"url": url, "status": "unknown", "response_time": None, "status_code": None}

        try:
            start_time = time.time()

            request = urllib.request.Request(url, headers={"User-Agent": "FinWiz-HealthCheck/1.0"})

            with urllib.request.urlopen(request, timeout=10) as response:
                response_time = time.time() - start_time

                check_result.update({"status": "success", "response_time": round(response_time, 3), "status_code": response.status})

        except urllib.error.HTTPError as e:
            check_result.update({"status": "failed", "status_code": e.code, "error": str(e)})

        except Exception as e:
            check_result.update({"status": "failed", "error": str(e)})

        return check_result

    def _save_status(self, status: dict) -> None:
        """Save status to file."""
        try:
            with open(self.status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save status: {e}")

    def print_status_report(self, status: dict) -> None:
        """Print formatted status report."""
        print("\n" + "=" * 60)
        print(f"📊 DEPLOYMENT STATUS - {status['environment'].upper()}")
        print("=" * 60)

        # Site accessibility
        if status["site_accessible"]:
            print("✅ Site is accessible")
        else:
            print("❌ Site is not accessible")

        # Site info
        site_info = status.get("site_info", {})
        if site_info.get("response_time"):
            print(f"⚡ Response time: {site_info['response_time']}s")

        if site_info.get("status_code"):
            print(f"🌐 Status code: {site_info['status_code']}")

        # Git info
        git_info = status.get("git_info", {})
        if git_info.get("last_commit_hash"):
            print(f"📝 Last commit: {git_info['last_commit_hash'][:8]}")
            print(f"👤 Author: {git_info.get('last_commit_author', 'Unknown')}")
            print(f"📅 Date: {git_info.get('last_commit_date', 'Unknown')}")
            print(f"💬 Message: {git_info.get('last_commit_message', 'No message')}")

        # Content checks
        content_checks = site_info.get("content_checks", {})
        if content_checks:
            print("\n📋 Content Checks:")
            for check, result in content_checks.items():
                if isinstance(result, bool):
                    status_icon = "✅" if result else "❌"
                    print(f"  {status_icon} {check}")
                else:
                    print(f"  ℹ️  {check}: {result}")

        # Health checks
        health_checks = status.get("health_checks", {}).get("checks", {})
        if health_checks:
            print("\n🏥 Health Checks:")
            for check_name, check_result in health_checks.items():
                status_icon = "✅" if check_result.get("status") == "success" else "❌"
                response_time = check_result.get("response_time")
                time_info = f" ({response_time}s)" if response_time else ""
                print(f"  {status_icon} {check_name}{time_info}")

        print(f"\n📄 Full report saved to: {self.status_file}")


def main():
    """Main entry point for deployment monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor documentation deployment")
    parser.add_argument(
        "environment",
        choices=["staging", "production"],
        nargs="?",
        default="production",
        help="Environment to monitor (default: production)",
    )
    parser.add_argument("--json", action="store_true", help="Output status as JSON")

    args = parser.parse_args()

    monitor = DeploymentMonitor()
    status = monitor.check_status(args.environment)

    if args.json:
        print(json.dumps(status, indent=2))
    else:
        monitor.print_status_report(status)

    # Exit with error code if site is not accessible
    sys.exit(0 if status["site_accessible"] else 1)


if __name__ == "__main__":
    main()
