"""Node 7: Cost aggregation and tracking."""

import json
from typing import Any

from app.config.settings import get_settings
from app.core.logger import get_logger
from app.graph.state import AgentState

logger = get_logger(__name__)
settings = get_settings()


def aggregate_cost(state: AgentState) -> dict[str, Any]:
    """Calculate and aggregate cost savings for auto-handled inquiry."""
    try:
        # Parse mock preset and override
        presets = {
            "default": {
                "saved_cost": settings.cost_per_case,
                "auto_processed": 1,
                "total_saved_today": 1960000,
                "total_auto_today": 70,
                "cost_note": f"자동 처리 1건 절감액: {settings.cost_per_case:,}원 (상담원 1건 처리 비용 기준)",
            },
            "empty": {
                "saved_cost": 0,
                "auto_processed": 0,
                "total_saved_today": 0,
                "total_auto_today": 0,
                "cost_note": "",
                "_mock_note": "집계 데이터 없음",
            },
            "error": {
                "saved_cost": 0,
                "auto_processed": 0,
                "total_saved_today": 0,
                "total_auto_today": 0,
                "cost_note": "",
                "_mock_error": "집계 시스템 연결 실패",
            },
            "timeout": {
                "saved_cost": 0,
                "auto_processed": 0,
                "total_saved_today": 0,
                "total_auto_today": 0,
                "cost_note": "",
                "_mock_error": "집계 응답 시간 초과",
            },
        }

        if state.mock_override and state.mock_override.strip():
            try:
                result = json.loads(state.mock_override)
            except json.JSONDecodeError:
                result = presets.get("default", presets["default"])
        else:
            result = presets.get(state.mock_preset, presets["default"])

        result["category"] = state.category

        logger.info(
            "Cost aggregated",
            saved_cost=result.get("saved_cost"),
            total_saved_today=result.get("total_saved_today"),
        )

        return {
            "saved_cost": result.get("saved_cost", 0),
            "cost_note": result.get("cost_note", ""),
            "total_saved_today": result.get("total_saved_today", 0),
        }

    except Exception as e:
        logger.error("Cost aggregation failed", error=str(e))
        return {
            "saved_cost": 0,
            "cost_note": "",
            "total_saved_today": 0,
        }
