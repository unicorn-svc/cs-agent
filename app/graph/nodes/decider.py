"""Node 5: Auto-processing decision logic."""

from typing import Any

from app.config.settings import get_settings
from app.core.logger import get_logger
from app.graph.state import AgentState
from app.monitoring.metrics import auto_processed_total, escalation_total

logger = get_logger(__name__)
settings = get_settings()


def decide_auto_process(state: AgentState) -> dict[str, Any]:
    """Decide whether auto-processing is possible based on score and complexity."""
    can_auto_process = (
        state.top_score >= settings.faq_score_threshold and state.complexity == "low"
    )

    logger.info(
        "Auto-process decision made",
        can_auto_process=can_auto_process,
        top_score=state.top_score,
        complexity=state.complexity,
        threshold=settings.faq_score_threshold,
    )

    category = state.category or "unknown"
    if can_auto_process:
        auto_processed_total.labels(category=category).inc()
    else:
        escalation_total.labels(category=category).inc()

    return {"auto_processable": can_auto_process}
