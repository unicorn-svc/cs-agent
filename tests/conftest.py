"""테스트 공통 fixture 정의."""

from __future__ import annotations

import os

import pytest

# 테스트 환경에서는 Mock 모드 강제
os.environ.setdefault("USE_MOCK", "true")
os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ.setdefault("API_KEY", "test-api-key")


@pytest.fixture
def default_state() -> dict:
    """기본 워크플로우 상태 fixture."""
    return {
        "query": "충전 케이블 연결 방법을 알려주세요",
        "inquiry_channel": "웹채팅",
        "mock_preset": "default",
        "mock_override": "",
    }


@pytest.fixture
def high_complexity_state() -> dict:
    """고복잡도 워크플로우 상태 fixture."""
    return {
        "query": "결제가 두 번 되었는데 환불해주세요",
        "inquiry_channel": "웹채팅",
        "mock_preset": "default",
        "mock_override": "",
        "complexity": "high",
        "category": "환불",
    }


@pytest.fixture
def classified_low_state() -> dict:
    """분류 완료된 저복잡도 상태 fixture."""
    return {
        "query": "충전 케이블 연결 방법을 알려주세요",
        "inquiry_channel": "웹채팅",
        "mock_preset": "default",
        "mock_override": "",
        "complexity": "low",
        "category": "제품사용",
    }


@pytest.fixture
def faq_searched_state() -> dict:
    """FAQ 검색 완료된 상태 fixture."""
    return {
        "query": "충전 케이블 연결 방법을 알려주세요",
        "inquiry_channel": "웹채팅",
        "mock_preset": "default",
        "mock_override": "",
        "complexity": "low",
        "category": "제품사용",
        "faq_results": '[{"title": "FAQ-제품사용-001", "content": "전원 버튼을 3초간 누르세요.", "score": 88}]',
        "top_score": 88.0,
        "faq_count": 1,
        "search_attempts": 1,
        "evaluation_log": '[{"attempt": 1, "query": "충전 케이블 연결 방법", "relevance": 88, "top_score": 88, "count": 1}]',
    }
