"""Node 9: Agent assignment based on complexity and priority."""

import json
from typing import Any

from app.core.logger import get_logger
from app.graph.state import AgentState

logger = get_logger(__name__)


def assign_agent(state: AgentState) -> dict[str, Any]:
    """Assign agent based on complexity and create queue entry."""
    try:
        # Mock agent assignment with presets
        presets = {
            "default": {
                "agent_id": "AGT-042",
                "agent_name": "김상담",
                "queue_position": 2,
                "estimated_wait_minutes": 5,
                "priority": "normal",
                "status": "queued",
            },
            "empty": {
                "agent_id": "",
                "agent_name": "",
                "queue_position": 0,
                "estimated_wait_minutes": 0,
                "priority": "",
                "status": "no_agent_available",
                "_mock_note": "가용 상담원 없음",
            },
            "error": {
                "agent_id": "",
                "agent_name": "",
                "queue_position": 0,
                "estimated_wait_minutes": 0,
                "priority": "",
                "status": "system_error",
                "_mock_error": "상담원 배정 시스템 연결 실패",
            },
            "timeout": {
                "agent_id": "",
                "agent_name": "",
                "queue_position": 0,
                "estimated_wait_minutes": 0,
                "priority": "",
                "status": "timeout",
                "_mock_error": "배정 응답 시간 초과",
            },
        }

        if state.mock_override and state.mock_override.strip():
            try:
                result = json.loads(state.mock_override)
            except json.JSONDecodeError:
                result = presets.get("default", presets["default"])
        else:
            result = presets.get(state.mock_preset, presets["default"])

        # Adjust priority based on complexity
        if state.complexity == "high" and result.get("priority") == "normal":
            result["priority"] = "high"
            if result.get("estimated_wait_minutes", 0) > 0:
                result["estimated_wait_minutes"] = max(1, result["estimated_wait_minutes"] - 2)

        result["category"] = state.category
        result["complexity"] = state.complexity

        logger.info(
            "Agent assigned",
            agent_id=result.get("agent_id"),
            queue_position=result.get("queue_position"),
            priority=result.get("priority"),
        )

        return {
            "agent_id": result.get("agent_id", ""),
            "agent_name": result.get("agent_name", ""),
            "queue_position": result.get("queue_position", 0),
            "estimated_wait_minutes": result.get("estimated_wait_minutes", 0),
            "priority": result.get("priority", ""),
        }

    except Exception as e:
        logger.error("Agent assignment failed", error=str(e))
        return {
            "agent_id": "",
            "agent_name": "",
            "queue_position": 0,
            "estimated_wait_minutes": 0,
            "priority": "normal",
        }
