"""Unit tests for agent assignment node."""

import pytest

from app.graph.state import AgentState
from app.graph.nodes.agent_assign import assign_agent


def test_assign_agent_default_preset():
    """Test agent assignment with default preset."""
    state = AgentState(
        query="test",
        complexity="low",
        category="제품사용",
        mock_preset="default",
    )

    result = assign_agent(state)

    assert result["agent_id"] == "AGT-042"
    assert result["agent_name"] == "김상담"
    assert result["queue_position"] > 0


def test_assign_agent_high_priority_on_high_complexity():
    """Test priority adjustment for high complexity."""
    state = AgentState(
        query="test",
        complexity="high",
        category="환불",
        mock_preset="default",
    )

    result = assign_agent(state)

    assert result["priority"] == "high"
    assert result["estimated_wait_minutes"] < 5  # Should be reduced


def test_assign_agent_empty_preset():
    """Test agent assignment with empty preset."""
    state = AgentState(
        query="test",
        complexity="low",
        category="배송",
        mock_preset="empty",
    )

    result = assign_agent(state)

    assert result["agent_id"] == ""
    assert result["agent_name"] == ""


def test_assign_agent_with_override():
    """Test agent assignment with override."""
    override = '{"agent_id": "AGT-999", "agent_name": "이상담"}'
    state = AgentState(
        query="test",
        complexity="low",
        category="배송",
        mock_preset="default",
        mock_override=override,
    )

    result = assign_agent(state)

    assert result["agent_id"] == "AGT-999"
    assert result["agent_name"] == "이상담"
