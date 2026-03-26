"""Node 4: FAQ search with relevance evaluation loop."""

import json
import time
from typing import Any

from app.core.logger import get_logger
from app.config.settings import get_settings
from app.graph.state import AgentState
from app.monitoring.metrics import faq_search_duration_seconds

logger = get_logger(__name__)
settings = get_settings()


def evaluate_relevance(query: str, results: list, top_score: float) -> float:
    """Evaluate relevance of search results (0-100)."""
    if not results or top_score == 0:
        return 0.0

    score = float(top_score)
    if len(results) > 1:
        score = min(100.0, score + 5.0)

    return score


def refine_query(query: str, attempt: int) -> str:
    """Refine question for re-search."""
    refinements = ["구체적으로", "자세히 알려주세요", "단계별로"]
    idx = min(attempt - 1, len(refinements) - 1)
    return query + " " + refinements[idx]


def search_faq_mock(query: str, category: str) -> dict[str, Any]:
    """Mock FAQ search - returns deterministic results based on hash."""
    variant = sum(ord(c) for c in query) % 3

    if variant == 0:
        return {
            "results": [
                {
                    "title": f"FAQ-{category}-001",
                    "content": "해당 제품의 사용 방법은 다음과 같습니다. 1) 전원 버튼을 3초간 누릅니다. 2) LED가 점멸하면 연결 준비 완료입니다. 3) 기기와 페어링하세요.",
                    "score": 88,
                },
                {
                    "title": f"FAQ-{category}-002",
                    "content": "추가 도움이 필요하시면 사용 설명서 12페이지를 참고해 주세요.",
                    "score": 76,
                },
            ],
            "top_score": 88,
            "count": 2,
        }
    elif variant == 1:
        return {"results": [], "top_score": 0, "count": 0}
    else:
        return {
            "results": [
                {
                    "title": "FAQ-일반-099",
                    "content": "죄송합니다. 관련 FAQ를 찾을 수 없습니다.",
                    "score": 35,
                }
            ],
            "top_score": 35,
            "count": 1,
        }


def search_faq(state: AgentState | dict) -> dict[str, Any]:
    """Search FAQ with relevance evaluation loop (max 3 attempts)."""
    try:
        if isinstance(state, dict):
            state = AgentState(**state)
        max_attempts = settings.max_search_attempts
        current_query = state.query
        attempts_log = []
        best_result = None
        best_score = 0.0
        search_start = time.monotonic()

        for attempt in range(1, max_attempts + 1):
            if state.mock_preset == "empty":
                sr = {"results": [], "top_score": 0, "count": 0}
            elif state.mock_override:
                sr = json.loads(state.mock_override)
            else:
                sr = search_faq_mock(current_query, state.category)
            results = sr["results"]
            top_score = sr["top_score"]
            relevance = evaluate_relevance(current_query, results, top_score)

            attempts_log.append({
                "attempt": attempt,
                "query": current_query,
                "relevance": relevance,
                "top_score": top_score,
                "count": sr["count"],
            })

            if relevance > best_score:
                best_result = sr
                best_score = relevance

            if relevance >= settings.faq_relevance_threshold:
                break

            if attempt < max_attempts:
                current_query = refine_query(state.query, attempt)

        final = best_result if best_result else sr
        result_json = json.dumps(final["results"], ensure_ascii=False) if final["results"] else "[]"

        search_elapsed = time.monotonic() - search_start
        faq_search_duration_seconds.observe(search_elapsed)

        logger.info(
            "FAQ search completed",
            attempts=attempt,
            top_score=final["top_score"],
            count=final["count"],
            elapsed_seconds=round(search_elapsed, 4),
        )

        return {
            "faq_results": result_json,
            "faq_count": final["count"],
            "top_score": final["top_score"],
            "search_attempts": attempt,
            "evaluation_log": json.dumps(attempts_log, ensure_ascii=False),
        }

    except Exception as e:
        logger.error("FAQ search failed", error=str(e))
        return {
            "faq_results": "[]",
            "top_score": 0.0,
            "search_attempts": 1,
            "evaluation_log": "[]",
        }
