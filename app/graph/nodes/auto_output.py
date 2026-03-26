"""Node 8: 자동 답변 출력.

FAQ 기반 자동 답변을 고객에게 전달함.
DSL Node 8 (자동 답변)에 대응.
"""

from __future__ import annotations

import structlog

from app.graph.state import AgentState

logger = structlog.get_logger()


def format_auto_answer(state: AgentState) -> AgentState:
    """자동 답변 텍스트와 메타데이터를 포맷팅함.

    DSL 템플릿:
      {{#6.text#}}
      ---
      _[자동 답변] 절감 비용: {{#7.cost_note#}} | 검색 {{#4.search_attempts#}}회 시도_
      _[평가 로그] {{#4.evaluation_log#}}_

    Args:
        state: 현재 워크플로우 상태

    Returns:
        auto_answer_text 필드가 업데이트된 상태
    """
    generated_answer = state.get("generated_answer", "")
    cost_note = state.get("cost_note", "")
    search_attempts = state.get("search_attempts", 1)
    evaluation_log = state.get("evaluation_log", "")

    # 답변 텍스트 조립
    parts = [generated_answer]
    parts.append("\n---")
    parts.append(
        f"_[자동 답변] 절감 비용: {cost_note} | "
        f"검색 {search_attempts}회 시도_"
    )
    if evaluation_log:
        parts.append(f"_[평가 로그] {evaluation_log}_")

    auto_answer_text = "\n".join(parts)

    logger.info(
        "자동 답변 출력 포맷 완료",
        answer_length=len(auto_answer_text),
    )

    return {
        "auto_answer_text": auto_answer_text,
        "process_type": "auto",
    }
