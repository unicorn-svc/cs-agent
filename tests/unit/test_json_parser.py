"""Unit tests for JSON parser node."""

import pytest

from app.graph.state import AgentState
from app.graph.nodes.json_parser import parse_json


def test_parse_valid_json():
    """Test parsing valid JSON output."""
    state = AgentState(query="test")
    llm_output = '{"complexity": "low", "category": "제품사용"}'

    result = parse_json(state, llm_output)

    assert result["complexity"] == "low"
    assert result["category"] == "제품사용"


def test_parse_json_with_extra_text():
    """Test parsing JSON with extra text."""
    state = AgentState(query="test")
    llm_output = 'Some text before {"complexity": "high", "category": "배송"} some text after'

    result = parse_json(state, llm_output)

    assert result["complexity"] == "high"
    assert result["category"] == "배송"


def test_parse_invalid_json():
    """Test parsing invalid JSON returns defaults."""
    state = AgentState(query="test")
    llm_output = "Not a valid JSON at all"

    result = parse_json(state, llm_output)

    assert result["complexity"] == "high"
    assert result["category"] == "기타"


def test_parse_invalid_complexity():
    """Test parsing with invalid complexity value."""
    state = AgentState(query="test")
    llm_output = '{"complexity": "invalid", "category": "배송"}'

    result = parse_json(state, llm_output)

    assert result["complexity"] == "high"
    assert result["category"] == "배송"
