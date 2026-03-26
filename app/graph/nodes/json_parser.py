"""Node 3: JSON parsing of LLM classification output."""

import json
from typing import Any

from app.core.logger import get_logger
from app.graph.state import AgentState
from app.monitoring.metrics import classification_total

logger = get_logger(__name__)


def parse_json(state: AgentState, llm_output: str) -> dict[str, Any]:
    """Parse LLM classification output from JSON format."""
    try:
        text = llm_output.strip()
        start = text.find("{")
        end = text.rfind("}") + 1

        if start >= 0 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {}

        complexity = result.get("complexity", "high")
        category = result.get("category", "기타")

        if complexity not in ("low", "high"):
            complexity = "high"

        logger.info("JSON parsed", complexity=complexity, category=category)
        classification_total.labels(complexity=complexity, category=category).inc()

        return {
            "complexity": complexity,
            "category": category,
        }

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("JSON parsing failed, using default values", error=str(e))
        return {
            "complexity": "high",
            "category": "기타",
        }
