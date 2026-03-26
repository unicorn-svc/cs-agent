"""상담원 대기열 관리 연동 도구.

복잡도/긴급도 기반 우선순위 산정 및 상담원 업무 시스템 API 호출.
DSL Node 9의 상담원 배정 대응. Mock/Real 전환 가능.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

logger = structlog.get_logger()


class AgentQueue:
    """Real 상담원 대기열 관리 (외부 시스템 연동).

    상담원 업무 시스템 REST API를 호출하여 대기열 등록 및 배정을 수행함.
    현재 stub 구현이며, 실제 시스템 연동 시 교체 필요.
    """

    def __init__(self, settings: Any = None) -> None:
        self._settings = settings
        self._api_url = (
            settings.agent_system_api_url if settings else "http://localhost:9000/api/v1"
        )

    def assign(
        self,
        category: str,
        complexity: str,
    ) -> dict:
        """상담원 배정 요청.

        Args:
            category: 질문 카테고리
            complexity: 질문 복잡도 ("low" | "high")

        Returns:
            agent_id, agent_name, queue_position, estimated_wait_minutes, priority, status
        """
        # TODO: httpx를 사용한 실제 REST API 호출로 교체
        # POST {api_url}/assignments
        # Body: {"category": category, "complexity": complexity}
        # 실제 시스템 미연동 시 기본 배정 응답 반환
        logger.info("상담원 배정 요청 (시뮬레이션)", category=category, complexity=complexity)
        priority = "high" if complexity == "high" else "normal"
        wait = 3 if priority == "high" else 5
        return {
            "agent_id": "AGT-042",
            "agent_name": "김상담",
            "queue_position": 2,
            "estimated_wait_minutes": wait,
            "priority": priority,
            "status": "queued",
        }


class MockAgentQueue(AgentQueue):
    """Mock 상담원 대기열 구현.

    DSL Node 9의 프리셋 전략을 재현함.
    """

    PRESETS = {
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
        },
        "error": {
            "agent_id": "",
            "agent_name": "",
            "queue_position": 0,
            "estimated_wait_minutes": 0,
            "priority": "",
            "status": "system_error",
        },
        "timeout": {
            "agent_id": "",
            "agent_name": "",
            "queue_position": 0,
            "estimated_wait_minutes": 0,
            "priority": "",
            "status": "timeout",
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

    def assign(
        self,
        category: str,
        complexity: str,
    ) -> dict:
        """Mock 상담원 배정 - 프리셋 전략."""
        if self._override and self._override.strip():
            try:
                result = json.loads(self._override)
                return self._apply_priority(result, complexity)
            except json.JSONDecodeError:
                pass

        preset_data = self.PRESETS.get(self._preset, self.PRESETS["default"]).copy()
        return self._apply_priority(preset_data, complexity)

    @staticmethod
    def _apply_priority(result: dict, complexity: str) -> dict:
        """복잡도에 따른 우선순위 조정."""
        if complexity == "high" and result.get("priority") == "normal":
            result["priority"] = "high"
            wait = result.get("estimated_wait_minutes", 0)
            if wait > 0:
                result["estimated_wait_minutes"] = max(1, wait - 2)

        return {
            "agent_id": result.get("agent_id", ""),
            "agent_name": result.get("agent_name", ""),
            "queue_position": result.get("queue_position", 0),
            "estimated_wait_minutes": result.get("estimated_wait_minutes", 0),
            "priority": result.get("priority", ""),
            "status": result.get("status", "queued"),
        }
