"""Prometheus 메트릭 수집 모듈.

처리율, 응답 시간, 에러율 등 운영 메트릭을 수집하여
Prometheus 형식으로 노출함.
"""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, generate_latest

# 처리 건수 카운터
REQUESTS_TOTAL = Counter(
    "cs_agent_requests_total",
    "Total number of chat requests",
    ["process_type", "category", "channel"],
)

# 응답 시간 히스토그램
RESPONSE_TIME = Histogram(
    "cs_agent_response_seconds",
    "Response time in seconds",
    ["process_type"],
    buckets=[0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 20.0, 30.0],
)

# 절감 비용 카운터
SAVED_COST_TOTAL = Counter(
    "cs_agent_saved_cost_total",
    "Total saved cost in KRW",
)

# 자동 처리율 게이지
AUTO_RATE = Gauge(
    "cs_agent_auto_rate",
    "Current auto processing rate percentage",
)

# 에러 카운터
ERRORS_TOTAL = Counter(
    "cs_agent_errors_total",
    "Total number of errors",
    ["error_type"],
)

# FAQ 검색 시도 히스토그램
SEARCH_ATTEMPTS = Histogram(
    "cs_agent_search_attempts",
    "Number of FAQ search attempts per request",
    buckets=[1, 2, 3],
)


def record_request(
    process_type: str,
    category: str,
    channel: str,
    elapsed_seconds: float,
    saved_cost: int = 0,
    search_attempts: int = 1,
) -> None:
    """요청 처리 결과를 메트릭에 기록함."""
    REQUESTS_TOTAL.labels(
        process_type=process_type,
        category=category,
        channel=channel,
    ).inc()

    RESPONSE_TIME.labels(process_type=process_type).observe(elapsed_seconds)

    if saved_cost > 0:
        SAVED_COST_TOTAL.inc(saved_cost)

    SEARCH_ATTEMPTS.observe(search_attempts)


def record_error(error_type: str) -> None:
    """에러를 메트릭에 기록함."""
    ERRORS_TOTAL.labels(error_type=error_type).inc()


def update_auto_rate(rate: float) -> None:
    """자동 처리율을 업데이트함."""
    AUTO_RATE.set(rate)


def get_metrics() -> bytes:
    """Prometheus 메트릭을 바이트 문자열로 반환함."""
    return generate_latest()
