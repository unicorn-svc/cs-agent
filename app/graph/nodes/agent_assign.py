"""Node 9: 상담원 배정.

복잡도/긴급도 기반 상담원 배정 우선순위 결정 및 대기열 등록.
DSL Node 9에 대응. Mock/Real 전환 가능.
"""

from __future__ import annotations

import structlog

from app.config.settings import get_settings
from app.graph.state import AgentState
from app.tools.agent_queue import AgentQueue, MockAgentQueue

logger = structlog.get_logger()


def assign_agent(state: AgentState) -> AgentState:
    """상담원을 배정하고 대기열에 등록함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        agent_id, agent_name, queue_position 등 배정 관련 필드 업데이트된 상태
    """
    settings = get_settings()
    category = state.get("category", "기타")
    complexity = state.get("complexity", "high")
    mock_preset = state.get("mock_preset", "default")
    mock_override = state.get("mock_override", "")

    logger.info(
        "상담원 배정 시작",
        category=category,
        complexity=complexity,
        use_mock=settings.use_mock,
    )

    try:
        if settings.use_mock:
            queue: AgentQueue = MockAgentQueue(
                preset=mock_preset,
                override=mock_override,
            )
        else:
            queue = AgentQueue(settings=settings)

        result = queue.assign(category=category, complexity=complexity)

        logger.info(
            "상담원 배정 완료",
            agent_id=result.get("agent_id", ""),
            status=result.get("status", ""),
            priority=result.get("priority", ""),
        )

        return {
            "agent_id": result.get("agent_id", ""),
            "agent_name": result.get("agent_name", ""),
            "queue_position": result.get("queue_position", 0),
            "estimated_wait_minutes": result.get("estimated_wait_minutes", 0),
            "priority": result.get("priority", ""),
            "assign_status": result.get("status", ""),
        }

    except Exception as e:
        logger.error("상담원 배정 실패", error=str(e))
        return {
            "agent_id": "",
            "agent_name": "",
            "queue_position": 0,
            "estimated_wait_minutes": 0,
            "priority": "",
            "assign_status": "system_error",
            "error": f"상담원 배정 실패: {str(e)}",
        }
