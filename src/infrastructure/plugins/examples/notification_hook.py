"""
Example Plugin: Email Notification Hook

Demonstrates how to create a hook plugin that responds to events.
"""

from typing import Dict, Any, List
import logging

from src.infrastructure.plugins.plugin_interface import (
    HookPlugin,
    HookEvent,
    PluginContext,
    PluginType,
    PluginPriority,
    plugin,
)

logger = logging.getLogger(__name__)


@plugin(
    name="email-notifications",
    version="1.0.0",
    description="Sends email notifications on simulation events",
    author="KooAI Team",
    plugin_type=PluginType.HOOK,
    priority=PluginPriority.NORMAL,
    tags=["notifications", "email"],
)
class EmailNotificationHook(HookPlugin):
    """
    Sends email notifications when simulations are analyzed or complete.

    Configuration:
        smtp_host: SMTP server host
        smtp_port: SMTP server port
        from_email: Sender email address
        notify_events: List of events to notify on
    """

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize email configuration."""
        self.smtp_host = config.get("smtp_host", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.from_email = config.get("from_email", "noreply@kooai.com")
        self.notify_events = config.get("notify_events", [
            "simulation.analyzed",
            "analysis.failed",
        ])

        logger.info(
            f"Email notifications configured: {self.smtp_host}:{self.smtp_port}"
        )

    def get_events(self) -> List[HookEvent]:
        """Register events to listen to."""
        events = []
        for event_str in self.notify_events:
            try:
                events.append(HookEvent(event_str))
            except ValueError:
                logger.warning(f"Unknown event: {event_str}")

        return events

    async def on_event(
        self, event: HookEvent, data: Dict[str, Any], context: PluginContext
    ) -> None:
        """
        Handle event by sending email notification.

        Args:
            event: Event that occurred
            data: Event data (user_email, simulation_id, etc.)
            context: Plugin context
        """
        user_email = data.get("user_email")
        if not user_email:
            logger.warning("No user_email in event data, skipping notification")
            return

        # Build notification based on event type
        if event == HookEvent.SIMULATION_ANALYZED:
            subject = "Simulation Analysis Complete"
            message = self._build_analysis_complete_message(data)

        elif event == HookEvent.ANALYSIS_FAILED:
            subject = "Simulation Analysis Failed"
            message = self._build_analysis_failed_message(data)

        elif event == HookEvent.SIMULATION_UPLOADED:
            subject = "Simulation Uploaded Successfully"
            message = self._build_upload_success_message(data)

        else:
            subject = f"KooAI Event: {event.value}"
            message = f"Event data: {data}"

        # Send email (mock implementation)
        await self._send_email(user_email, subject, message, context)

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        context: PluginContext,
    ) -> None:
        """
        Send email notification.

        In production, this would use SMTP or a service like SendGrid.
        """
        logger.info(
            f"[EMAIL NOTIFICATION] "
            f"To: {to_email} | "
            f"Subject: {subject} | "
            f"Tenant: {context.tenant_id or 'none'}"
        )

        # Mock email sending
        # In production:
        # import smtplib
        # from email.mime.text import MIMEText
        #
        # msg = MIMEText(message)
        # msg['Subject'] = subject
        # msg['From'] = self.from_email
        # msg['To'] = to_email
        #
        # with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
        #     server.starttls()
        #     server.sendmail(self.from_email, [to_email], msg.as_string())

    def _build_analysis_complete_message(self, data: Dict[str, Any]) -> str:
        """Build message for analysis complete event."""
        simulation_id = data.get("simulation_id", "unknown")
        results = data.get("results", {})

        message = f"""
Hello,

Your simulation analysis has completed successfully!

Simulation ID: {simulation_id}

Results Summary:
{self._format_results(results)}

You can view the full results in your KooAI dashboard.

Best regards,
KooAI Team
        """
        return message.strip()

    def _build_analysis_failed_message(self, data: Dict[str, Any]) -> str:
        """Build message for analysis failed event."""
        simulation_id = data.get("simulation_id", "unknown")
        error = data.get("error", "Unknown error")

        message = f"""
Hello,

Unfortunately, your simulation analysis has failed.

Simulation ID: {simulation_id}
Error: {error}

Please check your simulation data and try again, or contact support if the issue persists.

Best regards,
KooAI Team
        """
        return message.strip()

    def _build_upload_success_message(self, data: Dict[str, Any]) -> str:
        """Build message for upload success event."""
        simulation_id = data.get("simulation_id", "unknown")
        filename = data.get("filename", "unknown")

        message = f"""
Hello,

Your simulation has been uploaded successfully!

Simulation ID: {simulation_id}
Filename: {filename}

You can now analyze your simulation in the KooAI dashboard.

Best regards,
KooAI Team
        """
        return message.strip()

    def _format_results(self, results: Dict[str, Any]) -> str:
        """Format results dictionary for email."""
        if not results:
            return "No results available"

        lines = []
        for key, value in results.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  - {sub_key}: {sub_value}")
            else:
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)
