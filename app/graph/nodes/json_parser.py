"""Node 3: JSON 파싱.

LLM 분류 결과 JSON을 파싱하여 complexity, category 변수로 분리함.
DSL Node 3 (JSON 파싱)에 대응.
"""

from __future__ import annotations

import json

import structlog

from app.graph.state import AgentState

logger = structlog.get_logger()


def parse_classification(state: AgentState) -> AgentState:
    """LLM 출력에서 JSON을 추출하여 분류 결과를 파싱함.

    JSON 부분만 추출하여 파싱하며, 실패 시 기본값(high, 기타)을 반환함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        complexity, category 필드가 업데이트된 상태
    """
    raw = state.get("classification_raw", "")

    try:
        text = raw.strip()
        start = text.find("{")
        end = text.rfind("}") + 1

        if start >= 0 and end > start:
            result = json.loads(text[start:end])
        else:
            result = {}

        complexity = result.get("complexity", "high")
        category = result.get("category", "기타")

        # complexity 값 검증
        if complexity not in ("low", "high"):
            complexity = "high"

        logger.info(
            "JSON 파싱 완료",
            complexity=complexity,
            category=category,
        )

        return {
            "complexity": complexity,
            "category": category,
        }

    except (json.JSONDecodeError, Exception) as e:
        logger.warning("JSON 파싱 실패, 기본값 사용", error=str(e), raw=raw[:100])
        return {
            "complexity": "high",
            "category": "기타",
        }
