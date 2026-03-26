"""시나리오 테스트 (E2E).

scenario.md 기반 정상/예외 케이스 검증.
Mock 모드에서 실행.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest


class TestNormalScenarios:
    """정상 케이스 시나리오."""

    def test_sc01_simple_faq_auto_process(self):
        """SC-01: 단순 FAQ 자동 처리.

        입력: query="충전 케이블 연결 방법", channel="웹채팅"
        기대: 자동 답변, saved_cost=28000 집계
        """
        mock_classify = MagicMock()
        mock_classify.content = '{"complexity": "low", "category": "제품사용"}'
        mock_answer = MagicMock()
        mock_answer.content = "전원 버튼을 3초간 누르시면 LED가 점멸합니다."

        with patch("app.graph.nodes.classifier.ChatGroq") as cls, \
             patch("app.graph.nodes.answer_gen.ChatGroq") as ans:
            cls.return_value.invoke.return_value = mock_classify
            ans.return_value.invoke.return_value = mock_answer

            from app.graph.workflow import build_workflow
            workflow = build_workflow()
            result = workflow.invoke({
                "query": "충전 케이블 연결 방법",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            assert result["process_type"] == "auto"
            assert result["saved_cost"] == 28000
            assert len(result.get("generated_answer", "")) <= 400  # 200자 이내 (바이트가 아닌 유니코드)

    def test_sc02_high_complexity_escalation(self):
        """SC-02: 고복잡도 이관.

        입력: query="환불 분쟁 건", complexity=high
        기대: 이관 안내, agent_id 배정
        """
        mock_classify = MagicMock()
        mock_classify.content = '{"complexity": "high", "category": "환불"}'

        with patch("app.graph.nodes.classifier.ChatGroq") as cls:
            cls.return_value.invoke.return_value = mock_classify

            from app.graph.workflow import build_workflow
            workflow = build_workflow()
            result = workflow.invoke({
                "query": "환불 분쟁 건",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            assert result["process_type"] == "escalation"
            assert result["agent_id"] == "AGT-042"
            assert result["priority"] == "high"


class TestExceptionScenarios:
    """예외 케이스 시나리오."""

    def test_sc_e03_llm_timeout_fallback(self):
        """SC-E03: Groq API 타임아웃 시 이관 폴백."""
        with patch("app.graph.nodes.classifier.ChatGroq") as cls:
            cls.return_value.invoke.side_effect = TimeoutError("Groq API timeout")

            from app.graph.workflow import build_workflow
            workflow = build_workflow()
            result = workflow.invoke({
                "query": "테스트 질문",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            # 타임아웃 시 기본값(high, 기타)으로 폴백
            assert result["complexity"] == "high"

    def test_sc_e04_agent_system_error(self):
        """SC-E04: 상담원 시스템 오류."""
        mock_classify = MagicMock()
        mock_classify.content = '{"complexity": "high", "category": "기타"}'

        with patch("app.graph.nodes.classifier.ChatGroq") as cls:
            cls.return_value.invoke.return_value = mock_classify

            from app.graph.workflow import build_workflow
            workflow = build_workflow()
            result = workflow.invoke({
                "query": "복잡한 문의",
                "inquiry_channel": "웹채팅",
                "mock_preset": "error",
                "mock_override": "",
            })

            assert result["assign_status"] == "system_error"
            assert "오류" in result["escalation_message"]
