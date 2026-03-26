"""알림 발송 연동 도구.

운영 이상 지표 감지 시 관리자 알림 발송 (이메일/Slack).
자동 처리율 60% 미만, 특정 FAQ 오답 3회 연속 발생 등.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import structlog

logger = structlog.get_logger()


class Notifier:
    """Real 알림 발송 (Slack Webhook / 이메일).

    현재 stub 구현이며, 실제 Webhook 연동 시 교체 필요.
    """

    def __init__(self, settings: Any = None) -> None:
        self._settings = settings
        self._webhook_url = (
            settings.notify_webhook_url if settings else ""
        )

    def send_alert(
        self,
        alert_type: str,
        message: str,
        recipients: list[str] | None = None,
    ) -> dict:
        """알림 발송.

        Args:
            alert_type: 알림 유형 (auto_rate_low, faq_error_repeat 등)
            message: 알림 메시지
            recipients: 수신자 목록

        Returns:
            success, sent_at 포함 dict
        """
        # TODO: httpx를 사용한 Slack Webhook 또는 이메일 발송으로 교체
        # POST {webhook_url}
        # Body: {"text": f"[{alert_type}] {message}"}
        logger.warning(
            "알림 발송 (stub)",
            alert_type=alert_type,
            message=message,
            recipients=recipients,
        )

        return {
            "success": True,
            "sent_at": datetime.now(timezone.utc).isoformat(),
        }

    def check_auto_rate_alert(
        self,
        auto_rate: float,
        threshold: float = 60.0,
    ) -> bool:
        """자동 처리율 이상 알림 확인.

        Args:
            auto_rate: 현재 자동 처리율 (%)
            threshold: 알림 임계값 (기본 60%)

        Returns:
            알림 발송 여부
        """
        if auto_rate < threshold:
            self.send_alert(
                alert_type="auto_rate_low",
                message=(
                    f"자동 처리율이 {auto_rate:.1f}%로 "
                    f"임계값({threshold}%) 미만입니다. "
                    f"FAQ 저장소 갱신이 필요합니다."
                ),
            )
            return True
        return False

    def check_faq_error_repeat(
        self,
        faq_item_id: str,
        error_count: int,
        threshold: int = 3,
    ) -> bool:
        """FAQ 오답 반복 알림 확인.

        Args:
            faq_item_id: FAQ 항목 ID
            error_count: 연속 오답 횟수
            threshold: 알림 임계값 (기본 3회)

        Returns:
            알림 발송 여부
        """
        if error_count >= threshold:
            self.send_alert(
                alert_type="faq_error_repeat",
                message=(
                    f"FAQ 항목 '{faq_item_id}'에서 "
                    f"오답이 {error_count}회 연속 발생했습니다. "
                    f"해당 항목을 비활성화하고 검토가 필요합니다."
                ),
            )
            return True
        return False


class MockNotifier(Notifier):
    """Mock 알림 발송 구현.

    실제 외부 서비스를 호출하지 않고 로그만 기록함.
    """

    def __init__(self) -> None:
        super().__init__(settings=None)
        self.sent_alerts: list[dict] = []

    def send_alert(
        self,
        alert_type: str,
        message: str,
        recipients: list[str] | None = None,
    ) -> dict:
        """Mock 알림 발송 - 내부 리스트에 기록."""
        sent_at = datetime.now(timezone.utc).isoformat()
        alert = {
            "alert_type": alert_type,
            "message": message,
            "recipients": recipients or [],
            "sent_at": sent_at,
        }
        self.sent_alerts.append(alert)

        logger.info(
            "Mock 알림 발송",
            alert_type=alert_type,
            message=message[:100],
        )

        return {"success": True, "sent_at": sent_at}
