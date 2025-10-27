#!/usr/bin/env python3
"""
Documentation deployment script with staging and production environments.

This script provides automated deployment to GitHub Pages with support for
staging environments, zero-downtime deployment, and deployment validation.
"""

import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


class DocumentationDeployer:
    """Documentation deployment manager for GitHub Pages."""

    def __init__(self, repo_url: str | None = None):
        self.repo_url = repo_url or self._get_repo_url()
        self.deployment_stats = {}
        self.start_time = time.time()

    def deploy(self, environment: str = "production", force: bool = False) -> bool:
        """
        Deploy documentation to specified environment.

        Args:
            environment: Target environment ('production' or 'staging')
            force: Force deployment even if validation fails

        Returns:
            bool: True if deployment successful, False otherwise

        """
        print(f"🚀 Starting documentation deployment to {environment}...")

        try:
            # Pre-deployment validation
            if not self._validate_pre_deployment():
                if not force:
                    return False
                print("⚠️  Proceeding with deployment despite validation warnings")

            # Build documentation
            if not self._build_for_deployment():
                return False

            # Deploy to environment
            if environment == "staging":
                success = self._deploy_staging()
            else:
                success = self._deploy_production(force=force)

            if not success:
                return False

            # Post-deployment validation
            if not self._validate_post_deployment(environment):
                print("⚠️  Post-deployment validation failed")
                if not force:
                    return False

            # Generate deployment report
            self._generate_deployment_report(environment)

            deployment_time = time.time() - self.start_time
            print(f"✅ Deployment to {environment} completed successfully in {deployment_time:.2f}s")
            return True

        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return False

    def _get_repo_url(self) -> str | None:
        """Get repository URL from git remote."""
        try:
            result = subprocess.run(["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def _validate_pre_deployment(self) -> bool:
        """Validate environment before deployment."""
        print("🔍 Validating pre-deployment environment...")

        # Check git repository
        if not Path(".git").exists():
            print("❌ Not in a git repository")
            return False

        # Check for uncommitted changes
        try:
            result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)

            if result.stdout.strip():
                print("⚠️  Uncommitted changes detected:")
                print(result.stdout)
                print("   Consider committing changes before deployment")

        except subprocess.CalledProcessError:
            print("⚠️  Could not check git status")

        # Check mkdocs.yml exists
        if not Path("mkdocs.yml").exists():
            print("❌ mkdocs.yml not found")
            return False

        # Check documentation source
        if not Path("docs").exists():
            print("❌ Documentation source directory not found")
            return False

        print("✅ Pre-deployment validation passed")
        return True

    def _build_for_deployment(self) -> bool:
        """Build documentation for deployment."""
        print("🔨 Building documentation for deployment...")

        # Use the production build script
        try:
            result = subprocess.run(["python", "scripts/build_docs.py"], check=True)
            print("✅ Documentation build completed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Documentation build failed: {e}")
            return False

    def _deploy_staging(self) -> bool:
        """Deploy to staging environment (gh-pages-staging branch)."""
        print("📤 Deploying to staging environment...")

        try:
            # Deploy to staging branch
            result = subprocess.run(
                [
                    "uv",
                    "run",
                    "mkdocs",
                    "gh-deploy",
                    "--remote-branch",
                    "gh-pages-staging",
                    "--message",
                    f"Deploy staging documentation at {time.strftime('%Y-%m-%d %H:%M:%S')}",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if result.stdout:
                print("MkDocs deploy output:", result.stdout)

            print("✅ Staging deployment completed")

            # Get staging URL
            staging_url = self._get_staging_url()
            if staging_url:
                print(f"🌐 Staging site available at: {staging_url}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Staging deployment failed: {e}")
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

    def _deploy_production(self, force: bool = False) -> bool:
        """Deploy to production environment (gh-pages branch)."""
        print("📤 Deploying to production environment...")

        try:
            cmd = [
                "uv",
                "run",
                "mkdocs",
                "gh-deploy",
                "--message",
                f"Deploy production documentation at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            ]

            if force:
                cmd.append("--force")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if result.stdout:
                print("MkDocs deploy output:", result.stdout)

            print("✅ Production deployment completed")

            # Get production URL
            production_url = self._get_production_url()
            if production_url:
                print(f"🌐 Production site available at: {production_url}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Production deployment failed: {e}")
            if e.stderr:
                print("STDERR:", e.stderr)
            return False

    def _get_staging_url(self) -> str | None:
        """Get staging site URL."""
        if not self.repo_url:
            return None

        # Extract owner/repo from URL
        if "github.com" in self.repo_url:
            parts = self.repo_url.replace(".git", "").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                return f"https://{owner}.github.io/{repo}/staging/"

        return None

    def _get_production_url(self) -> str | None:
        """Get production site URL."""
        if not self.repo_url:
            return None

        # Extract owner/repo from URL
        if "github.com" in self.repo_url:
            parts = self.repo_url.replace(".git", "").split("/")
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                return f"https://{owner}.github.io/{repo}/"

        return None

    def _validate_post_deployment(self, environment: str) -> bool:
        """Validate deployment after completion."""
        print(f"🔍 Validating {environment} deployment...")

        # Get site URL
        if environment == "staging":
            site_url = self._get_staging_url()
        else:
            site_url = self._get_production_url()

        if not site_url:
            print("⚠️  Could not determine site URL for validation")
            return True  # Don't fail deployment for this

        # Wait a moment for GitHub Pages to update
        print("⏳ Waiting for GitHub Pages to update...")
        time.sleep(10)

        # Test site accessibility
        try:
            print(f"🌐 Testing site accessibility: {site_url}")

            request = urllib.request.Request(site_url, headers={"User-Agent": "FinWiz-Deploy-Validator/1.0"})

            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    content = response.read().decode("utf-8")

                    # Basic content validation
                    if "FinWiz Documentation" in content:
                        print("✅ Site is accessible and contains expected content")
                        return True
                    else:
                        print("⚠️  Site is accessible but content validation failed")
                        return False
                else:
                    print(f"⚠️  Site returned status code: {response.status}")
                    return False

        except urllib.error.URLError as e:
            print(f"⚠️  Site accessibility test failed: {e}")
            return False
        except Exception as e:
            print(f"⚠️  Unexpected error during site validation: {e}")
            return False

    def _generate_deployment_report(self, environment: str) -> None:
        """Generate deployment report."""
        deployment_time = time.time() - self.start_time

        report = {
            "deployment_time": round(deployment_time, 2),
            "deployment_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": environment,
            "repository_url": self.repo_url,
            **self.deployment_stats,
        }

        # Add site URLs
        if environment == "staging":
            report["site_url"] = self._get_staging_url()
        else:
            report["site_url"] = self._get_production_url()

        # Save report
        report_file = Path(f"deployment_report_{environment}.json")
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📊 Deployment report saved to {report_file}")

    def rollback(self, environment: str = "production") -> bool:
        """
        Rollback to previous deployment.

        Args:
            environment: Environment to rollback ('production' or 'staging')

        Returns:
            bool: True if rollback successful, False otherwise

        """
        print(f"🔄 Rolling back {environment} deployment...")

        try:
            # Get the branch name
            branch = "gh-pages-staging" if environment == "staging" else "gh-pages"

            # Reset to previous commit
            result = subprocess.run(["git", "checkout", branch], capture_output=True, text=True, check=True)

            result = subprocess.run(["git", "reset", "--hard", "HEAD~1"], capture_output=True, text=True, check=True)

            result = subprocess.run(
                ["git", "push", "--force-with-lease", "origin", branch], capture_output=True, text=True, check=True
            )

            print(f"✅ {environment.title()} rollback completed")
            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Rollback failed: {e}")
            return False


def main():
    """Main entry point for the deployment script."""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy FinWiz documentation")
    parser.add_argument(
        "environment",
        choices=["staging", "production"],
        nargs="?",
        default="production",
        help="Deployment environment (default: production)",
    )
    parser.add_argument("--force", action="store_true", help="Force deployment even if validation fails")
    parser.add_argument("--rollback", action="store_true", help="Rollback to previous deployment")

    args = parser.parse_args()

    deployer = DocumentationDeployer()

    if args.rollback:
        success = deployer.rollback(args.environment)
    else:
        success = deployer.deploy(args.environment, force=args.force)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
