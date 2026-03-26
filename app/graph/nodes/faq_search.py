"""Node 4: FAQ 검색 + 관련도 평가.

FAQ 지식베이스에서 의미 검색 후 관련도 평가를 수행함.
90점 미만 시 질문을 수정하여 재검색 (최대 3회).
DSL Node 4에 대응. Mock/Real 전환 가능.
"""

from __future__ import annotations

import json

import structlog

from app.config.settings import get_settings
from app.graph.state import AgentState
from app.tools.faq_kb import FAQKnowledgeBase, MockFAQKnowledgeBase

logger = structlog.get_logger()


def _evaluate_relevance(
    query: str,
    results: list[dict],
    top_score: float,
) -> float:
    """검색 결과 관련도 평가 (0-100).

    실제 구현에서는 LLM 평가 노드로 대체 가능.
    """
    if not results or top_score == 0:
        return 0.0
    score = top_score
    if len(results) > 1:
        score = min(100.0, score + 5.0)
    return score


def _refine_query(original_query: str, attempt: int) -> str:
    """질문 프롬프트 수정. 실제 구현에서는 LLM 재작성 노드로 대체 가능."""
    refinements = ["구체적으로", "자세히 알려주세요", "단계별로"]
    idx = min(attempt - 1, len(refinements) - 1)
    return original_query + " " + refinements[idx]


def search_faq(state: AgentState) -> AgentState:
    """FAQ 검색 + 관련도 평가 루프를 실행함.

    최대 max_search_attempts 회 반복하며, 관련도 90점 이상이면 즉시 반환함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        faq_results, top_score, search_attempts, evaluation_log 업데이트된 상태
    """
    settings = get_settings()
    query = state.get("query", "")
    category = state.get("category", "기타")
    max_attempts = settings.max_search_attempts
    relevance_threshold = settings.faq_relevance_threshold

    # Mock/Real 전환
    if settings.use_mock:
        mock_preset = state.get("mock_preset", "default")
        mock_override = state.get("mock_override", "")
        kb: FAQKnowledgeBase = MockFAQKnowledgeBase(
            preset=mock_preset,
            override=mock_override,
        )
    else:
        kb = FAQKnowledgeBase(settings=settings)

    logger.info(
        "FAQ 검색 시작",
        query=query[:50],
        category=category,
        use_mock=settings.use_mock,
    )

    current_query = query
    attempts_log: list[dict] = []
    best_result: dict | None = None
    best_score: float = 0.0
    attempt = 0

    for attempt in range(1, max_attempts + 1):
        sr = kb.search(current_query, category)
        results = sr.get("results", [])
        top_score = sr.get("top_score", 0.0)
        count = sr.get("count", 0)

        relevance = _evaluate_relevance(current_query, results, top_score)

        attempts_log.append({
            "attempt": attempt,
            "query": current_query,
            "relevance": relevance,
            "top_score": top_score,
            "count": count,
        })

        if relevance > best_score:
            best_result = sr
            best_score = relevance

        logger.info(
            "FAQ 검색 시도",
            attempt=attempt,
            relevance=relevance,
            top_score=top_score,
            count=count,
        )

        if relevance >= relevance_threshold:
            break

        if attempt < max_attempts:
            current_query = _refine_query(query, attempt)

    final = best_result if best_result else sr
    final_results = final.get("results", [])

    return {
        "faq_results": json.dumps(final_results, ensure_ascii=False)
        if final_results
        else "[]",
        "top_score": final.get("top_score", 0.0),
        "faq_count": final.get("count", 0),
        "search_attempts": attempt,
        "evaluation_log": json.dumps(attempts_log, ensure_ascii=False),
    }
