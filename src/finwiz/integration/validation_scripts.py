"""
Integration System Validation Scripts.

Provides validation scripts for single-user debugging of the crew data
integration system. These scripts help identify and diagnose integration
issues quickly.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .config import get_crew_dependency_config, get_integration_config
from .health_checker import get_health_checker
from .logging_utils import integration_logger, log_analyzer


class ValidationScript:
    """Base class for validation scripts."""

    def __init__(self, output_dir: Path = None) -> None:
        """Initialize validation script."""
        self.config = get_integration_config()
        self.crew_config = get_crew_dependency_config()
        self.output_dir = output_dir or self.config.output_dir
        self.logger = integration_logger

    def run(self) -> dict[str, Any]:
        """Run the validation script."""
        raise NotImplementedError("Subclasses must implement run method")

    def print_results(self, results: dict[str, Any]) -> None:
        """Print validation results in a user-friendly format."""
        print(f"\n{'=' * 60}")
        print(f"Validation Results: {self.__class__.__name__}")
        print(f"{'=' * 60}")

        for key, value in results.items():
            if isinstance(value, dict):
                print(f"\n{key.upper()}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                print(f"\n{key.upper()}:")
                for item in value:
                    print(f"  - {item}")
            else:
                print(f"{key}: {value}")

        print(f"\n{'=' * 60}\n")


class DataIntegrityValidator(ValidationScript):
    """Validates data integrity across all crew outputs."""

    def run(self) -> dict[str, Any]:
        """Run data integrity validation."""
        results = {
            "validation_timestamp": datetime.now().isoformat(),
            "crew_data_status": {},
            "schema_validation": {},
            "data_consistency": {},
            "issues_found": [],
            "recommendations": [],
        }

        try:
            # Check each crew's data
            for crew_name in self.crew_config.crew_dependencies.keys():
                crew_status = self._validate_crew_data(crew_name)
                results["crew_data_status"][crew_name] = crew_status

                if not crew_status["has_data"]:
                    results["issues_found"].append(f"No data found for {crew_name} crew")

                if crew_status["validation_errors"]:
                    results["issues_found"].extend([f"{crew_name}: {error}" for error in crew_status["validation_errors"]])

            # Check data consistency
            consistency_results = self._check_data_consistency()
            results["data_consistency"] = consistency_results

            if consistency_results["inconsistencies"]:
                results["issues_found"].extend(consistency_results["inconsistencies"])

            # Generate recommendations
            results["recommendations"] = self._generate_integrity_recommendations(results)

            return results

        except Exception as e:
            results["error"] = str(e)
            results["issues_found"].append(f"Validation script failed: {str(e)}")
            return results

    def _validate_crew_data(self, crew_name: str) -> dict[str, Any]:
        """Validate data for a specific crew."""
        crew_dir = self.output_dir / crew_name

        status = {"has_data": False, "file_count": 0, "files": [], "validation_errors": [], "last_modified": None}

        if not crew_dir.exists():
            status["validation_errors"].append("Directory does not exist")
            return status

        # Find JSON files
        json_files = list(crew_dir.glob("*.json"))
        status["file_count"] = len(json_files)
        status["files"] = [f.name for f in json_files]
        status["has_data"] = len(json_files) > 0

        if json_files:
            # Get last modified time
            newest_file = max(json_files, key=lambda f: f.stat().st_mtime)
            status["last_modified"] = datetime.fromtimestamp(newest_file.stat().st_mtime).isoformat()

            # Validate JSON structure
            for json_file in json_files:
                try:
                    with open(json_file, encoding="utf-8") as f:
                        data = json.load(f)

                    # Basic structure validation
                    if not isinstance(data, dict):
                        status["validation_errors"].append(f"{json_file.name}: Not a JSON object")

                    # Check for metadata
                    if "metadata" not in data:
                        status["validation_errors"].append(f"{json_file.name}: Missing metadata field")

                except json.JSONDecodeError as e:
                    status["validation_errors"].append(f"{json_file.name}: Invalid JSON - {str(e)}")
                except Exception as e:
                    status["validation_errors"].append(f"{json_file.name}: Read error - {str(e)}")

        return status

    def _check_data_consistency(self) -> dict[str, Any]:
        """Check consistency across crew data."""
        consistency = {"ticker_consistency": {}, "timestamp_consistency": {}, "inconsistencies": []}

        try:
            # Collect tickers from all crews
            all_tickers = {}
            all_timestamps = {}

            for crew_name in ["stock", "etf", "crypto"]:
                crew_dir = self.output_dir / crew_name
                if not crew_dir.exists():
                    continue

                for json_file in crew_dir.glob("*.json"):
                    try:
                        with open(json_file, encoding="utf-8") as f:
                            data = json.load(f)

                        # Extract tickers/symbols
                        tickers = self._extract_tickers_from_data(data, crew_name)
                        if tickers:
                            all_tickers[crew_name] = tickers

                        # Extract timestamps
                        timestamp = self._extract_timestamp_from_data(data)
                        if timestamp:
                            all_timestamps[crew_name] = timestamp

                    except Exception:
                        continue

            # Check ticker consistency
            consistency["ticker_consistency"] = all_tickers

            # Check timestamp consistency (should be within reasonable range)
            consistency["timestamp_consistency"] = all_timestamps

            if all_timestamps:
                timestamps = [datetime.fromisoformat(ts) for ts in all_timestamps.values()]
                time_range = max(timestamps) - min(timestamps)

                if time_range > timedelta(hours=6):  # More than 6 hours apart
                    consistency["inconsistencies"].append(f"Large time gap between crew executions: {time_range}")

            return consistency

        except Exception as e:
            consistency["inconsistencies"].append(f"Consistency check failed: {str(e)}")
            return consistency

    def _extract_tickers_from_data(self, data: dict, crew_name: str) -> list[str]:
        """Extract ticker symbols from crew data."""
        tickers = []

        try:
            if crew_name == "stock":
                # Look for validated_tickers or similar fields
                if "validated_tickers" in data:
                    tickers.extend([t.get("symbol", "") for t in data["validated_tickers"] if isinstance(t, dict)])
            elif crew_name == "etf":
                if "validated_etfs" in data:
                    tickers.extend([e.get("symbol", "") for e in data["validated_etfs"] if isinstance(e, dict)])
            elif crew_name == "crypto":
                if "validated_symbols" in data:
                    tickers.extend([s.get("symbol", "") for s in data["validated_symbols"] if isinstance(s, dict)])
        except Exception:
            pass

        return [t for t in tickers if t]  # Remove empty strings

    def _extract_timestamp_from_data(self, data: dict) -> str | None:
        """Extract timestamp from crew data."""
        try:
            if "metadata" in data and "execution_timestamp" in data["metadata"]:
                return data["metadata"]["execution_timestamp"]
        except Exception:
            pass

        return None

    def _generate_integrity_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate recommendations based on integrity validation."""
        recommendations = []

        # Check for missing data
        missing_crews = [crew for crew, status in results["crew_data_status"].items() if not status["has_data"]]

        if missing_crews:
            recommendations.append(f"Execute missing crews: {', '.join(missing_crews)}")

        # Check for validation errors
        error_crews = [crew for crew, status in results["crew_data_status"].items() if status["validation_errors"]]

        if error_crews:
            recommendations.append(f"Fix validation errors in crews: {', '.join(error_crews)}")

        # Check for consistency issues
        if results["data_consistency"]["inconsistencies"]:
            recommendations.append("Review data consistency issues and re-run crews if needed")

        if not recommendations:
            recommendations.append("Data integrity appears good - continue monitoring")

        return recommendations


class DependencyValidator(ValidationScript):
    """Validates crew dependencies and execution order."""

    def run(self) -> dict[str, Any]:
        """Run dependency validation."""
        results = {
            "validation_timestamp": datetime.now().isoformat(),
            "dependency_status": {},
            "execution_order": [],
            "circular_dependencies": [],
            "missing_dependencies": [],
            "recommendations": [],
        }

        try:
            # Check each crew's dependencies
            for crew_name, dependencies in self.crew_config.crew_dependencies.items():
                dep_status = self._validate_crew_dependencies(crew_name, dependencies)
                results["dependency_status"][crew_name] = dep_status

                if dep_status["missing_dependencies"]:
                    results["missing_dependencies"].extend([f"{crew_name} missing: {', '.join(dep_status['missing_dependencies'])}"])

            # Calculate execution order
            results["execution_order"] = self._calculate_execution_order()

            # Check for circular dependencies
            results["circular_dependencies"] = self._detect_circular_dependencies()

            # Generate recommendations
            results["recommendations"] = self._generate_dependency_recommendations(results)

            return results

        except Exception as e:
            results["error"] = str(e)
            return results

    def _validate_crew_dependencies(self, crew_name: str, dependencies: list[str]) -> dict[str, Any]:
        """Validate dependencies for a specific crew."""
        status = {
            "crew_name": crew_name,
            "required_dependencies": dependencies,
            "satisfied_dependencies": [],
            "missing_dependencies": [],
            "stale_dependencies": [],
        }

        for dep_crew in dependencies:
            dep_dir = self.output_dir / dep_crew

            if not dep_dir.exists() or not list(dep_dir.glob("*.json")):
                status["missing_dependencies"].append(dep_crew)
            else:
                # Check if dependency data is fresh
                json_files = list(dep_dir.glob("*.json"))
                newest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                file_age = datetime.now() - datetime.fromtimestamp(newest_file.stat().st_mtime)

                if file_age > timedelta(hours=self.config.default_max_age_hours):
                    status["stale_dependencies"].append(dep_crew)
                else:
                    status["satisfied_dependencies"].append(dep_crew)

        return status

    def _calculate_execution_order(self) -> list[str]:
        """Calculate optimal execution order based on dependencies."""
        # Simple topological sort
        dependencies = self.crew_config.crew_dependencies
        in_degree = {crew: 0 for crew in dependencies}

        # Calculate in-degrees
        for crew, deps in dependencies.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[crew] += 1

        # Topological sort
        queue = [crew for crew, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for dependent crews
            for crew, deps in dependencies.items():
                if current in deps:
                    in_degree[crew] -= 1
                    if in_degree[crew] == 0:
                        queue.append(crew)

        return result

    def _detect_circular_dependencies(self) -> list[str]:
        """Detect circular dependencies in crew configuration."""
        # Simple cycle detection using DFS
        dependencies = self.crew_config.crew_dependencies
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(crew: str, path: list[str]) -> None:
            if crew in rec_stack:
                # Found a cycle
                cycle_start = path.index(crew)
                cycles.append(" -> ".join(path[cycle_start:] + [crew]))
                return

            if crew in visited:
                return

            visited.add(crew)
            rec_stack.add(crew)

            for dep in dependencies.get(crew, []):
                if dep in dependencies:  # Only follow valid crews
                    dfs(dep, path + [crew])

            rec_stack.remove(crew)

        for crew in dependencies:
            if crew not in visited:
                dfs(crew, [])

        return cycles

    def _generate_dependency_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate recommendations based on dependency validation."""
        recommendations = []

        if results["missing_dependencies"]:
            recommendations.append("Execute crews with missing dependencies first")
            recommendations.extend([f"  - {dep}" for dep in results["missing_dependencies"]])

        if results["circular_dependencies"]:
            recommendations.append("Fix circular dependencies:")
            recommendations.extend([f"  - {cycle}" for cycle in results["circular_dependencies"]])

        if results["execution_order"]:
            recommendations.append(f"Recommended execution order: {' -> '.join(results['execution_order'])}")

        return recommendations


class PerformanceValidator(ValidationScript):
    """Validates system performance and identifies bottlenecks."""

    def run(self) -> dict[str, Any]:
        """Run performance validation."""
        results = {
            "validation_timestamp": datetime.now().isoformat(),
            "execution_analysis": {},
            "bottlenecks": {},
            "resource_usage": {},
            "recommendations": [],
        }

        try:
            # Analyze execution patterns
            results["execution_analysis"] = log_analyzer.analyze_crew_execution_patterns()

            # Identify bottlenecks
            results["bottlenecks"] = log_analyzer.identify_integration_bottlenecks()

            # Check current resource usage
            health_checker = get_health_checker()
            health_report = health_checker.perform_comprehensive_health_check()

            # Extract resource information
            for component in health_report.components:
                if component.component == "system_resources":
                    results["resource_usage"] = component.details
                    break

            # Generate recommendations
            results["recommendations"] = self._generate_performance_recommendations(results)

            return results

        except Exception as e:
            results["error"] = str(e)
            return results

    def _generate_performance_recommendations(self, results: dict[str, Any]) -> list[str]:
        """Generate performance recommendations."""
        recommendations = []

        # Check bottlenecks
        bottlenecks = results.get("bottlenecks", {})

        if bottlenecks.get("slow_crews"):
            slow_crews = [crew["crew"] for crew in bottlenecks["slow_crews"]]
            recommendations.append(f"Optimize slow crews: {', '.join(slow_crews)}")

        if bottlenecks.get("frequent_failure_crews"):
            failing_crews = [crew["crew"] for crew in bottlenecks["frequent_failure_crews"]]
            recommendations.append(f"Fix reliability issues in: {', '.join(failing_crews)}")

        # Check resource usage
        resource_usage = results.get("resource_usage", {})
        issues = resource_usage.get("issues", [])

        if issues:
            recommendations.append("Address resource issues:")
            recommendations.extend([f"  - {issue}" for issue in issues])

        if not recommendations:
            recommendations.append("Performance appears acceptable - continue monitoring")

        return recommendations


def run_all_validations(output_dir: Path = None) -> dict[str, Any]:
    """Run all validation scripts and return combined results."""
    print("Running comprehensive integration system validation...")

    validators = [DataIntegrityValidator(output_dir), DependencyValidator(output_dir), PerformanceValidator(output_dir)]

    all_results = {
        "validation_suite_timestamp": datetime.now().isoformat(),
        "validators_run": [],
        "overall_status": "healthy",
        "critical_issues": [],
        "all_recommendations": [],
    }

    for validator in validators:
        validator_name = validator.__class__.__name__
        print(f"\nRunning {validator_name}...")

        try:
            results = validator.run()
            all_results[validator_name.lower()] = results
            all_results["validators_run"].append(validator_name)

            # Print results
            validator.print_results(results)

            # Collect critical issues
            if "issues_found" in results and results["issues_found"]:
                all_results["critical_issues"].extend(results["issues_found"])

            # Collect recommendations
            if "recommendations" in results and results["recommendations"]:
                all_results["all_recommendations"].extend(results["recommendations"])

            # Update overall status
            if "error" in results:
                all_results["overall_status"] = "critical"
            elif results.get("issues_found") or results.get("missing_dependencies"):
                if all_results["overall_status"] == "healthy":
                    all_results["overall_status"] = "warning"

        except Exception as e:
            print(f"ERROR: {validator_name} failed: {str(e)}")
            all_results["critical_issues"].append(f"{validator_name} failed: {str(e)}")
            all_results["overall_status"] = "critical"

    # Print summary
    print(f"\n{'=' * 60}")
    print("VALIDATION SUMMARY")
    print(f"{'=' * 60}")
    print(f"Overall Status: {all_results['overall_status'].upper()}")
    print(f"Validators Run: {len(all_results['validators_run'])}")
    print(f"Critical Issues: {len(all_results['critical_issues'])}")
    print(f"Total Recommendations: {len(all_results['all_recommendations'])}")

    if all_results["critical_issues"]:
        print("\nCRITICAL ISSUES:")
        for issue in all_results["critical_issues"]:
            print(f"  - {issue}")

    if all_results["all_recommendations"]:
        print("\nRECOMMENDATIONS:")
        for rec in all_results["all_recommendations"]:
            print(f"  - {rec}")

    print(f"\n{'=' * 60}\n")

    return all_results


def main() -> None:
    """Run validation scripts based on command line arguments."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "integrity":
            validator = DataIntegrityValidator()
            results = validator.run()
            validator.print_results(results)
        elif command == "dependencies":
            validator = DependencyValidator()
            results = validator.run()
            validator.print_results(results)
        elif command == "performance":
            validator = PerformanceValidator()
            results = validator.run()
            validator.print_results(results)
        elif command == "all":
            run_all_validations()
        else:
            print("Usage: python validation_scripts.py [integrity|dependencies|performance|all]")
    else:
        # Run all validations by default
        run_all_validations()


if __name__ == "__main__":
    main()
