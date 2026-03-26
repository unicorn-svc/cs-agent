"""Node 3: JSON 파싱 단위 테스트."""

import pytest

from app.graph.nodes.json_parser import parse_classification


class TestParseClassification:
    """JSON 파싱 노드 테스트."""

    def test_parse_valid_json(self):
        """정상 JSON 파싱."""
        state = {"classification_raw": '{"complexity": "low", "category": "제품사용"}'}
        result = parse_classification(state)
        assert result["complexity"] == "low"
        assert result["category"] == "제품사용"

    def test_parse_json_with_extra_text(self):
        """부가 텍스트가 포함된 JSON 추출."""
        state = {
            "classification_raw": '분류 결과입니다: {"complexity": "high", "category": "환불"} 입니다.'
        }
        result = parse_classification(state)
        assert result["complexity"] == "high"
        assert result["category"] == "환불"

    def test_parse_invalid_json_returns_default(self):
        """파싱 실패 시 기본값 반환."""
        state = {"classification_raw": "이것은 JSON이 아닙니다"}
        result = parse_classification(state)
        assert result["complexity"] == "high"
        assert result["category"] == "기타"

    def test_parse_empty_string(self):
        """빈 문자열 시 기본값 반환."""
        state = {"classification_raw": ""}
        result = parse_classification(state)
        assert result["complexity"] == "high"
        assert result["category"] == "기타"

    def test_parse_missing_field_uses_default(self):
        """필드 누락 시 기본값 사용."""
        state = {"classification_raw": '{"complexity": "low"}'}
        result = parse_classification(state)
        assert result["complexity"] == "low"
        assert result["category"] == "기타"

    def test_parse_invalid_complexity_defaults_to_high(self):
        """잘못된 complexity 값은 high로 변환."""
        state = {"classification_raw": '{"complexity": "medium", "category": "배송"}'}
        result = parse_classification(state)
        assert result["complexity"] == "high"
        assert result["category"] == "배송"

    def test_parse_no_classification_raw_in_state(self):
        """상태에 classification_raw 없을 때 기본값 반환."""
        state = {}
        result = parse_classification(state)
        assert result["complexity"] == "high"
        assert result["category"] == "기타"
