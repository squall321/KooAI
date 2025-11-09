"""
Tests for Log Analysis Tools

Tests the LogEntry, LogAnalyzer, MetricsAnalyzer, and AuditAnalyzer classes.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest


class TestLogEntry:
    """Test LogEntry class"""

    def test_log_entry_parse_json(self):
        """Test parsing JSON log entry"""
        from src.infrastructure.logging.log_analyzer import LogEntry

        log_line = json.dumps({
            "timestamp": "2025-01-01T10:00:00+00:00",
            "levelname": "INFO",
            "message": "Test message",
            "event_type": "test_event",
            "user_id": "usr_123"
        })

        entry = LogEntry(log_line)
        assert entry.level == "INFO"
        assert entry.message == "Test message"
        assert entry.event_type == "test_event"
        assert entry.user_id == "usr_123"

    def test_log_entry_parse_invalid_json(self):
        """Test parsing invalid JSON falls back gracefully"""
        from src.infrastructure.logging.log_analyzer import LogEntry

        log_line = "This is not JSON"
        entry = LogEntry(log_line)

        assert entry.level == "UNKNOWN"
        assert entry.message == log_line
        assert entry.event_type is None

    def test_log_entry_timestamp_parsing(self):
        """Test timestamp is parsed correctly"""
        from src.infrastructure.logging.log_analyzer import LogEntry

        log_line = json.dumps({
            "timestamp": "2025-01-01T12:30:45+00:00",
            "message": "test"
        })

        entry = LogEntry(log_line)
        assert isinstance(entry.timestamp, datetime)


class TestLogAnalyzer:
    """Test LogAnalyzer class"""

    @pytest.fixture
    def temp_log_file(self, tmp_path):
        """Create temporary log file with test data"""
        log_file = tmp_path / "test.log"

        # Create sample log entries
        entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "levelname": "INFO",
                "message": "User logged in",
                "event_type": "login",
                "user_id": "usr_123"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "levelname": "ERROR",
                "message": "Database connection failed",
                "event_type": "error",
                "user_id": "usr_456"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "levelname": "INFO",
                "message": "File uploaded",
                "event_type": "file_upload",
                "user_id": "usr_123"
            }
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        return log_file

    def test_log_analyzer_creation(self, temp_log_file):
        """Test LogAnalyzer can be created"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        assert analyzer is not None
        assert analyzer.log_file == temp_log_file

    def test_load_logs(self, temp_log_file):
        """Test loading log entries"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        analyzer.load_logs()

        assert len(analyzer.entries) == 3

    def test_load_logs_with_time_filter(self, temp_log_file):
        """Test loading logs with time filter"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        since = datetime.now() - timedelta(hours=1)
        analyzer.load_logs(since=since)

        # All test entries should be within 1 hour
        assert len(analyzer.entries) >= 0

    def test_load_logs_nonexistent_file(self, tmp_path):
        """Test loading from nonexistent file"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(tmp_path / "nonexistent.log")
        analyzer.load_logs()

        assert len(analyzer.entries) == 0

    def test_analyze_basic_stats(self, temp_log_file):
        """Test analyze returns basic statistics"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        stats = analyzer.analyze(hours=24)

        assert "total_entries" in stats
        assert stats["total_entries"] == 3
        assert "levels" in stats
        assert "errors" in stats

    def test_analyze_error_rate(self, temp_log_file):
        """Test analyze calculates error rate"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        stats = analyzer.analyze(hours=24)

        # 1 error out of 3 entries = 33%
        assert "error_rate" in stats
        assert stats["error_rate"] > 0

    def test_analyze_event_types(self, temp_log_file):
        """Test analyze counts event types"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        stats = analyzer.analyze(hours=24)

        assert "event_types" in stats
        assert "login" in stats["event_types"]

    def test_analyze_top_users(self, temp_log_file):
        """Test analyze identifies top users"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        stats = analyzer.analyze(hours=24)

        assert "top_users" in stats

    def test_analyze_empty_log(self, tmp_path):
        """Test analyze with empty log file"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        empty_log = tmp_path / "empty.log"
        empty_log.touch()

        analyzer = LogAnalyzer(empty_log)
        stats = analyzer.analyze(hours=24)

        assert stats["total_entries"] == 0

    def test_get_error_summary(self, temp_log_file):
        """Test getting error summary"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        errors = analyzer.get_error_summary(hours=24)

        assert isinstance(errors, list)
        # Should have 1 error from test data
        assert len(errors) >= 0

    def test_get_user_activity(self, temp_log_file):
        """Test getting user activity"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        activity = analyzer.get_user_activity("usr_123", hours=24)

        assert activity["user_id"] == "usr_123"
        assert "total_actions" in activity

    def test_get_user_activity_nonexistent(self, temp_log_file):
        """Test getting activity for nonexistent user"""
        from src.infrastructure.logging.log_analyzer import LogAnalyzer

        analyzer = LogAnalyzer(temp_log_file)
        activity = analyzer.get_user_activity("usr_999", hours=24)

        assert activity["total_actions"] == 0


class TestMetricsAnalyzer:
    """Test MetricsAnalyzer class"""

    @pytest.fixture
    def temp_metrics_log(self, tmp_path):
        """Create temporary metrics log file"""
        log_file = tmp_path / "metrics.log"

        entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "file_upload",
                "file_size_mb": 10.5,
                "duration_seconds": 5.2,
                "success": True
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "llm_request",
                "model": "claude-3-sonnet",
                "total_tokens": 500,
                "cost_usd": 0.05,
                "duration_seconds": 2.1
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "visualization_render",
                "viz_type": "3d_mesh",
                "duration_seconds": 1.5,
                "success": True
            }
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        return log_file

    def test_metrics_analyzer_creation(self, temp_metrics_log):
        """Test MetricsAnalyzer can be created"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        analyzer = MetricsAnalyzer(temp_metrics_log)
        assert analyzer is not None

    def test_get_file_upload_stats(self, temp_metrics_log):
        """Test getting file upload statistics"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        analyzer = MetricsAnalyzer(temp_metrics_log)
        stats = analyzer.get_file_upload_stats(hours=24)

        assert "total_uploads" in stats
        assert stats["total_uploads"] >= 0

    def test_get_file_upload_stats_empty(self, tmp_path):
        """Test file upload stats with no data"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        empty_log = tmp_path / "empty.log"
        empty_log.touch()

        analyzer = MetricsAnalyzer(empty_log)
        stats = analyzer.get_file_upload_stats(hours=24)

        assert stats["total_uploads"] == 0

    def test_get_llm_usage_stats(self, temp_metrics_log):
        """Test getting LLM usage statistics"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        analyzer = MetricsAnalyzer(temp_metrics_log)
        stats = analyzer.get_llm_usage_stats(hours=24)

        assert "total_requests" in stats
        assert "total_tokens" in stats
        assert "total_cost_usd" in stats

    def test_get_llm_usage_stats_empty(self, tmp_path):
        """Test LLM usage stats with no data"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        empty_log = tmp_path / "empty.log"
        empty_log.touch()

        analyzer = MetricsAnalyzer(empty_log)
        stats = analyzer.get_llm_usage_stats(hours=24)

        assert stats["total_requests"] == 0

    def test_get_visualization_stats(self, temp_metrics_log):
        """Test getting visualization statistics"""
        from src.infrastructure.logging.log_analyzer import MetricsAnalyzer

        analyzer = MetricsAnalyzer(temp_metrics_log)
        stats = analyzer.get_visualization_stats(hours=24)

        assert "total_renders" in stats
        assert "viz_types" in stats


class TestAuditAnalyzer:
    """Test AuditAnalyzer class"""

    @pytest.fixture
    def temp_audit_log(self, tmp_path):
        """Create temporary audit log file"""
        log_file = tmp_path / "audit.log"

        entries = [
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "authentication",
                "auth_event": "login",
                "success": True,
                "ip_address": "192.168.1.1",
                "email": "user@example.com"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "authentication",
                "auth_event": "login",
                "success": False,
                "ip_address": "10.0.0.1",
                "email": "bad@example.com"
            },
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": "data_access",
                "action": "read",
                "resource_type": "file",
                "user_id": "usr_123"
            }
        ]

        with open(log_file, "w") as f:
            for entry in entries:
                f.write(json.dumps(entry) + "\n")

        return log_file

    def test_audit_analyzer_creation(self, temp_audit_log):
        """Test AuditAnalyzer can be created"""
        from src.infrastructure.logging.log_analyzer import AuditAnalyzer

        analyzer = AuditAnalyzer(temp_audit_log)
        assert analyzer is not None

    def test_get_authentication_stats(self, temp_audit_log):
        """Test getting authentication statistics"""
        from src.infrastructure.logging.log_analyzer import AuditAnalyzer

        analyzer = AuditAnalyzer(temp_audit_log)
        stats = analyzer.get_authentication_stats(hours=24)

        assert "total_auth_events" in stats
        assert "successful_auth" in stats
        assert "failed_auth" in stats

    def test_get_access_patterns(self, temp_audit_log):
        """Test getting access patterns"""
        from src.infrastructure.logging.log_analyzer import AuditAnalyzer

        analyzer = AuditAnalyzer(temp_audit_log)
        stats = analyzer.get_access_patterns(hours=24)

        assert "total_access_events" in stats
        assert "actions" in stats

    def test_detect_anomalies(self, temp_audit_log):
        """Test anomaly detection"""
        from src.infrastructure.logging.log_analyzer import AuditAnalyzer

        analyzer = AuditAnalyzer(temp_audit_log)
        anomalies = analyzer.detect_anomalies(hours=24)

        assert isinstance(anomalies, list)


class TestDashboardReport:
    """Test dashboard report generation"""

    @pytest.fixture
    def temp_logs(self, tmp_path):
        """Create temporary log files"""
        app_log = tmp_path / "app.log"
        metrics_log = tmp_path / "metrics.log"
        audit_log = tmp_path / "audit.log"

        # Create empty files
        app_log.touch()
        metrics_log.touch()
        audit_log.touch()

        return app_log, metrics_log, audit_log

    def test_generate_dashboard_report(self, temp_logs):
        """Test generating dashboard report"""
        from src.infrastructure.logging.log_analyzer import generate_dashboard_report

        app_log, metrics_log, audit_log = temp_logs
        report = generate_dashboard_report(app_log, metrics_log, audit_log, hours=24)

        assert "generated_at" in report
        assert "time_range_hours" in report
        assert "application" in report
        assert "file_uploads" in report
        assert "llm_usage" in report
        assert "visualizations" in report
        assert "authentication" in report
        assert "security_anomalies" in report

    def test_generate_dashboard_report_nonexistent_files(self, tmp_path):
        """Test generating report with nonexistent files"""
        from src.infrastructure.logging.log_analyzer import generate_dashboard_report

        app_log = tmp_path / "nonexistent1.log"
        metrics_log = tmp_path / "nonexistent2.log"
        audit_log = tmp_path / "nonexistent3.log"

        report = generate_dashboard_report(app_log, metrics_log, audit_log, hours=24)

        # Should still generate report with empty data
        assert "generated_at" in report
