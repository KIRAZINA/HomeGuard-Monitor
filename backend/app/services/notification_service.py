import structlog
from typing import List
import aiohttp
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.models.alert import Alert, AlertRule

logger = structlog.get_logger()


class NotificationService:
    def __init__(self):
        self.telegram_bot_token = settings.TELEGRAM_BOT_TOKEN
        self.discord_webhook_url = settings.DISCORD_WEBHOOK_URL
        self.twilio_account_sid = settings.TWILIO_ACCOUNT_SID
        self.twilio_auth_token = settings.TWILIO_AUTH_TOKEN
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD

    async def send_alert_notifications(self, alert: Alert, rule: AlertRule):
        """Send notifications through all configured channels"""
        if not rule.notification_channels:
            return
        
        for channel in rule.notification_channels:
            try:
                if channel == "email":
                    await self._send_email_notification(alert, rule)
                elif channel == "telegram":
                    await self._send_telegram_notification(alert, rule)
                elif channel == "discord":
                    await self._send_discord_notification(alert, rule)
                elif channel == "sms":
                    await self._send_sms_notification(alert, rule)
            except Exception as e:
                logger.error("Failed to send notification", 
                           channel=channel, 
                           alert_id=alert.id, 
                           error=str(e))

    async def _send_email_notification(self, alert: Alert, rule: AlertRule):
        """Send email notification"""
        if not all([self.smtp_host, self.smtp_username, self.smtp_password]):
            logger.warning("Email configuration missing")
            return
        
        message = MIMEMultipart()
        message["From"] = self.smtp_username
        message["To"] = self.smtp_username  # Send to self for now
        message["Subject"] = f"HomeGuard Alert: {rule.name}"
        
        body = f"""
        Alert: {rule.name}
        Severity: {alert.severity}
        Device ID: {alert.device_id}
        Metric: {alert.metric_type}
        Value: {alert.trigger_value}
        Message: {alert.message}
        Time: {alert.triggered_at}
        """
        
        message.attach(MIMEText(body, "plain"))
        
        await aiosmtplib.send(
            message,
            hostname=self.smtp_host,
            port=self.smtp_port,
            start_tls=True,
            username=self.smtp_username,
            password=self.smtp_password,
        )
        
        logger.info("Email notification sent", alert_id=alert.id)

    async def _send_telegram_notification(self, alert: Alert, rule: AlertRule):
        """Send Telegram notification"""
        if not self.telegram_bot_token:
            logger.warning("Telegram bot token not configured")
            return
        
        # This would need to be configured with chat IDs
        # For now, we'll just log the message
        message = f"""
        🚨 *HomeGuard Alert*
        
        *Alert:* {rule.name}
        *Severity:* {alert.severity}
        *Device:* {alert.device_id}
        *Metric:* {alert.metric_type}
        *Value:* {alert.trigger_value}
        *Message:* {alert.message}
        """
        
        logger.info("Telegram notification would be sent", 
                   alert_id=alert.id, 
                   message=message)

    async def _send_discord_notification(self, alert: Alert, rule: AlertRule):
        """Send Discord notification"""
        if not self.discord_webhook_url:
            logger.warning("Discord webhook URL not configured")
            return
        
        embed = {
            "title": f"HomeGuard Alert: {rule.name}",
            "description": alert.message,
            "color": self._get_discord_color(alert.severity),
            "fields": [
                {"name": "Severity", "value": alert.severity, "inline": True},
                {"name": "Device ID", "value": str(alert.device_id), "inline": True},
                {"name": "Metric", "value": alert.metric_type, "inline": True},
                {"name": "Value", "value": str(alert.trigger_value), "inline": True},
            ],
            "timestamp": alert.triggered_at.isoformat()
        }
        
        payload = {"embeds": [embed]}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.discord_webhook_url, json=payload) as response:
                if response.status == 204:
                    logger.info("Discord notification sent", alert_id=alert.id)
                else:
                    logger.error("Failed to send Discord notification", 
                               status=response.status, 
                               alert_id=alert.id)

    async def _send_sms_notification(self, alert: Alert, rule: AlertRule):
        """Send SMS notification via Twilio"""
        if not all([self.twilio_account_sid, self.twilio_auth_token]):
            logger.warning("Twilio configuration missing")
            return
        
        # This would need phone numbers to be configured
        message = f"HomeGuard Alert: {rule.name} - {alert.message}"
        
        logger.info("SMS notification would be sent", 
                   alert_id=alert.id, 
                   message=message)

    def _get_discord_color(self, severity: str) -> int:
        """Get Discord embed color based on severity"""
        colors = {
            "info": 0x3498db,      # Blue
            "warning": 0xf39c12,   # Orange
            "critical": 0xe74c3c,  # Red
        }
        return colors.get(severity, 0x95a5a6)  # Default gray
