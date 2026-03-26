"""API 엔드포인트 통합 테스트.

FastAPI TestClient를 사용하여 API 엔드포인트를 검증함.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app


AUTH_HEADERS = {"X-API-Key": "test-api-key"}


@pytest.fixture
def client():
    """테스트 클라이언트 fixture."""
    return TestClient(app)


class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트."""

    def test_health_check(self, client):
        """GET /health 정상 응답."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"
        assert "timestamp" in data


class TestMetricsEndpoint:
    """메트릭 엔드포인트 테스트."""

    def test_prometheus_metrics(self, client):
        """GET /metrics Prometheus 형식 응답."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_daily_metrics_mock(self, client):
        """GET /v1/metrics/daily Mock 모드 응답."""
        response = client.get("/v1/metrics/daily", headers=AUTH_HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "date" in data
        assert "auto_rate" in data

    def test_monthly_metrics_mock(self, client):
        """GET /v1/metrics/monthly Mock 모드 응답."""
        response = client.get(
            "/v1/metrics/monthly?year=2026&month=3", headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 2026
        assert data["month"] == 3


class TestChatStreamEndpoint:
    """채팅 스트리밍 엔드포인트 테스트."""

    def test_invalid_channel_rejected(self, client):
        """잘못된 채널 값 422 반환."""
        response = client.post(
            "/v1/chat/stream",
            json={
                "query": "테스트",
                "inquiry_channel": "무선",
            },
        )
        assert response.status_code == 422

    def test_empty_query_rejected(self, client):
        """빈 질문 422 반환."""
        response = client.post(
            "/v1/chat/stream",
            json={
                "query": "",
                "inquiry_channel": "웹채팅",
            },
        )
        assert response.status_code == 422

    def test_chat_stream_auto_answer(self, client):
        """자동 답변 SSE 스트리밍 응답."""
        mock_classify = MagicMock()
        mock_classify.content = '{"complexity": "low", "category": "제품사용"}'

        mock_answer = MagicMock()
        mock_answer.content = "전원 버튼을 3초간 누르세요."

        with patch("app.graph.nodes.classifier.ChatGroq") as mock_cls, \
             patch("app.graph.nodes.answer_gen.ChatGroq") as mock_ans:

            mock_cls.return_value.invoke.return_value = mock_classify
            mock_ans.return_value.invoke.return_value = mock_answer

            response = client.post(
                "/v1/chat/stream",
                json={
                    "query": "충전 케이블 연결 방법을 알려주세요",
                    "inquiry_channel": "웹채팅",
                    "mock_preset": "default",
                },
                headers=AUTH_HEADERS,
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")
