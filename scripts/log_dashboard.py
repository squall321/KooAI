#!/usr/bin/env python3
"""
Log Dashboard CLI

Command-line dashboard for viewing log analytics.
"""

import sys
from pathlib import Path
import json
import argparse

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.logging.log_analyzer import (
    LogAnalyzer,
    MetricsAnalyzer,
    AuditAnalyzer,
    generate_dashboard_report,
)


def print_header(title: str):
    """Print section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_stats(stats: dict, indent: int = 0):
    """Print statistics dictionary."""
    prefix = "  " * indent
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_stats(value, indent + 1)
        elif isinstance(value, float):
            if key.endswith("_rate"):
                print(f"{prefix}{key}: {value:.2%}")
            else:
                print(f"{prefix}{key}: {value:.2f}")
        else:
            print(f"{prefix}{key}: {value}")


def show_overview(hours: int = 24):
    """Show overview dashboard."""
    print_header(f"KooAI Log Dashboard - Last {hours} Hours")

    report = generate_dashboard_report(
        Path("logs/app.log"),
        Path("logs/metrics.log"),
        Path("logs/audit.log"),
        hours=hours,
    )

    # Application Overview
    print_header("Application Logs")
    if report["application"]:
        print(f"  Total Entries: {report['application'].get('total_entries', 0)}")
        print(f"  Errors: {report['application'].get('errors', 0)}")
        print(f"  Error Rate: {report['application'].get('error_rate', 0):.2%}")

        if report["application"].get("top_errors"):
            print("\n  Top Errors:")
            for error, count in list(report["application"]["top_errors"].items())[:5]:
                print(f"    [{count:3d}] {error[:70]}")
    else:
        print("  No application logs found")

    # File Uploads
    print_header("File Uploads")
    if report["file_uploads"]:
        print_stats(report["file_uploads"], indent=1)
    else:
        print("  No upload data")

    # LLM Usage
    print_header("LLM Usage")
    if report["llm_usage"]:
        print_stats(report["llm_usage"], indent=1)
    else:
        print("  No LLM usage data")

    # Visualizations
    print_header("Visualizations")
    if report["visualizations"]:
        print_stats(report["visualizations"], indent=1)
    else:
        print("  No visualization data")

    # Authentication
    print_header("Authentication")
    if report["authentication"]:
        print_stats(report["authentication"], indent=1)
    else:
        print("  No authentication data")

    # Security Anomalies
    if report["security_anomalies"]:
        print_header("⚠️  Security Anomalies")
        for anomaly in report["security_anomalies"]:
            print(f"\n  [{anomaly['severity'].upper()}] {anomaly['type']}")
            print(f"  {anomaly['description']}")

    print("\n")


def show_errors(hours: int = 24, limit: int = 20):
    """Show recent errors."""
    print_header(f"Recent Errors - Last {hours} Hours")

    analyzer = LogAnalyzer(Path("logs/app.log"))
    errors = analyzer.get_error_summary(hours)

    if not errors:
        print("  No errors found")
        return

    for error in errors[-limit:]:
        print(f"\n  [{error['timestamp']}] {error['level']}")
        print(f"  User: {error.get('user_id', 'N/A')}")
        print(f"  Message: {error['message']}")
        if error.get("event_type"):
            print(f"  Event: {error['event_type']}")

    print(f"\n  Total errors shown: {min(len(errors), limit)} of {len(errors)}")
    print()


def show_user_activity(user_id: str, hours: int = 24):
    """Show activity for specific user."""
    print_header(f"User Activity: {user_id} - Last {hours} Hours")

    # Check all log files
    for log_name, log_path in [
        ("Application", Path("logs/app.log")),
        ("Metrics", Path("logs/metrics.log")),
        ("Audit", Path("logs/audit.log")),
    ]:
        if not log_path.exists():
            continue

        analyzer = LogAnalyzer(log_path)
        activity = analyzer.get_user_activity(user_id, hours)

        if activity["total_actions"] > 0:
            print(f"\n  {log_name}:")
            print_stats(activity, indent=2)

    print()


def show_metrics(hours: int = 24):
    """Show detailed metrics."""
    print_header(f"Business Metrics - Last {hours} Hours")

    metrics_analyzer = MetricsAnalyzer(Path("logs/metrics.log"))

    # File uploads
    print("\n  File Uploads:")
    upload_stats = metrics_analyzer.get_file_upload_stats(hours)
    print_stats(upload_stats, indent=2)

    # LLM usage
    print("\n  LLM Usage:")
    llm_stats = metrics_analyzer.get_llm_usage_stats(hours)
    print_stats(llm_stats, indent=2)

    # Visualizations
    print("\n  Visualizations:")
    viz_stats = metrics_analyzer.get_visualization_stats(hours)
    print_stats(viz_stats, indent=2)

    print()


def show_security(hours: int = 24):
    """Show security insights."""
    print_header(f"Security Insights - Last {hours} Hours")

    audit_analyzer = AuditAnalyzer(Path("logs/audit.log"))

    # Authentication
    print("\n  Authentication:")
    auth_stats = audit_analyzer.get_authentication_stats(hours)
    print_stats(auth_stats, indent=2)

    # Access patterns
    print("\n  Data Access:")
    access_stats = audit_analyzer.get_access_patterns(hours)
    print_stats(access_stats, indent=2)

    # Anomalies
    anomalies = audit_analyzer.detect_anomalies(hours)
    if anomalies:
        print("\n  ⚠️  Detected Anomalies:")
        for anomaly in anomalies:
            print(f"\n    [{anomaly['severity'].upper()}] {anomaly['type']}")
            print(f"    {anomaly['description']}")

    print()


def export_json(hours: int = 24, output: str = "dashboard.json"):
    """Export dashboard data as JSON."""
    report = generate_dashboard_report(
        Path("logs/app.log"),
        Path("logs/metrics.log"),
        Path("logs/audit.log"),
        hours=hours,
    )

    with open(output, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Dashboard data exported to {output}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="KooAI Log Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show overview for last 24 hours
  python log_dashboard.py overview

  # Show overview for last hour
  python log_dashboard.py overview --hours 1

  # Show recent errors
  python log_dashboard.py errors

  # Show user activity
  python log_dashboard.py user usr_abc123

  # Show business metrics
  python log_dashboard.py metrics --hours 168

  # Show security insights
  python log_dashboard.py security

  # Export to JSON
  python log_dashboard.py export --output report.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Overview command
    overview_parser = subparsers.add_parser("overview", help="Show dashboard overview")
    overview_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )

    # Errors command
    errors_parser = subparsers.add_parser("errors", help="Show recent errors")
    errors_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )
    errors_parser.add_argument(
        "--limit", type=int, default=20, help="Number of errors to show (default: 20)"
    )

    # User command
    user_parser = subparsers.add_parser("user", help="Show user activity")
    user_parser.add_argument("user_id", help="User ID to analyze")
    user_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Show business metrics")
    metrics_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )

    # Security command
    security_parser = subparsers.add_parser("security", help="Show security insights")
    security_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )

    # Export command
    export_parser = subparsers.add_parser("export", help="Export data as JSON")
    export_parser.add_argument(
        "--hours", type=int, default=24, help="Hours to analyze (default: 24)"
    )
    export_parser.add_argument(
        "--output", type=str, default="dashboard.json", help="Output file"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == "overview":
        show_overview(args.hours)
    elif args.command == "errors":
        show_errors(args.hours, args.limit)
    elif args.command == "user":
        show_user_activity(args.user_id, args.hours)
    elif args.command == "metrics":
        show_metrics(args.hours)
    elif args.command == "security":
        show_security(args.hours)
    elif args.command == "export":
        export_json(args.hours, args.output)


if __name__ == "__main__":
    main()
