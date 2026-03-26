"""Node 4: FAQ 검색 + 관련도 평가 단위 테스트."""

import json

import pytest

from app.graph.nodes.faq_search import search_faq


class TestSearchFaq:
    """FAQ 검색 노드 테스트."""

    def test_default_search_returns_results(self):
        """기본 검색 시 결과 반환 (해시 기반 변형에 따라 다름)."""
        state = {
            "query": "충전 케이블 연결 방법을 알려주세요",
            "category": "제품사용",
            "mock_preset": "default",
            "mock_override": "",
        }
        result = search_faq(state)

        assert "faq_results" in result
        assert "top_score" in result
        assert "search_attempts" in result
        assert "evaluation_log" in result
        assert result["search_attempts"] >= 1
        assert result["search_attempts"] <= 3

    def test_empty_preset_returns_no_results(self):
        """empty 프리셋: 결과 없음."""
        state = {
            "query": "테스트 질문",
            "category": "기타",
            "mock_preset": "empty",
            "mock_override": "",
        }
        result = search_faq(state)
        assert result["top_score"] == 0.0
        assert result["faq_count"] == 0

    def test_search_attempts_max_3(self):
        """재검색 최대 3회 제한."""
        state = {
            "query": "테스트 질문",
            "category": "기타",
            "mock_preset": "empty",
            "mock_override": "",
        }
        result = search_faq(state)
        assert result["search_attempts"] <= 3

    def test_evaluation_log_is_valid_json(self):
        """평가 로그가 유효한 JSON."""
        state = {
            "query": "충전 케이블 연결 방법을 알려주세요",
            "category": "제품사용",
            "mock_preset": "default",
            "mock_override": "",
        }
        result = search_faq(state)
        log = json.loads(result["evaluation_log"])
        assert isinstance(log, list)
        assert len(log) >= 1
        assert "attempt" in log[0]
        assert "relevance" in log[0]

    def test_high_score_stops_early(self):
        """관련도 90점 이상이면 재검색 중단."""
        # 오버라이드로 높은 점수 강제
        override = json.dumps({
            "results": [{"title": "FAQ-001", "content": "답변", "score": 95}],
            "top_score": 95.0,
            "count": 1,
        })
        state = {
            "query": "테스트",
            "category": "기타",
            "mock_preset": "default",
            "mock_override": override,
        }
        result = search_faq(state)
        assert result["search_attempts"] == 1
        assert result["top_score"] == 95.0
