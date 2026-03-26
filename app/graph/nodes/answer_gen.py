"""Node 6: 자동 답변 생성 (LLM).

FAQ 검색 결과를 기반으로 고객에게 제공할 자동 답변을 생성함.
DSL Node 6 (자동 답변 생성)에 대응.
"""

from __future__ import annotations

import json

import structlog
from langchain_groq import ChatGroq

from app.config.settings import get_settings
from app.graph.state import AgentState

logger = structlog.get_logger()

SYSTEM_PROMPT_TEMPLATE = """당신은 비용 효율을 최우선으로 하는 고객센터 자동 응답 에이전트입니다.

## 행동 규칙
- 정중하고 간결한 존댓말을 사용하세요.
- 200자(한국어 기준) 이내, 약 2-3문장으로 핵심 답변만 제공하세요.
- 불필요한 안부 인사나 감사 표현을 하지 마세요.
- FAQ 검색 결과에 없는 내용은 추측하여 답변하지 마세요.
- 검색 결과의 내용을 바탕으로 고객 질문에 직접 답변하세요.

## FAQ 검색 결과
{faq_context}

## 검색 정보
- 검색 시도 횟수: {search_attempts}회
- 최고 관련도 점수: {top_score}점
{confidence_note}
"""


def _format_faq_context(faq_results_json: str) -> str:
    """FAQ 검색 결과 JSON을 마크다운 형식으로 변환함."""
    try:
        results = json.loads(faq_results_json)
        if not results:
            return "검색 결과 없음"

        lines = []
        for i, item in enumerate(results, 1):
            title = item.get("title", "")
            content = item.get("content", "")
            score = item.get("score", 0)
            lines.append(f"### 결과 {i}: {title} (관련도: {score}점)")
            lines.append(content)
            lines.append("")
        return "\n".join(lines)

    except (json.JSONDecodeError, TypeError):
        return faq_results_json


def generate_answer(state: AgentState) -> AgentState:
    """LLM을 사용하여 FAQ 기반 자동 답변을 생성함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        generated_answer 필드가 업데이트된 상태
    """
    settings = get_settings()
    query = state.get("query", "")
    faq_results = state.get("faq_results", "[]")
    search_attempts = state.get("search_attempts", 1)
    top_score = state.get("top_score", 0.0)

    logger.info(
        "자동 답변 생성 시작",
        query=query[:50],
        search_attempts=search_attempts,
        top_score=top_score,
    )

    # 신뢰도 낮은 경우 불확실성 표현 유도
    confidence_note = ""
    if top_score < 80:
        confidence_note = (
            "- 주의: 검색 결과의 관련도가 높지 않습니다. "
            "답변에 불확실성을 표현하세요."
        )

    faq_context = _format_faq_context(faq_results)

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        faq_context=faq_context,
        search_attempts=search_attempts,
        top_score=top_score,
        confidence_note=confidence_note,
    )

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            max_tokens=settings.groq_max_tokens,
            temperature=settings.groq_temperature,
        )

        messages = [
            ("system", system_prompt),
            ("human", query),
        ]

        response = llm.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)

        logger.info("자동 답변 생성 완료", answer_length=len(answer))

        return {"generated_answer": answer}

    except Exception as e:
        logger.error("자동 답변 생성 LLM 호출 실패", error=str(e))
        return {
            "generated_answer": "",
            "error": f"답변 생성 실패: {str(e)}",
            "auto_processable": False,
            "process_type": "escalation",
        }
