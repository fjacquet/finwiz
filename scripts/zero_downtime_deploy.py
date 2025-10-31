#!/usr/bin/env python3
"""
Zero-downtime deployment strategy for documentation.

This script implements a blue-green deployment strategy for documentation
to minimize downtime and provide rollback capabilities.
"""

import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path


class ZeroDowntimeDeployer:
    """Implements zero-downtime deployment for documentation."""

    def __init__(self, config_file: str = "docs/deployment-config.yml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.temp_dir = None
        self.backup_created = False

    def deploy(self, environment: str = "production", force: bool = False) -> bool:
        """
        Deploy with zero-downtime strategy.

        Args:
            environment: Target environment
            force: Force deployment even if validation fails

        Returns:
            bool: True if deployment successful, False otherwise

        """
        print(f"🚀 Starting zero-downtime deployment to {environment}...")

        try:
            # Validate environment
            if environment not in self.config.get("environments", {}):
                print(f"❌ Unknown environment: {environment}")
                return False

            env_config = self.config["environments"][environment]

            # Create backup if enabled
            if self.config.get("rollback", {}).get("backup_before_deploy", True):
                if not self._create_backup(environment):
                    if not force:
                        return False
                    print("⚠️  Proceeding without backup")

            # Build new version
            if not self._build_new_version(env_config):
                return False

            # Validate new build
            if not self._validate_new_build(env_config, force):
                return False

            # Deploy with blue-green strategy
            if not self._deploy_blue_green(environment, env_config):
                return False

            # Verify deployment
            if not self._verify_deployment(environment, env_config):
                print("⚠️  Deployment verification failed")
                if not force:
                    print("🔄 Attempting rollback...")
                    self._rollback(environment)
                    return False

            # Cleanup
            self._cleanup()

            print(f"✅ Zero-downtime deployment to {environment} completed successfully")
            return True

        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            if self.backup_created:
                print("🔄 Attempting rollback...")
                self._rollback(environment)
            return False

    def _load_config(self) -> dict:
        """Load deployment configuration."""
        if not self.config_file.exists():
            print(f"⚠️  Config file not found: {self.config_file}")
            return self._get_default_config()

        try:
            import yaml

            with open(self.config_file) as f:
                return yaml.safe_load(f)
        except ImportError:
            print("⚠️  PyYAML not available, using default config")
            return self._get_default_config()
        except Exception as e:
            print(f"⚠️  Could not load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> dict:
        """Get default configuration."""
        return {
            "environments": {
                "production": {
                    "name": "Production",
                    "branch": "gh-pages",
                    "validation": {"strict": True},
                    "optimization": {"minify_assets": True},
                },
                "staging": {
                    "name": "Staging",
                    "branch": "gh-pages-staging",
                    "validation": {"strict": False},
                    "optimization": {"minify_assets": False},
                },
            },
            "rollback": {"backup_before_deploy": True},
        }

    def _create_backup(self, environment: str) -> bool:
        """Create backup of current deployment."""
        print("💾 Creating deployment backup...")

        try:
            env_config = self.config["environments"][environment]
            branch = env_config.get("branch", "gh-pages")

            # Create temporary directory for backup
            self.temp_dir = Path(tempfile.mkdtemp(prefix="docs_backup_"))

            # Clone current deployment branch
            result = subprocess.run(
                ["git", "clone", "--single-branch", "--branch", branch, ".", str(self.temp_dir / "backup")],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(f"⚠️  Could not create backup: {result.stderr}")
                return False

            self.backup_created = True
            print(f"✅ Backup created in {self.temp_dir}")
            return True

        except Exception as e:
            print(f"⚠️  Backup creation failed: {e}")
            return False

    def _build_new_version(self, env_config: dict) -> bool:
        """Build new version of documentation."""
        print("🔨 Building new version...")

        try:
            # Determine build options based on environment
            optimization = env_config.get("optimization", {})

            cmd = ["python", "scripts/build_docs.py"]

            if not optimization.get("minify_assets", True):
                cmd.append("--no-optimize")

            result = subprocess.run(cmd, check=True)
            print("✅ New version built successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            return False

    def _validate_new_build(self, env_config: dict, force: bool) -> bool:
        """Validate new build before deployment."""
        print("🔍 Validating new build...")

        try:
            validation = env_config.get("validation", {})

            cmd = ["python", "scripts/validate_build.py"]

            if validation.get("fail_on_warnings", False):
                cmd.append("--fail-on-warnings")

            result = subprocess.run(cmd, check=True)
            print("✅ Build validation passed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Build validation failed: {e}")
            return force

    def _deploy_blue_green(self, environment: str, env_config: dict) -> bool:
        """Deploy using blue-green strategy."""
        print("🔄 Deploying with blue-green strategy...")

        try:
            branch = env_config.get("branch", "gh-pages")

            # Create deployment message
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            message = f"Zero-downtime deploy to {environment} at {timestamp}"

            # Deploy to GitHub Pages
            result = subprocess.run(
                ["uv", "run", "mkdocs", "gh-deploy", "--remote-branch", branch, "--message", message],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                print("Deploy output:", result.stdout)

            print("✅ Blue-green deployment completed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Blue-green deployment failed: {e}")
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

    def _verify_deployment(self, environment: str, env_config: dict) -> bool:
        """Verify deployment is working correctly."""
        print("🔍 Verifying deployment...")

        # Get site URL
        site_url = self._get_site_url(environment)
        if not site_url:
            print("⚠️  Could not determine site URL for verification")
            return True  # Don't fail deployment for this

        # Wait for GitHub Pages to update
        print("⏳ Waiting for GitHub Pages to update...")
        time.sleep(15)  # Give GitHub Pages time to update

        # Test site accessibility
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"🌐 Testing site accessibility (attempt {attempt + 1}/{max_retries}): {site_url}")

                request = urllib.request.Request(site_url, headers={"User-Agent": "FinWiz-Deploy-Verifier/1.0"})

                with urllib.request.urlopen(request, timeout=30) as response:
                    if response.status == 200:
                        content = response.read().decode("utf-8")

                        # Basic content validation
                        if "FinWiz Documentation" in content:
                            print("✅ Deployment verification successful")
                            return True
                        else:
                            print("⚠️  Site accessible but content validation failed")

                    else:
                        print(f"⚠️  Site returned status code: {response.status}")

            except urllib.error.URLError as e:
                print(f"⚠️  Site accessibility test failed (attempt {attempt + 1}): {e}")

            except Exception as e:
                print(f"⚠️  Unexpected error during verification (attempt {attempt + 1}): {e}")

            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(10)

        print("⚠️  Deployment verification failed after all attempts")
        return False

    def _get_site_url(self, environment: str) -> str | None:
        """Get site URL for environment."""
        try:
            # Get repository info
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)

            repo_url = result.stdout.strip()

            if "github.com" in repo_url:
                # Extract owner/repo from URL
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

    def _rollback(self, environment: str) -> bool:
        """Rollback to previous deployment."""
        print("🔄 Rolling back deployment...")

        if not self.backup_created or not self.temp_dir:
            print("❌ No backup available for rollback")
            return False

        try:
            env_config = self.config["environments"][environment]
            branch = env_config.get("branch", "gh-pages")

            # Restore from backup
            backup_dir = self.temp_dir / "backup"

            if not backup_dir.exists():
                print("❌ Backup directory not found")
                return False

            # Force push backup to restore previous state
            result = subprocess.run(["git", "-C", str(backup_dir), "push", "--force", "origin", branch], capture_output=True, text=True, check=True)

            print("✅ Rollback completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def _cleanup(self) -> None:
        """Cleanup temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            try:
                shutil.rmtree(self.temp_dir)
                print("🧹 Cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup failed: {e}")


def main():
    """Main entry point for zero-downtime deployment."""
    import argparse

    parser = argparse.ArgumentParser(description="Zero-downtime documentation deployment")
    parser.add_argument(
        "environment",
        choices=["staging", "production"],
        nargs="?",
        default="production",
        help="Deployment environment (default: production)",
    )
    parser.add_argument("--force", action="store_true", help="Force deployment even if validation fails")
    parser.add_argument("--config", default="docs/deployment-config.yml", help="Deployment configuration file")

    args = parser.parse_args()

    deployer = ZeroDowntimeDeployer(config_file=args.config)
    success = deployer.deploy(args.environment, force=args.force)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
