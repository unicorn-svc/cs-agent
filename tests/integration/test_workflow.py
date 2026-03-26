"""Integration tests for the complete workflow."""

import pytest
import asyncio

from app.graph.state import AgentState
from app.graph.workflow import create_workflow


@pytest.fixture
def workflow():
    """Create workflow for testing."""
    return create_workflow()


def test_auto_answer_workflow(workflow):
    """Test complete auto-answer workflow."""
    state = AgentState(
        query="충전 케이블 연결 방법을 알려주세요",
        inquiry_channel="웹채팅",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    assert result.get("auto_processable") is True
    assert result.get("saved_cost") > 0
    assert result.get("generated_answer") != ""


def test_escalation_workflow(workflow):
    """Test complete escalation workflow."""
    state = AgentState(
        query="환불 분쟁이 있습니다",
        inquiry_channel="전화",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    assert result.get("auto_processable") is False
    assert result.get("agent_id") != ""


def test_workflow_with_error_preset(workflow):
    """Test workflow with error preset."""
    state = AgentState(
        query="배송 현황을 확인하고 싶습니다",
        inquiry_channel="웹채팅",
        mock_preset="error",
    )

    result = workflow.invoke(state.model_dump())

    assert result.get("category") != ""
    assert result.get("complexity") != ""


def test_workflow_json_parsing(workflow):
    """Test JSON parsing in workflow."""
    state = AgentState(
        query="제품 설정 방법",
        inquiry_channel="카카오톡",
        mock_preset="default",
    )

    result = workflow.invoke(state.model_dump())

    assert result.get("complexity") in ("low", "high")
    assert result.get("category") != ""
