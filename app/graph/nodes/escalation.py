"""Node 10: 상담원 이관 안내.

상담원 이관 안내 메시지를 고객에게 전달함.
DSL Node 10 (상담원 이관 안내)에 대응.
"""

from __future__ import annotations

import structlog

from app.graph.state import AgentState

logger = structlog.get_logger()


def format_escalation(state: AgentState) -> AgentState:
    """상담원 이관 안내 메시지를 포맷팅함.

    DSL 템플릿:
      해당 문의는 전문 상담원의 도움이 필요합니다.
      상담원 연결까지 약 {{#9.estimated_wait_minutes#}}분 소요 예정입니다.
      대기 순서: {{#9.queue_position#}}번째
      잠시만 기다려 주시면 {{#9.agent_name#}} 상담원이 도와드리겠습니다.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        escalation_message 필드가 업데이트된 상태
    """
    estimated_wait = state.get("estimated_wait_minutes", 0)
    queue_position = state.get("queue_position", 0)
    agent_name = state.get("agent_name", "")
    assign_status = state.get("assign_status", "")

    if assign_status == "system_error":
        message = (
            "해당 문의는 전문 상담원의 도움이 필요합니다.\n"
            "현재 상담원 배정 시스템에 일시적 오류가 발생했습니다.\n"
            "잠시 후 다시 시도해 주시기 바랍니다."
        )
    elif assign_status == "no_agent_available":
        message = (
            "해당 문의는 전문 상담원의 도움이 필요합니다.\n"
            "현재 가용 상담원이 없습니다.\n"
            "잠시 후 다시 연결해 주시기 바랍니다."
        )
    else:
        message = (
            f"해당 문의는 전문 상담원의 도움이 필요합니다.\n"
            f"상담원 연결까지 약 {estimated_wait}분 소요 예정입니다.\n"
            f"대기 순서: {queue_position}번째\n"
            f"잠시만 기다려 주시면 {agent_name} 상담원이 도와드리겠습니다."
        )

    logger.info(
        "상담원 이관 안내 포맷 완료",
        assign_status=assign_status,
    )

    return {
        "escalation_message": message,
        "process_type": "escalation",
    }
