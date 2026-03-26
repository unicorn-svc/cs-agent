"""Unit tests for auto-process decision node."""

import pytest

from app.graph.state import AgentState
from app.graph.nodes.decider import decide_auto_process
from app.config.settings import get_settings

settings = get_settings()


def test_auto_process_when_score_high_and_low_complexity():
    """Test auto-process when score >= threshold and complexity is low."""
    state = AgentState(
        query="test",
        complexity="low",
        top_score=settings.faq_score_threshold + 5,
    )

    result = decide_auto_process(state)

    assert result["auto_processable"] is True


def test_no_auto_process_when_score_low():
    """Test no auto-process when score < threshold."""
    state = AgentState(
        query="test",
        complexity="low",
        top_score=settings.faq_score_threshold - 5,
    )

    result = decide_auto_process(state)

    assert result["auto_processable"] is False


def test_no_auto_process_when_high_complexity():
    """Test no auto-process when complexity is high."""
    state = AgentState(
        query="test",
        complexity="high",
        top_score=settings.faq_score_threshold + 5,
    )

    result = decide_auto_process(state)

    assert result["auto_processable"] is False


def test_no_auto_process_both_conditions_fail():
    """Test no auto-process when both conditions fail."""
    state = AgentState(
        query="test",
        complexity="high",
        top_score=settings.faq_score_threshold - 5,
    )

    result = decide_auto_process(state)

    assert result["auto_processable"] is False
