"""Unit tests for cost aggregation node."""

import pytest

from app.graph.state import AgentState
from app.graph.nodes.cost_agg import aggregate_cost
from app.config.settings import get_settings

settings = get_settings()


def test_aggregate_cost_default_preset():
    """Test cost aggregation with default preset."""
    state = AgentState(
        query="test",
        category="제품사용",
        mock_preset="default",
    )

    result = aggregate_cost(state)

    assert result["saved_cost"] == settings.cost_per_case
    assert result["cost_note"] != ""


def test_aggregate_cost_empty_preset():
    """Test cost aggregation with empty preset."""
    state = AgentState(
        query="test",
        category="배송",
        mock_preset="empty",
    )

    result = aggregate_cost(state)

    assert result["saved_cost"] == 0
    assert result["cost_note"] == ""


def test_aggregate_cost_error_preset():
    """Test cost aggregation with error preset."""
    state = AgentState(
        query="test",
        category="결제",
        mock_preset="error",
    )

    result = aggregate_cost(state)

    assert result["saved_cost"] == 0
    assert result["total_saved_today"] == 0


def test_aggregate_cost_with_override():
    """Test cost aggregation with override."""
    override = '{"saved_cost": 50000, "total_saved_today": 2000000}'
    state = AgentState(
        query="test",
        category="환불",
        mock_preset="default",
        mock_override=override,
    )

    result = aggregate_cost(state)

    assert result["saved_cost"] == 50000
