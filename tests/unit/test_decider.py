"""Node 5: 자동처리 가능 여부 판단 단위 테스트."""

import pytest

from app.graph.nodes.decider import decide_auto_process, route_decision


class TestDecideAutoProcess:
    """자동처리 판단 노드 테스트."""

    def test_auto_when_high_score_and_low_complexity(self):
        """점수 75 이상 AND 복잡도 low → 자동처리."""
        state = {"top_score": 88.0, "complexity": "low"}
        result = decide_auto_process(state)
        assert result["auto_processable"] is True
        assert result["process_type"] == "auto"

    def test_auto_when_score_equals_threshold(self):
        """점수가 정확히 임계값(75)일 때 자동처리."""
        state = {"top_score": 75.0, "complexity": "low"}
        result = decide_auto_process(state)
        assert result["auto_processable"] is True

    def test_escalation_when_low_score(self):
        """점수 75 미만 → 상담원 이관."""
        state = {"top_score": 60.0, "complexity": "low"}
        result = decide_auto_process(state)
        assert result["auto_processable"] is False
        assert result["process_type"] == "escalation"

    def test_escalation_when_high_complexity(self):
        """복잡도 high → 상담원 이관 (점수 무관)."""
        state = {"top_score": 95.0, "complexity": "high"}
        result = decide_auto_process(state)
        assert result["auto_processable"] is False
        assert result["process_type"] == "escalation"

    def test_escalation_when_low_score_and_high_complexity(self):
        """점수 낮고 복잡도 높음 → 상담원 이관."""
        state = {"top_score": 30.0, "complexity": "high"}
        result = decide_auto_process(state)
        assert result["auto_processable"] is False

    def test_default_values(self):
        """기본값(점수 0, 복잡도 high) → 상담원 이관."""
        state = {}
        result = decide_auto_process(state)
        assert result["auto_processable"] is False


class TestRouteDecision:
    """라우팅 함수 테스트."""

    def test_route_auto(self):
        """자동처리 가능 시 auto 반환."""
        state = {"auto_processable": True}
        assert route_decision(state) == "auto"

    def test_route_escalation(self):
        """자동처리 불가 시 escalation 반환."""
        state = {"auto_processable": False}
        assert route_decision(state) == "escalation"

    def test_route_default_is_escalation(self):
        """기본값은 escalation."""
        state = {}
        assert route_decision(state) == "escalation"
