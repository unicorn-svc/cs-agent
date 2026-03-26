"""비용 집계 외부 연동 도구.

자동 처리 완료 시 건당 절감 비용 계산 및 집계 DB 저장.
DSL Node 7의 비용 절감 집계 대응. Mock/Real 전환 가능.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

logger = structlog.get_logger()


class CostTracker:
    """Real 비용 집계 (PostgreSQL 연동).

    자동 처리 완료 건을 DB에 기록하고 당일 누적 절감액을 조회함.
    현재 stub 구현이며, PostgreSQL 연동 시 교체 필요.
    """

    def __init__(self, settings: Any = None) -> None:
        self._settings = settings
        self._cost_per_case = (
            settings.cost_per_case if settings else 28000
        )

    def record_auto_process(
        self,
        category: str,
        channel: str,
    ) -> dict:
        """자동 처리 1건을 기록하고 집계 결과를 반환함.

        Args:
            category: 질문 카테고리
            channel: 문의 채널

        Returns:
            saved_cost, auto_processed, total_saved_today, total_auto_today, cost_note
        """
        # TODO: PostgreSQL INSERT 및 집계 쿼리로 교체
        # 현재 stub: 단건 처리 결과만 반환
        saved_cost = self._cost_per_case
        auto_processed = 1

        logger.info(
            "비용 집계 기록 (stub)",
            category=category,
            channel=channel,
            saved_cost=saved_cost,
        )

        return {
            "saved_cost": saved_cost,
            "auto_processed": auto_processed,
            "total_saved_today": saved_cost,  # stub: 단건만 반영
            "total_auto_today": 1,
            "cost_note": f"자동 처리 1건 절감액: {saved_cost:,}원 (상담원 1건 처리 비용 기준)",
        }

    def get_daily_summary(self) -> dict:
        """당일 처리 현황 및 절감 비용 조회.

        Returns:
            당일 집계 데이터
        """
        # TODO: PostgreSQL 집계 쿼리로 교체
        raise NotImplementedError("PostgreSQL 연동 후 구현 필요")

    def get_monthly_summary(self, year: int, month: int) -> dict:
        """월별 집계 보고서 조회.

        Returns:
            월별 집계 데이터
        """
        # TODO: PostgreSQL 집계 쿼리로 교체
        raise NotImplementedError("PostgreSQL 연동 후 구현 필요")


class MockCostTracker(CostTracker):
    """Mock 비용 집계 구현.

    DSL Node 7의 프리셋 전략을 재현함.
    """

    PRESETS = {
        "default": {
            "saved_cost": 28000,
            "auto_processed": 1,
            "total_saved_today": 1960000,
            "total_auto_today": 70,
            "cost_note": "자동 처리 1건 절감액: 28,000원 (상담원 1건 처리 비용 기준)",
        },
        "empty": {
            "saved_cost": 0,
            "auto_processed": 0,
            "total_saved_today": 0,
            "total_auto_today": 0,
            "cost_note": "",
        },
        "error": {
            "saved_cost": 0,
            "auto_processed": 0,
            "total_saved_today": 0,
            "total_auto_today": 0,
            "cost_note": "",
        },
        "timeout": {
            "saved_cost": 0,
            "auto_processed": 0,
            "total_saved_today": 0,
            "total_auto_today": 0,
            "cost_note": "",
        },
    }

    def __init__(
        self,
        preset: str = "default",
        override: str = "",
    ) -> None:
        super().__init__(settings=None)
        self._preset = preset
        self._override = override

    def record_auto_process(
        self,
        category: str,
        channel: str,
    ) -> dict:
        """Mock 비용 집계 - 프리셋 전략."""
        if self._override and self._override.strip():
            try:
                result = json.loads(self._override)
                return {
                    "saved_cost": result.get("saved_cost", 0),
                    "auto_processed": result.get("auto_processed", 0),
                    "total_saved_today": result.get("total_saved_today", 0),
                    "total_auto_today": result.get("total_auto_today", 0),
                    "cost_note": result.get("cost_note", ""),
                }
            except json.JSONDecodeError:
                pass

        preset_data = self.PRESETS.get(self._preset, self.PRESETS["default"])
        return {
            "saved_cost": preset_data["saved_cost"],
            "auto_processed": preset_data["auto_processed"],
            "total_saved_today": preset_data["total_saved_today"],
            "total_auto_today": preset_data["total_auto_today"],
            "cost_note": preset_data["cost_note"],
        }

    def get_daily_summary(self) -> dict:
        """Mock 당일 집계."""
        return {
            "total_inquiries": 100,
            "auto_processed": 70,
            "auto_rate": 70.0,
            "escalated": 30,
            "total_saved_today": 1960000,
            "avg_response_ms": 3500,
            "alert_triggered": False,
        }

    def get_monthly_summary(self, year: int, month: int) -> dict:
        """Mock 월별 집계."""
        return {
            "year": year,
            "month": month,
            "total_inquiries": 3000,
            "auto_processed": 2100,
            "auto_rate": 70.0,
            "total_saved": 58800000,
            "avg_response_ms": 3500,
        }
