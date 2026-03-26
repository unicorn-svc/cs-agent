"""API 엔드포인트 정의.

FastAPI 라우터로 채팅 스트리밍, 메트릭, 헬스체크 엔드포인트를 제공함.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse

from app.api.schemas import (
    AutoAnswerMetadata,
    ChatRequest,
    DailyMetricsResponse,
    ErrorDetail,
    ErrorResponse,
    EscalationMetadata,
    HealthResponse,
    MonthlyMetricsResponse,
)
from app.config.settings import Settings, get_settings
from app.graph.workflow import get_workflow
from app.monitoring.metrics import get_metrics, record_error, record_request
from app.tools.cost_tracker import CostTracker, MockCostTracker

logger = structlog.get_logger()

router = APIRouter()


def _verify_api_key(request: Request) -> None:
    """API Key 인증 검증."""
    settings = get_settings()
    if not settings.api_key:
        return  # API Key 미설정 시 인증 건너뜀

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
    else:
        token = request.headers.get("X-API-Key", "")

    if token != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="UNAUTHORIZED",
                    message="API Key 인증에 실패했습니다.",
                )
            ).model_dump(),
        )


async def _stream_response(state: dict, elapsed_ms: int):
    """SSE 스트리밍 응답 생성 제너레이터."""
    process_type = state.get("process_type", "auto")

    if process_type == "auto":
        # 자동 답변: 토큰 단위 스트리밍
        answer = state.get("auto_answer_text", "") or state.get("generated_answer", "")
        # 토큰 단위로 분할 (문장 단위)
        sentences = answer.split(". ")
        for i, sentence in enumerate(sentences):
            content = sentence + (". " if i < len(sentences) - 1 else "")
            yield {
                "event": "message",
                "data": json.dumps(
                    {"type": "token", "content": content},
                    ensure_ascii=False,
                ),
            }

        # 메타데이터 이벤트
        metadata = AutoAnswerMetadata(
            process_type="auto",
            category=state.get("category", ""),
            complexity=state.get("complexity", ""),
            top_score=state.get("top_score", 0.0),
            search_attempts=state.get("search_attempts", 0),
            saved_cost=state.get("saved_cost", 0),
            cost_note=state.get("cost_note", ""),
            elapsed_ms=elapsed_ms,
        )
        yield {
            "event": "metadata",
            "data": metadata.model_dump_json(),
        }

    else:
        # 이관 안내: 단일 응답
        escalation_msg = state.get("escalation_message", "")
        yield {
            "event": "message",
            "data": json.dumps(
                {"type": "escalation", "content": escalation_msg},
                ensure_ascii=False,
            ),
        }

        # 메타데이터 이벤트
        metadata = EscalationMetadata(
            process_type="escalation",
            agent_id=state.get("agent_id", ""),
            agent_name=state.get("agent_name", ""),
            queue_position=state.get("queue_position", 0),
            estimated_wait_minutes=state.get("estimated_wait_minutes", 0),
            priority=state.get("priority", ""),
        )
        yield {
            "event": "metadata",
            "data": metadata.model_dump_json(),
        }

    # 완료 이벤트
    yield {
        "event": "done",
        "data": "{}",
    }


@router.post("/v1/chat/stream")
async def chat_stream(
    request: Request,
    body: ChatRequest,
):
    """고객 질문 처리 (SSE 스트리밍).

    POST /v1/chat/stream
    """
    _verify_api_key(request)

    start_time = time.time()

    logger.info(
        "채팅 요청 수신",
        query=body.query[:50],
        channel=body.inquiry_channel.value,
    )

    try:
        workflow = get_workflow()

        # 초기 상태 설정
        initial_state = {
            "query": body.query,
            "inquiry_channel": body.inquiry_channel.value,
            "mock_preset": body.mock_preset.value,
            "mock_override": body.mock_override or "",
        }

        # 워크플로우 실행
        result = workflow.invoke(initial_state)

        elapsed_ms = int((time.time() - start_time) * 1000)
        result["elapsed_ms"] = elapsed_ms

        # 메트릭 기록
        record_request(
            process_type=result.get("process_type", "auto"),
            category=result.get("category", "기타"),
            channel=body.inquiry_channel.value,
            elapsed_seconds=(time.time() - start_time),
            saved_cost=result.get("saved_cost", 0),
            search_attempts=result.get("search_attempts", 1),
        )

        return EventSourceResponse(
            _stream_response(result, elapsed_ms),
            media_type="text/event-stream",
        )

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error("채팅 처리 실패", error=str(e), elapsed_ms=elapsed_ms)
        record_error(error_type=type(e).__name__)

        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="PROCESSING_ERROR",
                    message="요청 처리 중 오류가 발생했습니다.",
                    details=str(e),
                )
            ).model_dump(),
        )


@router.get("/v1/metrics/daily", response_model=DailyMetricsResponse)
async def daily_metrics(request: Request):
    """당일 처리 현황 및 절감 비용 조회.

    GET /v1/metrics/daily
    """
    _verify_api_key(request)

    settings = get_settings()

    try:
        if settings.use_mock:
            tracker = MockCostTracker()
        else:
            tracker = CostTracker(settings=settings)

        summary = tracker.get_daily_summary()

        return DailyMetricsResponse(
            date=date.today(),
            total_inquiries=summary.get("total_inquiries", 0),
            auto_processed=summary.get("auto_processed", 0),
            auto_rate=summary.get("auto_rate", 0.0),
            escalated=summary.get("escalated", 0),
            total_saved_today=summary.get("total_saved_today", 0),
            avg_response_ms=summary.get("avg_response_ms", 0),
            alert_triggered=summary.get("alert_triggered", False),
        )

    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_IMPLEMENTED",
                    message="Real 모드에서는 DB 연동이 필요합니다.",
                )
            ).model_dump(),
        )
    except Exception as e:
        logger.error("일별 메트릭 조회 실패", error=str(e))
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/v1/metrics/monthly", response_model=MonthlyMetricsResponse)
async def monthly_metrics(
    request: Request,
    year: int = 0,
    month: int = 0,
):
    """월별 집계 보고서 조회.

    GET /v1/metrics/monthly?year=2026&month=3
    """
    _verify_api_key(request)

    settings = get_settings()
    if year == 0:
        year = date.today().year
    if month == 0:
        month = date.today().month

    try:
        if settings.use_mock:
            tracker = MockCostTracker()
        else:
            tracker = CostTracker(settings=settings)

        summary = tracker.get_monthly_summary(year, month)

        return MonthlyMetricsResponse(
            year=summary.get("year", year),
            month=summary.get("month", month),
            total_inquiries=summary.get("total_inquiries", 0),
            auto_processed=summary.get("auto_processed", 0),
            auto_rate=summary.get("auto_rate", 0.0),
            total_saved=summary.get("total_saved", 0),
            avg_response_ms=summary.get("avg_response_ms", 0),
        )

    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="NOT_IMPLEMENTED",
                    message="Real 모드에서는 DB 연동이 필요합니다.",
                )
            ).model_dump(),
        )
    except Exception as e:
        logger.error("월별 메트릭 조회 실패", error=str(e))
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """서비스 헬스체크.

    GET /health
    """
    return HealthResponse(
        status="ok",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/metrics")
async def prometheus_metrics():
    """Prometheus 메트릭 엔드포인트.

    GET /metrics
    """
    return Response(
        content=get_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
