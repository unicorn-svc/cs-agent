"""Node 7: 비용 절감 집계.

자동 처리 1건 완료 시 절감 비용을 계산하고 누적 집계에 반영함.
DSL Node 7에 대응. Mock/Real 전환 가능.
"""

from __future__ import annotations

import structlog

from app.config.settings import get_settings
from app.graph.state import AgentState
from app.tools.cost_tracker import CostTracker, MockCostTracker

logger = structlog.get_logger()


def aggregate_cost(state: AgentState) -> AgentState:
    """비용 절감 집계를 수행함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        saved_cost, cost_note, total_saved_today 등 비용 관련 필드 업데이트된 상태
    """
    settings = get_settings()
    category = state.get("category", "기타")
    channel = state.get("inquiry_channel", "웹채팅")
    mock_preset = state.get("mock_preset", "default")
    mock_override = state.get("mock_override", "")

    logger.info(
        "비용 집계 시작",
        category=category,
        use_mock=settings.use_mock,
    )

    try:
        if settings.use_mock:
            tracker: CostTracker = MockCostTracker(
                preset=mock_preset,
                override=mock_override,
            )
        else:
            tracker = CostTracker(settings=settings)

        result = tracker.record_auto_process(category=category, channel=channel)

        logger.info(
            "비용 집계 완료",
            saved_cost=result.get("saved_cost", 0),
            total_saved_today=result.get("total_saved_today", 0),
        )

        return {
            "saved_cost": result.get("saved_cost", 0),
            "auto_processed": result.get("auto_processed", 0),
            "total_saved_today": result.get("total_saved_today", 0),
            "total_auto_today": result.get("total_auto_today", 0),
            "cost_note": result.get("cost_note", ""),
        }

    except Exception as e:
        logger.error("비용 집계 실패", error=str(e))
        # 집계 실패해도 답변 전달은 계속 진행
        return {
            "saved_cost": 0,
            "auto_processed": 0,
            "total_saved_today": 0,
            "total_auto_today": 0,
            "cost_note": "",
            "error": f"비용 집계 실패: {str(e)}",
        }
