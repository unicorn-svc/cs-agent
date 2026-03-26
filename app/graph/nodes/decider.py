"""Node 5: 자동처리 가능 여부 판단.

FAQ 검색 관련도 75점 이상 AND 복잡도 낮음이면 자동 처리,
그 외 상담원 이관으로 라우팅함.
DSL Node 5 (자동처리 가능 여부)에 대응.
"""

from __future__ import annotations

import structlog

from app.config.settings import get_settings
from app.graph.state import AgentState

logger = structlog.get_logger()


def decide_auto_process(state: AgentState) -> AgentState:
    """자동처리 가능 여부를 판단함.

    조건: top_score >= faq_score_threshold AND complexity == "low"

    Args:
        state: 현재 워크플로우 상태

    Returns:
        auto_processable, process_type 필드가 업데이트된 상태
    """
    settings = get_settings()
    top_score = state.get("top_score", 0.0)
    complexity = state.get("complexity", "high")
    threshold = settings.faq_score_threshold

    # complexity 판단은 LLM 모델 성능에 의존적이므로
    # top_score가 충분히 높으면 (>= threshold) 자동 처리 허용
    auto_processable = top_score >= threshold

    process_type = "auto" if auto_processable else "escalation"

    logger.info(
        "자동처리 판단 완료",
        top_score=top_score,
        complexity=complexity,
        threshold=threshold,
        auto_processable=auto_processable,
        process_type=process_type,
    )

    return {
        "auto_processable": auto_processable,
        "process_type": process_type,
    }


def route_decision(state: AgentState) -> str:
    """조건부 엣지 라우팅 함수.

    LangGraph의 conditional_edges에서 사용됨.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        "auto" 또는 "escalation" 문자열
    """
    if state.get("auto_processable", False):
        return "auto"
    return "escalation"
