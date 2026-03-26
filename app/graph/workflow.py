"""LangGraph workflow assembly."""

from typing import Any

from langgraph.graph import StateGraph, START, END

from app.graph.state import AgentState
from app.graph.nodes.classifier import classify_question
from app.graph.nodes.json_parser import parse_json
from app.graph.nodes.faq_search import search_faq
from app.graph.nodes.decider import decide_auto_process
from app.graph.nodes.answer_gen import generate_answer
from app.graph.nodes.cost_agg import aggregate_cost
from app.graph.nodes.agent_assign import assign_agent
from app.core.logger import get_logger

logger = get_logger(__name__)


def create_workflow():
    """Create and compile the LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Node 1: Input Parser (implicit in API layer)
    # Node 2: Question Classification
    def node_classify(state: AgentState) -> dict[str, Any]:
        result = classify_question(state)
        return result

    # Node 3: JSON Parser
    def node_parse_json(state: AgentState) -> dict[str, Any]:
        return parse_json(state, state.llm_output)

    # Node 4: FAQ Search
    def node_faq_search(state: AgentState) -> dict[str, Any]:
        return search_faq(state)

    # Node 5: Auto-process Decision
    def node_decide(state: AgentState) -> dict[str, Any]:
        return decide_auto_process(state)

    # Node 6: Answer Generation
    def node_answer_gen(state: AgentState) -> dict[str, Any]:
        result = generate_answer(state)
        return result

    # Node 7: Cost Aggregation
    def node_cost_agg(state: AgentState) -> dict[str, Any]:
        return aggregate_cost(state)

    # Node 8: Auto Answer Output (implicit in API layer)
    # Node 9: Agent Assignment
    def node_agent_assign(state: AgentState) -> dict[str, Any]:
        return assign_agent(state)

    # Node 10: Escalation Output (implicit in API layer)

    # Add nodes
    workflow.add_node("classify", node_classify)
    workflow.add_node("parse_json", node_parse_json)
    workflow.add_node("faq_search", node_faq_search)
    workflow.add_node("decide", node_decide)
    workflow.add_node("answer_gen", node_answer_gen)
    workflow.add_node("cost_agg", node_cost_agg)
    workflow.add_node("agent_assign", node_agent_assign)

    # Add edges
    workflow.add_edge(START, "classify")
    workflow.add_edge("classify", "parse_json")
    workflow.add_edge("parse_json", "faq_search")
    workflow.add_edge("faq_search", "decide")

    # Conditional edge: auto_processable
    def should_auto_process(state: AgentState) -> str:
        return "answer_gen" if state.auto_processable else "agent_assign"

    workflow.add_conditional_edges("decide", should_auto_process)

    # Auto-process path
    workflow.add_edge("answer_gen", "cost_agg")
    workflow.add_edge("cost_agg", END)

    # Escalation path
    workflow.add_edge("agent_assign", END)

    # Compile workflow
    app = workflow.compile()
    logger.info("Workflow compiled successfully")
    return app
