"""Node 9: 상담원 배정 단위 테스트."""

import pytest

from app.graph.nodes.agent_assign import assign_agent


class TestAssignAgent:
    """상담원 배정 노드 테스트."""

    def test_default_preset_normal_priority(self):
        """기본 프리셋 + low complexity: normal 우선순위."""
        state = {
            "category": "제품사용",
            "complexity": "low",
            "mock_preset": "default",
            "mock_override": "",
        }
        result = assign_agent(state)
        assert result["agent_id"] == "AGT-042"
        assert result["agent_name"] == "김상담"
        assert result["queue_position"] == 2
        assert result["estimated_wait_minutes"] == 5
        assert result["priority"] == "normal"
        assert result["assign_status"] == "queued"

    def test_high_complexity_priority_upgrade(self):
        """high complexity: priority 승격, 대기 시간 2분 단축."""
        state = {
            "category": "환불",
            "complexity": "high",
            "mock_preset": "default",
            "mock_override": "",
        }
        result = assign_agent(state)
        assert result["priority"] == "high"
        assert result["estimated_wait_minutes"] == 3  # 5 - 2 = 3

    def test_empty_preset(self):
        """empty 프리셋: 가용 상담원 없음."""
        state = {
            "category": "제품사용",
            "complexity": "high",
            "mock_preset": "empty",
            "mock_override": "",
        }
        result = assign_agent(state)
        assert result["agent_id"] == ""
        assert result["assign_status"] == "no_agent_available"

    def test_error_preset(self):
        """error 프리셋: 시스템 에러."""
        state = {
            "category": "제품사용",
            "complexity": "high",
            "mock_preset": "error",
            "mock_override": "",
        }
        result = assign_agent(state)
        assert result["assign_status"] == "system_error"

    def test_timeout_preset(self):
        """timeout 프리셋: 타임아웃."""
        state = {
            "category": "제품사용",
            "complexity": "low",
            "mock_preset": "timeout",
            "mock_override": "",
        }
        result = assign_agent(state)
        assert result["assign_status"] == "timeout"
