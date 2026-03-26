"""워크플로우 통합 테스트.

자동 답변 및 이관 워크플로우의 E2E 실행을 검증함.
Mock 모드에서 실행되므로 외부 API 의존성 없음.
"""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest


class TestAutoAnswerWorkflow:
    """자동 답변 워크플로우 E2E 테스트."""

    def test_full_auto_workflow(self):
        """Node 1~8 전체 실행: 자동 답변 경로."""
        # LLM 호출을 Mock으로 대체
        mock_response = MagicMock()
        mock_response.content = '{"complexity": "low", "category": "제품사용"}'

        mock_answer_response = MagicMock()
        mock_answer_response.content = "전원 버튼을 3초간 누르시면 LED가 점멸합니다."

        with patch("app.graph.nodes.classifier.ChatGroq") as mock_classifier_llm, \
             patch("app.graph.nodes.answer_gen.ChatGroq") as mock_answer_llm:

            mock_classifier_llm.return_value.invoke.return_value = mock_response
            mock_answer_llm.return_value.invoke.return_value = mock_answer_response

            from app.graph.workflow import build_workflow

            workflow = build_workflow()
            result = workflow.invoke({
                "query": "충전 케이블 연결 방법을 알려주세요",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            assert result["process_type"] == "auto"
            assert result["complexity"] == "low"
            assert result["category"] == "제품사용"
            assert result["generated_answer"] == "전원 버튼을 3초간 누르시면 LED가 점멸합니다."
            assert result["saved_cost"] == 28000
            assert "auto_answer_text" in result


class TestEscalationWorkflow:
    """이관 워크플로우 E2E 테스트."""

    def test_full_escalation_workflow(self):
        """Node 1~5, 9~10 전체 실행: 이관 경로."""
        mock_response = MagicMock()
        mock_response.content = '{"complexity": "high", "category": "환불"}'

        with patch("app.graph.nodes.classifier.ChatGroq") as mock_llm:
            mock_llm.return_value.invoke.return_value = mock_response

            from app.graph.workflow import build_workflow

            workflow = build_workflow()
            result = workflow.invoke({
                "query": "결제가 두 번 되었는데 환불해주세요",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            assert result["process_type"] == "escalation"
            assert result["complexity"] == "high"
            assert result["agent_id"] == "AGT-042"
            assert result["agent_name"] == "김상담"
            assert result["priority"] == "high"
            # high complexity로 대기 시간 2분 단축
            assert result["estimated_wait_minutes"] == 3
            assert "escalation_message" in result
            assert "전문 상담원" in result["escalation_message"]


class TestErrorHandling:
    """에러 핸들링 통합 테스트."""

    def test_llm_failure_fallback_to_escalation(self):
        """LLM 실패 시 상담원 이관으로 폴백."""
        with patch("app.graph.nodes.classifier.ChatGroq") as mock_llm:
            mock_llm.return_value.invoke.side_effect = Exception("API Error")

            from app.graph.workflow import build_workflow

            workflow = build_workflow()
            result = workflow.invoke({
                "query": "테스트 질문",
                "inquiry_channel": "웹채팅",
                "mock_preset": "default",
                "mock_override": "",
            })

            # LLM 실패 시 기본값(high, 기타)으로 폴백 → 이관 경로
            assert result["complexity"] == "high"
            assert result["category"] == "기타"

    def test_error_preset_agent_assign(self):
        """상담원 배정 시스템 에러 시 에러 안내."""
        mock_response = MagicMock()
        mock_response.content = '{"complexity": "high", "category": "환불"}'

        with patch("app.graph.nodes.classifier.ChatGroq") as mock_llm:
            mock_llm.return_value.invoke.return_value = mock_response

            from app.graph.workflow import build_workflow

            workflow = build_workflow()
            result = workflow.invoke({
                "query": "환불 문의",
                "inquiry_channel": "웹채팅",
                "mock_preset": "error",
                "mock_override": "",
            })

            assert result["assign_status"] == "system_error"
            assert "오류" in result["escalation_message"]
