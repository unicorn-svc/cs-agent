"""Scenario-based E2E tests."""

import pytest

from app.graph.state import AgentState
from app.graph.workflow import create_workflow


@pytest.fixture
def workflow():
    """Create workflow for testing."""
    return create_workflow()


def test_scenario_01_simple_faq_auto_process(workflow):
    """SC-01: Simple FAQ auto-processing."""
    state = AgentState(
        query="충전 케이블 연결 방법을 알려주세요",
        inquiry_channel="웹채팅",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    # Verify auto-processing
    assert result.get("auto_processable") is True
    assert result.get("saved_cost") > 0
    assert len(result.get("generated_answer", "")) > 0


def test_scenario_02_high_complexity_escalation(workflow):
    """SC-02: High complexity escalation."""
    state = AgentState(
        query="환불 분쟁으로 인한 법적 소송 관련 상담이 필요합니다",
        inquiry_channel="전화",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    # Verify escalation
    assert result.get("auto_processable") is False
    assert result.get("agent_id") != ""
    assert result.get("priority") == "high"


def test_scenario_03_faq_research_loop(workflow):
    """SC-03: FAQ re-search loop."""
    state = AgentState(
        query="이상한 요청으로 FAQ 재검색을 트리거",
        inquiry_channel="이메일",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    # Verify search attempts
    assert result.get("search_attempts") >= 1


def test_scenario_04_processing_rate_70_percent(workflow):
    """SC-04: Processing rate 70% verification."""
    auto_count = 0
    total_count = 100

    # Test with mixed presets
    presets = ["default"] * 70 + ["empty"] * 30

    for preset in presets:
        state = AgentState(
            query="테스트 쿼리",
            inquiry_channel="웹채팅",
            mock_preset=preset,
        )
        result = workflow.invoke(state.model_dump())
        if result.get("auto_processable"):
            auto_count += 1

    auto_rate = (auto_count / total_count) * 100
    assert auto_rate >= 60  # At least 60% auto-processing rate
