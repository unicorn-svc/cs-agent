"""LangGraph 워크플로우 그래프 조립.

DSL의 노드/엣지 구조를 LangGraph StateGraph로 매핑하여
전체 워크플로우를 조립함.

그래프 구조:
  START → classifier → json_parser → faq_search → decider
    → (auto) answer_gen → cost_agg → auto_output → END
    → (escalation) agent_assign → escalation → END
"""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.graph.nodes.agent_assign import assign_agent
from app.graph.nodes.answer_gen import generate_answer
from app.graph.nodes.auto_output import format_auto_answer
from app.graph.nodes.classifier import classify_question
from app.graph.nodes.cost_agg import aggregate_cost
from app.graph.nodes.decider import decide_auto_process, route_decision
from app.graph.nodes.escalation import format_escalation
from app.graph.nodes.faq_search import search_faq
from app.graph.nodes.json_parser import parse_classification
from app.graph.state import AgentState


def build_workflow() -> StateGraph:
    """워크플로우 그래프를 조립하여 반환함.

    Returns:
        컴파일된 LangGraph StateGraph
    """
    graph = StateGraph(AgentState)

    # 노드 등록
    graph.add_node("classifier", classify_question)
    graph.add_node("json_parser", parse_classification)
    graph.add_node("faq_search", search_faq)
    graph.add_node("decider", decide_auto_process)
    graph.add_node("answer_gen", generate_answer)
    graph.add_node("cost_agg", aggregate_cost)
    graph.add_node("auto_output", format_auto_answer)
    graph.add_node("agent_assign", assign_agent)
    graph.add_node("escalation", format_escalation)

    # 엣지 연결 (무조건)
    graph.set_entry_point("classifier")
    graph.add_edge("classifier", "json_parser")
    graph.add_edge("json_parser", "faq_search")
    graph.add_edge("faq_search", "decider")

    # 조건부 엣지 (Node 5: 자동처리 가능 여부)
    graph.add_conditional_edges(
        "decider",
        route_decision,
        {
            "auto": "answer_gen",
            "escalation": "agent_assign",
        },
    )

    # 자동 답변 경로
    graph.add_edge("answer_gen", "cost_agg")
    graph.add_edge("cost_agg", "auto_output")
    graph.add_edge("auto_output", END)

    # 상담원 이관 경로
    graph.add_edge("agent_assign", "escalation")
    graph.add_edge("escalation", END)

    return graph.compile()


# 싱글톤 인스턴스
_workflow_instance = None


def get_workflow() -> StateGraph:
    """워크플로우 싱글톤 인스턴스를 반환함."""
    global _workflow_instance
    if _workflow_instance is None:
        _workflow_instance = build_workflow()
    return _workflow_instance
