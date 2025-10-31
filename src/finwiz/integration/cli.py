#!/usr/bin/env python3
"""
Integration System CLI.

Command-line interface for monitoring and debugging the crew data integration
system. Provides easy access to health checks, validation scripts, and
system status.
"""

import argparse
import json
import sys
from typing import Any

from .health_checker import get_health_checker, perform_quick_health_check
from .logging_utils import lineage_tracker, log_analyzer
from .validation_scripts import DataIntegrityValidator, DependencyValidator, PerformanceValidator, run_all_validations


def cmd_health(args: Any) -> None:
    """Run health check command."""
    print("Running integration system health check...")

    if args.quick:
        # Quick health check
        result = perform_quick_health_check()

        print("\nQuick Health Check Results:")
        print(f"Status: {result['overall_status'].upper()}")
        print(f"Timestamp: {result['check_timestamp']}")

        if result.get("issues"):
            print("\nIssues Found:")
            for issue in result["issues"]:
                print(f"  - {issue}")
        else:
            print("\nNo issues found")

    else:
        # Comprehensive health check
        health_checker = get_health_checker()
        report = health_checker.perform_comprehensive_health_check()

        print("\nComprehensive Health Check Results:")
        print(f"Overall Status: {report.overall_status.upper()}")
        print(f"Components Checked: {len(report.components)}")
        print(f"Timestamp: {report.check_timestamp}")

        # Show component status
        print("\nComponent Status:")
        for component in report.components:
            status_icon = "✓" if component.status == "healthy" else "⚠" if component.status == "warning" else "✗"
            print(f"  {status_icon} {component.component}: {component.status} - {component.message}")

        # Show recommendations
        if report.recommendations:
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")

        # Export report if requested
        if args.export:
            output_file = health_checker.export_health_report()
            print(f"\nHealth report exported to: {output_file}")


def cmd_validate(args: Any) -> None:
    """Run validation command."""
    if args.type == "all":
        run_all_validations()
    elif args.type == "integrity":
        validator = DataIntegrityValidator()
        results = validator.run()
        validator.print_results(results)
    elif args.type == "dependencies":
        validator = DependencyValidator()
        results = validator.run()
        validator.print_results(results)
    elif args.type == "performance":
        validator = PerformanceValidator()
        results = validator.run()
        validator.print_results(results)


def cmd_status(args: Any) -> None:
    """Show system status command."""
    print("Integration System Status")
    print("=" * 50)

    # Quick health check
    health_result = perform_quick_health_check()
    print(f"Health Status: {health_result['overall_status'].upper()}")

    # Lineage summary
    try:
        lineage_summary = lineage_tracker.get_lineage_summary()
        print(f"Total Executions: {lineage_summary.get('total_executions', 0)}")
        print(f"Recent Executions (24h): {lineage_summary.get('recent_executions_24h', 0)}")
        print(f"Active Crews: {len(lineage_summary.get('active_crews', []))}")

        if lineage_summary.get("active_crews"):
            print(f"Crews: {', '.join(lineage_summary['active_crews'])}")

    except Exception as e:
        print(f"Could not load lineage data: {e}")

    # Show recent issues if any
    if health_result.get("issues"):
        print("\nRecent Issues:")
        for issue in health_result["issues"]:
            print(f"  - {issue}")


def cmd_analyze(args: Any) -> None:
    """Run analysis command."""
    print("Analyzing integration system performance...")

    try:
        if args.type == "execution":
            # Analyze execution patterns
            analysis = log_analyzer.analyze_crew_execution_patterns(hours_back=args.hours)

            print(f"\nExecution Analysis (last {args.hours} hours):")
            print(f"Total Executions: {analysis.get('total_executions', 0)}")

            # Show execution frequency
            frequency = analysis.get("execution_frequency", {})
            if frequency:
                print("\nExecution Frequency:")
                for crew, count in frequency.items():
                    print(f"  {crew}: {count} executions")

            # Show success rates
            success_rates = analysis.get("success_rates", {})
            if success_rates:
                print("\nSuccess Rates:")
                for crew, rates in success_rates.items():
                    print(f"  {crew}: {rates['percentage']:.1f}% ({rates['success']}/{rates['total']})")

            # Show average durations
            durations = analysis.get("average_durations", {})
            if durations:
                print("\nAverage Execution Times:")
                for crew, duration_data in durations.items():
                    print(f"  {crew}: {duration_data['average']:.2f}s (min: {duration_data['min']:.2f}s, max: {duration_data['max']:.2f}s)")

        elif args.type == "bottlenecks":
            # Identify bottlenecks
            bottlenecks = log_analyzer.identify_integration_bottlenecks()

            print("\nBottleneck Analysis:")

            if bottlenecks.get("high_dependency_crews"):
                print("\nHigh Dependency Crews:")
                for crew_info in bottlenecks["high_dependency_crews"]:
                    print(f"  {crew_info['crew']}: {crew_info['dependency_count']} dependencies")

            if bottlenecks.get("slow_crews"):
                print("\nSlow Crews:")
                for crew_info in bottlenecks["slow_crews"]:
                    print(f"  {crew_info['crew']}: {crew_info['average_duration']:.2f}s average")

            if bottlenecks.get("frequent_failure_crews"):
                print("\nFrequent Failure Crews:")
                for crew_info in bottlenecks["frequent_failure_crews"]:
                    print(f"  {crew_info['crew']}: {crew_info['success_rate']:.1f}% success rate")

            if not any(bottlenecks.values()):
                print("No significant bottlenecks detected")

        elif args.type == "debug":
            # Generate debug report
            crew_name = args.crew if hasattr(args, "crew") else None
            report = log_analyzer.generate_debug_report(crew_name)

            if args.export:
                output_file = log_analyzer.export_debug_report(crew_name=crew_name)
                print(f"Debug report exported to: {output_file}")
            else:
                print(json.dumps(report, indent=2, default=str))

    except Exception as e:
        print(f"Analysis failed: {e}")


def cmd_lineage(args: Any) -> None:
    """Show data lineage command."""
    print("Data Lineage Information")
    print("=" * 50)

    try:
        if args.crew:
            # Show lineage for specific crew
            lineage = lineage_tracker.get_crew_lineage(args.crew)
            print(f"\nLineage for {args.crew} crew:")

            if not lineage:
                print("No lineage data found")
            else:
                for i, execution in enumerate(lineage[-5:], 1):  # Show last 5
                    print(f"\n{i}. Execution at {execution['execution_timestamp']}")
                    print(f"   Input sources: {len(execution.get('input_data', {}))}")
                    print(f"   Output files: {len(execution.get('output_files', []))}")

        else:
            # Show overall lineage summary
            summary = lineage_tracker.get_lineage_summary()

            print(f"Total Executions: {summary.get('total_executions', 0)}")
            print(f"Recent Executions (24h): {summary.get('recent_executions_24h', 0)}")
            print(f"Total Dependencies: {summary.get('total_dependencies', 0)}")
            print(f"Total Data Flows: {summary.get('total_data_flows', 0)}")

            # Show crew execution counts
            execution_counts = summary.get("crew_execution_counts", {})
            if execution_counts:
                print("\nCrew Execution Counts:")
                for crew, count in execution_counts.items():
                    print(f"  {crew}: {count}")

            # Show data flow graph
            if args.flows:
                flow_graph = lineage_tracker.get_data_flow_graph()
                if flow_graph:
                    print("\nData Flow Graph:")
                    for source, flows in flow_graph.items():
                        targets = [flow["target"] for flow in flows]
                        print(f"  {source} -> {', '.join(set(targets))}")

    except Exception as e:
        print(f"Could not load lineage data: {e}")


def main() -> int | None:
    """Run the main CLI interface."""
    parser = argparse.ArgumentParser(
        description="FinWiz Integration System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s health --quick                    # Quick health check
  %(prog)s health --export                   # Full health check with export
  %(prog)s validate all                      # Run all validations
  %(prog)s validate integrity                # Check data integrity only
  %(prog)s status                           # Show system status
  %(prog)s analyze execution --hours 48     # Analyze last 48 hours
  %(prog)s analyze bottlenecks              # Find performance bottlenecks
  %(prog)s lineage --crew stock             # Show lineage for stock crew
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Health command
    health_parser = subparsers.add_parser("health", help="Run health checks")
    health_parser.add_argument("--quick", action="store_true", help="Run quick health check")
    health_parser.add_argument("--export", action="store_true", help="Export detailed report")
    health_parser.set_defaults(func=cmd_health)

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Run validation scripts")
    validate_parser.add_argument("type", choices=["all", "integrity", "dependencies", "performance"], help="Type of validation to run")
    validate_parser.set_defaults(func=cmd_validate)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze system performance")
    analyze_subparsers = analyze_parser.add_subparsers(dest="type", help="Analysis type")

    # Execution analysis
    exec_parser = analyze_subparsers.add_parser("execution", help="Analyze execution patterns")
    exec_parser.add_argument("--hours", type=int, default=24, help="Hours to analyze (default: 24)")

    # Bottleneck analysis
    analyze_subparsers.add_parser("bottlenecks", help="Identify bottlenecks")

    # Debug analysis
    debug_parser = analyze_subparsers.add_parser("debug", help="Generate debug report")
    debug_parser.add_argument("--crew", help="Focus on specific crew")
    debug_parser.add_argument("--export", action="store_true", help="Export to file")

    analyze_parser.set_defaults(func=cmd_analyze)

    # Lineage command
    lineage_parser = subparsers.add_parser("lineage", help="Show data lineage")
    lineage_parser.add_argument("--crew", help="Show lineage for specific crew")
    lineage_parser.add_argument("--flows", action="store_true", help="Show data flow graph")
    lineage_parser.set_defaults(func=cmd_lineage)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
