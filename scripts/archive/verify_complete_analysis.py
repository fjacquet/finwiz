#!/usr/bin/env python
"""
Verification script to ensure complete FinWiz analysis with up-to-date data.

This script checks:
- All crew outputs exist
- Data freshness (< 24 hours recommended)
- A+ opportunities available
- Portfolio review complete
- Final reports generated
- Data integration successful
"""

import json
import sys
from datetime import datetime
from pathlib import Path


class AnalysisVerifier:
    """Verify completeness and freshness of FinWiz analysis."""

    def __init__(self):
        self.output_dir = Path("output")
        self.issues = []
        self.warnings = []
        self.successes = []

    def check_file_exists(self, path: Path, description: str) -> bool:
        """Check if a file exists."""
        if path.exists():
            self.successes.append(f"✅ {description}: {path}")
            return True
        else:
            self.issues.append(f"❌ {description} missing: {path}")
            return False

    def check_file_freshness(self, path: Path, max_age_hours: int = 24) -> tuple[bool, float]:
        """Check if a file is fresh (modified within max_age_hours)."""
        if not path.exists():
            return False, 0

        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        age_hours = (datetime.now() - mtime).total_seconds() / 3600

        if age_hours <= max_age_hours:
            self.successes.append(f"✅ Fresh data ({age_hours:.1f}h old): {path.name}")
            return True, age_hours
        else:
            self.warnings.append(f"⚠️  Stale data ({age_hours:.1f}h old): {path.name}")
            return False, age_hours

    def check_json_content(self, path: Path, required_keys: list[str]) -> bool:
        """Check if JSON file contains required keys."""
        if not path.exists():
            return False

        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                self.warnings.append(f"⚠️  Missing keys in {path.name}: {missing_keys}")
                return False
            else:
                self.successes.append(f"✅ Valid structure: {path.name}")
                return True
        except Exception as e:
            self.issues.append(f"❌ Invalid JSON in {path.name}: {e}")
            return False

    def verify_core_analysis(self) -> dict[str, bool]:
        """Verify core analysis crews (stock, ETF, crypto)."""
        print("\n" + "=" * 80)
        print("📊 CORE ANALYSIS VERIFICATION")
        print("=" * 80)

        results = {}

        # Check stock analysis
        stock_dir = self.output_dir / "stock"
        if stock_dir.exists():
            stock_files = list(stock_dir.glob("*.json"))
            if stock_files:
                results["stock"] = True
                self.successes.append(f"✅ Stock analysis: {len(stock_files)} files")
                # Check freshness
                for f in stock_files:
                    self.check_file_freshness(f)
            else:
                results["stock"] = False
                self.issues.append("❌ Stock analysis: No output files")
        else:
            results["stock"] = False
            self.issues.append("❌ Stock analysis: Directory missing")

        # Check ETF analysis
        etf_dir = self.output_dir / "etf"
        if etf_dir.exists():
            etf_files = list(etf_dir.glob("*.json"))
            if etf_files:
                results["etf"] = True
                self.successes.append(f"✅ ETF analysis: {len(etf_files)} files")
                for f in etf_files:
                    self.check_file_freshness(f)
            else:
                results["etf"] = False
                self.issues.append("❌ ETF analysis: No output files")
        else:
            results["etf"] = False
            self.issues.append("❌ ETF analysis: Directory missing")

        # Check crypto analysis
        crypto_dir = self.output_dir / "crypto"
        if crypto_dir.exists():
            crypto_files = list(crypto_dir.glob("*.json"))
            if crypto_files:
                results["crypto"] = True
                self.successes.append(f"✅ Crypto analysis: {len(crypto_files)} files")
                for f in crypto_files:
                    self.check_file_freshness(f)
            else:
                results["crypto"] = False
                self.warnings.append("⚠️  Crypto analysis: No output files (optional)")
        else:
            results["crypto"] = False
            self.warnings.append("⚠️  Crypto analysis: Directory missing (optional)")

        return results

    def verify_portfolio_analysis(self) -> bool:
        """Verify portfolio review and rebalancing."""
        print("\n" + "=" * 80)
        print("💼 PORTFOLIO ANALYSIS VERIFICATION")
        print("=" * 80)

        portfolio_file = self.output_dir / "portfolio" / "portfolio_review.json"

        if not self.check_file_exists(portfolio_file, "Portfolio review"):
            return False

        # Check freshness
        is_fresh, age = self.check_file_freshness(portfolio_file)

        # Check content structure
        required_keys = ["portfolio_review"]
        if self.check_json_content(portfolio_file, required_keys):
            # Check holdings detail
            try:
                with open(portfolio_file, encoding="utf-8") as f:
                    data = json.load(f)

                holdings = data.get("portfolio_review", {}).get("holdings", [])
                if holdings:
                    self.successes.append(f"✅ Portfolio holdings: {len(holdings)} positions")

                    # Check for deep analysis (not just validation)
                    deep_analysis_count = sum(1 for h in holdings if h.get("crew_analysis_used") is not None)
                    if deep_analysis_count > 0:
                        self.successes.append(f"✅ Deep analysis: {deep_analysis_count}/{len(holdings)} holdings")
                    else:
                        self.warnings.append("⚠️  Shallow analysis: Only ticker validation performed")

                    # Check for alternatives
                    with_alternatives = sum(1 for h in holdings if h.get("alternatives") and len(h["alternatives"]) > 0)
                    if with_alternatives > 0:
                        self.successes.append(f"✅ Alternatives found: {with_alternatives} holdings have A+ alternatives")
                    else:
                        self.warnings.append("⚠️  No A+ alternatives found for any holdings")

                else:
                    self.warnings.append("⚠️  Portfolio review: No holdings found")

            except Exception as e:
                self.issues.append(f"❌ Portfolio review content error: {e}")
                return False

        return True

    def verify_discovery_analysis(self) -> dict[str, int]:
        """Verify A+ discovery analysis."""
        print("\n" + "=" * 80)
        print("🔍 A+ DISCOVERY VERIFICATION")
        print("=" * 80)

        discovery_dir = self.output_dir / "discovery"
        results = {"etf": 0, "stock": 0, "crypto": 0}

        if not discovery_dir.exists():
            self.warnings.append("⚠️  Discovery directory missing - A+ analysis not run")
            return results

        # Check ETF A+ candidates
        etf_file = discovery_dir / "a_plus_etfs.json"
        if etf_file.exists():
            try:
                with open(etf_file, encoding="utf-8") as f:
                    data = json.load(f)
                candidates = data.get("a_plus_candidates", [])
                results["etf"] = len(candidates)
                if candidates:
                    self.successes.append(f"✅ A+ ETFs: {len(candidates)} candidates")
                else:
                    self.warnings.append("⚠️  A+ ETFs: No candidates found")
                self.check_file_freshness(etf_file)
            except Exception as e:
                self.issues.append(f"❌ A+ ETFs file error: {e}")
        else:
            self.warnings.append("⚠️  A+ ETFs: File missing")

        # Check Stock A+ candidates
        stock_file = discovery_dir / "a_plus_stocks.json"
        if stock_file.exists():
            try:
                with open(stock_file, encoding="utf-8") as f:
                    data = json.load(f)
                candidates = data.get("a_plus_candidates", [])
                results["stock"] = len(candidates)
                if candidates:
                    self.successes.append(f"✅ A+ Stocks: {len(candidates)} candidates")
                else:
                    self.warnings.append("⚠️  A+ Stocks: No candidates found")
                self.check_file_freshness(stock_file)
            except Exception as e:
                self.issues.append(f"❌ A+ Stocks file error: {e}")
        else:
            self.warnings.append("⚠️  A+ Stocks: File missing")

        # Check Crypto A+ candidates
        crypto_file = discovery_dir / "a_plus_crypto.json"
        if crypto_file.exists():
            try:
                with open(crypto_file, encoding="utf-8") as f:
                    data = json.load(f)
                candidates = data.get("a_plus_candidates", [])
                results["crypto"] = len(candidates)
                if candidates:
                    self.successes.append(f"✅ A+ Crypto: {len(candidates)} candidates")
                else:
                    self.warnings.append("⚠️  A+ Crypto: No candidates found")
                self.check_file_freshness(crypto_file)
            except Exception as e:
                self.issues.append(f"❌ A+ Crypto file error: {e}")
        else:
            self.warnings.append("⚠️  A+ Crypto: File missing (optional)")

        return results

    def verify_final_reports(self) -> bool:
        """Verify final HTML reports."""
        print("\n" + "=" * 80)
        print("📄 FINAL REPORTS VERIFICATION")
        print("=" * 80)

        en_report = self.output_dir / "finwiz_family_financial_plan.html"
        fr_report = self.output_dir / "finwiz_family_financial_plan.html"

        en_exists = self.check_file_exists(en_report, "English report")
        fr_exists = self.check_file_exists(fr_report, "French report")

        if en_exists:
            self.check_file_freshness(en_report)
        if fr_exists:
            self.check_file_freshness(fr_report)

        # Check report JSON outputs
        report_dir = self.output_dir / "report"
        if report_dir.exists():
            json_files = list(report_dir.glob("*.json"))
            if json_files:
                self.successes.append(f"✅ Report JSON files: {len(json_files)} files")
            else:
                self.warnings.append("⚠️  Report JSON files: None found")
        else:
            self.warnings.append("⚠️  Report directory missing")

        return en_exists or fr_exists

    def verify_data_integration(self) -> bool:
        """Verify data integration completeness."""
        print("\n" + "=" * 80)
        print("🔗 DATA INTEGRATION VERIFICATION")
        print("=" * 80)

        # Check if all expected directories exist
        expected_dirs = ["stock", "etf", "crypto", "portfolio", "discovery", "report"]
        existing_dirs = [d for d in expected_dirs if (self.output_dir / d).exists()]

        self.successes.append(f"✅ Output directories: {len(existing_dirs)}/{len(expected_dirs)} present")

        if len(existing_dirs) < len(expected_dirs):
            missing = set(expected_dirs) - set(existing_dirs)
            self.warnings.append(f"⚠️  Missing directories: {missing}")

        # Count total JSON files
        total_json = len(list(self.output_dir.rglob("*.json")))
        if total_json > 0:
            self.successes.append(f"✅ Total data files: {total_json} JSON files")
        else:
            self.issues.append("❌ No data files found - analysis may not have run")

        return len(existing_dirs) >= 3  # At least 3 crews should have run

    def print_summary(self):
        """Print verification summary."""
        print("\n" + "=" * 80)
        print("📋 VERIFICATION SUMMARY")
        print("=" * 80)

        print(f"\n✅ Successes: {len(self.successes)}")
        for success in self.successes:
            print(f"  {success}")

        if self.warnings:
            print(f"\n⚠️  Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.issues:
            print(f"\n❌ Issues: {len(self.issues)}")
            for issue in self.issues:
                print(f"  {issue}")

        print("\n" + "=" * 80)

        # Overall status
        if not self.issues:
            if not self.warnings:
                print("🎉 VERIFICATION PASSED - All systems operational!")
                print("=" * 80)
                return 0
            else:
                print("✅ VERIFICATION PASSED WITH WARNINGS")
                print("=" * 80)
                print("\nRecommendations:")
                print("- Review warnings above")
                print("- Consider re-running analysis for missing optional components")
                return 0
        else:
            print("❌ VERIFICATION FAILED")
            print("=" * 80)
            print("\nRecommendations:")
            print("1. Remove old data: rm -rf output/*/")
            print("2. Run fresh analysis: uv run python src/finwiz/main.py")
            print("3. Check logs for errors: tail -f logs/*.log")
            return 1

    def run_verification(self) -> int:
        """Run complete verification."""
        print("=" * 80)
        print("🔍 FinWiz Complete Analysis Verification")
        print("=" * 80)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all verifications
        core_results = self.verify_core_analysis()
        portfolio_ok = self.verify_portfolio_analysis()
        discovery_results = self.verify_discovery_analysis()
        reports_ok = self.verify_final_reports()
        integration_ok = self.verify_data_integration()

        # Print summary
        return self.print_summary()


def main():
    """Main entry point."""
    verifier = AnalysisVerifier()
    exit_code = verifier.run_verification()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
