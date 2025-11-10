"""
Log Analysis Tools

Analyze structured logs for insights and anomaly detection.
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import statistics


class LogEntry:
    """Parsed log entry."""

    def __init__(self, raw_line: str):
        """Parse log line."""
        try:
            self.data = json.loads(raw_line)
            self.timestamp = datetime.fromisoformat(
                self.data.get("timestamp", "").replace("Z", "+00:00")
            )
            self.level = self.data.get("levelname", "INFO")
            self.message = self.data.get("message", "")
            self.event_type = self.data.get("event_type")
            self.user_id = self.data.get("user_id")
        except (json.JSONDecodeError, ValueError):
            # Fallback for non-JSON logs
            self.data = {"raw": raw_line}
            self.timestamp = datetime.now()
            self.level = "UNKNOWN"
            self.message = raw_line
            self.event_type = None
            self.user_id = None


class LogAnalyzer:
    """
    Log analysis and statistics.

    Analyzes structured logs for patterns, errors, and metrics.
    """

    def __init__(self, log_file: Path):
        """
        Initialize log analyzer.

        Args:
            log_file: Path to log file

        Example:
            ```python
            analyzer = LogAnalyzer(Path("logs/app.log"))
            stats = analyzer.analyze(hours=24)
            print(f"Total entries: {stats['total_entries']}")
            print(f"Error rate: {stats['error_rate']:.2%}")
            ```
        """
        self.log_file = log_file
        self.entries: List[LogEntry] = []

    def load_logs(
        self, since: Optional[datetime] = None, until: Optional[datetime] = None
    ) -> None:
        """
        Load log entries from file.

        Args:
            since: Start time filter
            until: End time filter
        """
        self.entries = []

        if not self.log_file.exists():
            return

        with open(self.log_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                entry = LogEntry(line)

                # Time filter
                if since and entry.timestamp < since:
                    continue
                if until and entry.timestamp > until:
                    continue

                self.entries.append(entry)

    def analyze(self, hours: int = 24) -> Dict:
        """
        Analyze logs for the past N hours.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with analysis results

        Example:
            ```python
            analyzer = LogAnalyzer(Path("logs/app.log"))
            stats = analyzer.analyze(hours=1)

            print(f"Requests: {stats['total_entries']}")
            print(f"Errors: {stats['errors']}")
            print(f"Top users: {stats['top_users']}")
            ```
        """
        since = datetime.now() - timedelta(hours=hours)
        self.load_logs(since=since)

        if not self.entries:
            return {
                "total_entries": 0,
                "time_range": {"since": since.isoformat(), "until": datetime.now().isoformat()},
            }

        # Basic stats
        total = len(self.entries)
        levels = Counter(entry.level for entry in self.entries)
        event_types = Counter(
            entry.event_type for entry in self.entries if entry.event_type
        )
        users = Counter(entry.user_id for entry in self.entries if entry.user_id)

        # Error analysis
        errors = [e for e in self.entries if e.level in ("ERROR", "CRITICAL")]
        error_messages = Counter(e.message for e in errors)

        # Time-based analysis
        hourly_distribution: defaultdict[str, int] = defaultdict(int)
        for entry in self.entries:
            hour = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            hourly_distribution[hour.isoformat()] += 1

        return {
            "total_entries": total,
            "time_range": {
                "since": since.isoformat(),
                "until": datetime.now().isoformat(),
                "hours": hours,
            },
            "levels": dict(levels),
            "errors": len(errors),
            "error_rate": len(errors) / total if total > 0 else 0,
            "event_types": dict(event_types.most_common(10)),
            "top_users": dict(users.most_common(10)),
            "top_errors": dict(error_messages.most_common(10)),
            "hourly_distribution": dict(hourly_distribution),
        }

    def get_error_summary(self, hours: int = 24) -> List[Dict]:
        """
        Get detailed error summary.

        Args:
            hours: Number of hours to analyze

        Returns:
            List of error details
        """
        since = datetime.now() - timedelta(hours=hours)
        self.load_logs(since=since)

        errors = [e for e in self.entries if e.level in ("ERROR", "CRITICAL")]

        summary = []
        for error in errors[-100:]:  # Last 100 errors
            summary.append(
                {
                    "timestamp": error.timestamp.isoformat(),
                    "level": error.level,
                    "message": error.message,
                    "user_id": error.user_id,
                    "event_type": error.event_type,
                    "data": error.data,
                }
            )

        return summary

    def get_user_activity(self, user_id: str, hours: int = 24) -> Dict:
        """
        Get activity summary for specific user.

        Args:
            user_id: User ID
            hours: Number of hours to analyze

        Returns:
            User activity summary
        """
        since = datetime.now() - timedelta(hours=hours)
        self.load_logs(since=since)

        user_entries = [e for e in self.entries if e.user_id == user_id]

        if not user_entries:
            return {"user_id": user_id, "total_actions": 0}

        event_types = Counter(e.event_type for e in user_entries if e.event_type)

        return {
            "user_id": user_id,
            "total_actions": len(user_entries),
            "event_types": dict(event_types),
            "first_seen": min(e.timestamp for e in user_entries).isoformat(),
            "last_seen": max(e.timestamp for e in user_entries).isoformat(),
        }


class MetricsAnalyzer:
    """
    Analyze metrics logs for business insights.

    Focuses on business metrics like uploads, LLM usage, etc.
    """

    def __init__(self, metrics_log: Path):
        """Initialize metrics analyzer."""
        self.log_file = metrics_log
        self.analyzer = LogAnalyzer(metrics_log)

    def get_file_upload_stats(self, hours: int = 24) -> Dict:
        """Get file upload statistics."""
        since = datetime.now() - timedelta(hours=hours)
        self.analyzer.load_logs(since=since)

        uploads = [
            e
            for e in self.analyzer.entries
            if e.event_type == "file_upload" and "file_size_mb" in e.data
        ]

        if not uploads:
            return {"total_uploads": 0}

        file_sizes = [e.data["file_size_mb"] for e in uploads]
        durations = [
            e.data.get("duration_seconds", 0)
            for e in uploads
            if "duration_seconds" in e.data
        ]
        successful = [e for e in uploads if e.data.get("success", False)]

        return {
            "total_uploads": len(uploads),
            "successful_uploads": len(successful),
            "success_rate": len(successful) / len(uploads) if uploads else 0,
            "total_size_mb": sum(file_sizes),
            "avg_size_mb": statistics.mean(file_sizes) if file_sizes else 0,
            "max_size_mb": max(file_sizes) if file_sizes else 0,
            "avg_duration_seconds": statistics.mean(durations) if durations else 0,
            "throughput_mb_per_hour": sum(file_sizes) / hours if hours > 0 else 0,
        }

    def get_llm_usage_stats(self, hours: int = 24) -> Dict:
        """Get LLM usage statistics."""
        since = datetime.now() - timedelta(hours=hours)
        self.analyzer.load_logs(since=since)

        llm_requests = [
            e for e in self.analyzer.entries if e.event_type == "llm_request"
        ]

        if not llm_requests:
            return {"total_requests": 0}

        total_tokens = sum(e.data.get("total_tokens", 0) for e in llm_requests)
        total_cost = sum(e.data.get("cost_usd", 0) for e in llm_requests)
        models = Counter(e.data.get("model") for e in llm_requests)
        durations = [
            e.data.get("duration_seconds", 0)
            for e in llm_requests
            if "duration_seconds" in e.data
        ]

        return {
            "total_requests": len(llm_requests),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 2),
            "avg_tokens_per_request": (
                total_tokens / len(llm_requests) if llm_requests else 0
            ),
            "avg_cost_per_request_usd": (
                total_cost / len(llm_requests) if llm_requests else 0
            ),
            "avg_duration_seconds": statistics.mean(durations) if durations else 0,
            "models_used": dict(models),
            "tokens_per_hour": total_tokens / hours if hours > 0 else 0,
            "cost_per_hour_usd": total_cost / hours if hours > 0 else 0,
        }

    def get_visualization_stats(self, hours: int = 24) -> Dict:
        """Get visualization render statistics."""
        since = datetime.now() - timedelta(hours=hours)
        self.analyzer.load_logs(since=since)

        viz_renders = [
            e for e in self.analyzer.entries if e.event_type == "visualization_render"
        ]

        if not viz_renders:
            return {"total_renders": 0}

        viz_types = Counter(e.data.get("viz_type") for e in viz_renders)
        successful = [e for e in viz_renders if e.data.get("success", False)]
        durations = [
            e.data.get("duration_seconds", 0)
            for e in viz_renders
            if "duration_seconds" in e.data
        ]

        return {
            "total_renders": len(viz_renders),
            "successful_renders": len(successful),
            "success_rate": len(successful) / len(viz_renders) if viz_renders else 0,
            "viz_types": dict(viz_types),
            "avg_duration_seconds": statistics.mean(durations) if durations else 0,
            "max_duration_seconds": max(durations) if durations else 0,
        }


class AuditAnalyzer:
    """
    Analyze audit logs for security insights.

    Focuses on authentication, authorization, and access patterns.
    """

    def __init__(self, audit_log: Path):
        """Initialize audit analyzer."""
        self.log_file = audit_log
        self.analyzer = LogAnalyzer(audit_log)

    def get_authentication_stats(self, hours: int = 24) -> Dict:
        """Get authentication statistics."""
        since = datetime.now() - timedelta(hours=hours)
        self.analyzer.load_logs(since=since)

        auth_events = [
            e for e in self.analyzer.entries if e.event_type == "authentication"
        ]

        if not auth_events:
            return {"total_auth_events": 0}

        successful = [e for e in auth_events if e.data.get("success", False)]
        failed = [e for e in auth_events if not e.data.get("success", False)]
        logins = [e for e in auth_events if e.data.get("auth_event") == "login"]
        failed_logins = [
            e for e in failed if e.data.get("auth_event") == "login"
        ]

        # Failed login attempts by IP
        failed_ips = Counter(
            e.data.get("ip_address") for e in failed_logins if "ip_address" in e.data
        )

        # Failed login attempts by email
        failed_emails = Counter(
            e.data.get("email") for e in failed_logins if "email" in e.data
        )

        return {
            "total_auth_events": len(auth_events),
            "successful_auth": len(successful),
            "failed_auth": len(failed),
            "success_rate": len(successful) / len(auth_events) if auth_events else 0,
            "total_logins": len(logins),
            "failed_logins": len(failed_logins),
            "suspicious_ips": dict(failed_ips.most_common(10)),
            "suspicious_emails": dict(failed_emails.most_common(10)),
        }

    def get_access_patterns(self, hours: int = 24) -> Dict:
        """Get data access patterns."""
        since = datetime.now() - timedelta(hours=hours)
        self.analyzer.load_logs(since=since)

        access_events = [
            e for e in self.analyzer.entries if e.event_type == "data_access"
        ]

        if not access_events:
            return {"total_access_events": 0}

        actions = Counter(e.data.get("action") for e in access_events)
        resource_types = Counter(e.data.get("resource_type") for e in access_events)
        users = Counter(e.data.get("user_id") for e in access_events)

        return {
            "total_access_events": len(access_events),
            "actions": dict(actions),
            "resource_types": dict(resource_types),
            "top_users": dict(users.most_common(10)),
        }

    def detect_anomalies(self, hours: int = 24) -> List[Dict]:
        """
        Detect potential security anomalies.

        Returns:
            List of potential security issues
        """
        anomalies = []

        # High number of failed logins
        auth_stats = self.get_authentication_stats(hours)
        if auth_stats.get("failed_logins", 0) > 10:
            anomalies.append(
                {
                    "type": "high_failed_logins",
                    "severity": "medium",
                    "count": auth_stats["failed_logins"],
                    "description": f"{auth_stats['failed_logins']} failed login attempts in {hours} hours",
                }
            )

        # Suspicious IP addresses
        if auth_stats.get("suspicious_ips"):
            for ip, count in list(auth_stats["suspicious_ips"].items())[:3]:
                if count > 5:
                    anomalies.append(
                        {
                            "type": "suspicious_ip",
                            "severity": "high",
                            "ip_address": ip,
                            "count": count,
                            "description": f"IP {ip} had {count} failed login attempts",
                        }
                    )

        return anomalies


def generate_dashboard_report(
    app_log: Path,
    metrics_log: Path,
    audit_log: Path,
    hours: int = 24,
) -> Dict:
    """
    Generate comprehensive dashboard report.

    Args:
        app_log: Application log file
        metrics_log: Metrics log file
        audit_log: Audit log file
        hours: Number of hours to analyze

    Returns:
        Complete dashboard data

    Example:
        ```python
        report = generate_dashboard_report(
            Path("logs/app.log"),
            Path("logs/metrics.log"),
            Path("logs/audit.log"),
            hours=24
        )

        print(json.dumps(report, indent=2))
        ```
    """
    # Application logs
    app_analyzer = LogAnalyzer(app_log) if app_log.exists() else None
    app_stats = app_analyzer.analyze(hours) if app_analyzer else {}

    # Metrics logs
    metrics_analyzer = MetricsAnalyzer(metrics_log) if metrics_log.exists() else None
    if metrics_analyzer:
        upload_stats = metrics_analyzer.get_file_upload_stats(hours)
        llm_stats = metrics_analyzer.get_llm_usage_stats(hours)
        viz_stats = metrics_analyzer.get_visualization_stats(hours)
    else:
        upload_stats = {}
        llm_stats = {}
        viz_stats = {}

    # Audit logs
    audit_analyzer = AuditAnalyzer(audit_log) if audit_log.exists() else None
    if audit_analyzer:
        auth_stats = audit_analyzer.get_authentication_stats(hours)
        access_stats = audit_analyzer.get_access_patterns(hours)
        anomalies = audit_analyzer.detect_anomalies(hours)
    else:
        auth_stats = {}
        access_stats = {}
        anomalies = []

    return {
        "generated_at": datetime.now().isoformat(),
        "time_range_hours": hours,
        "application": app_stats,
        "file_uploads": upload_stats,
        "llm_usage": llm_stats,
        "visualizations": viz_stats,
        "authentication": auth_stats,
        "data_access": access_stats,
        "security_anomalies": anomalies,
    }
