"""Node 7: 비용 절감 집계 단위 테스트."""

import pytest

from app.graph.nodes.cost_agg import aggregate_cost


class TestAggregateCost:
    """비용 집계 노드 테스트."""

    def test_default_preset_cost(self):
        """기본 프리셋: 28,000원/건 절감."""
        state = {
            "category": "제품사용",
            "inquiry_channel": "웹채팅",
            "mock_preset": "default",
            "mock_override": "",
        }
        result = aggregate_cost(state)
        assert result["saved_cost"] == 28000
        assert result["auto_processed"] == 1
        assert result["total_saved_today"] == 1960000
        assert result["total_auto_today"] == 70
        assert "28,000" in result["cost_note"]

    def test_empty_preset(self):
        """empty 프리셋: 집계 데이터 없음."""
        state = {
            "category": "제품사용",
            "inquiry_channel": "웹채팅",
            "mock_preset": "empty",
            "mock_override": "",
        }
        result = aggregate_cost(state)
        assert result["saved_cost"] == 0
        assert result["auto_processed"] == 0
        assert result["cost_note"] == ""

    def test_error_preset(self):
        """error 프리셋: 집계 데이터 없음."""
        state = {
            "category": "제품사용",
            "inquiry_channel": "웹채팅",
            "mock_preset": "error",
            "mock_override": "",
        }
        result = aggregate_cost(state)
        assert result["saved_cost"] == 0

    def test_timeout_preset(self):
        """timeout 프리셋: 집계 데이터 없음."""
        state = {
            "category": "제품사용",
            "inquiry_channel": "웹채팅",
            "mock_preset": "timeout",
            "mock_override": "",
        }
        result = aggregate_cost(state)
        assert result["saved_cost"] == 0

    def test_mock_override(self):
        """오버라이드 JSON으로 커스텀 집계."""
        import json
        override = json.dumps({
            "saved_cost": 50000,
            "auto_processed": 2,
            "total_saved_today": 100000,
            "total_auto_today": 4,
            "cost_note": "커스텀 비용",
        })
        state = {
            "category": "제품사용",
            "inquiry_channel": "웹채팅",
            "mock_preset": "default",
            "mock_override": override,
        }
        result = aggregate_cost(state)
        assert result["saved_cost"] == 50000
        assert result["auto_processed"] == 2
