"""Notification service for alerts."""

from typing import List, Optional
from datetime import datetime, timezone

from app.core.logger import get_logger
from app.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class NotificationService:
    """Service for sending notifications."""

    def __init__(self):
        """Initialize notification service."""
        self.notifications = []

    async def send_alert(
        self,
        alert_type: str,
        message: str,
        recipients: List[str],
    ) -> bool:
        """Send alert notification."""
        try:
            notification = {
                "alert_type": alert_type,
                "message": message,
                "recipients": recipients,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "success": True,
            }
            self.notifications.append(notification)
            logger.info("Alert sent", alert_type=alert_type, recipient_count=len(recipients))
            return True

        except Exception as e:
            logger.error("Failed to send alert", error=str(e))
            return False

    async def send_low_auto_rate_alert(self, auto_rate: float, threshold: float) -> bool:
        """Send alert when auto-rate is below threshold."""
        message = f"자동 처리율이 {auto_rate:.1f}% 로 하락했습니다. (임계값: {threshold:.1f}%)"
        return await self.send_alert("LOW_AUTO_RATE", message, ["admin@example.com"])
