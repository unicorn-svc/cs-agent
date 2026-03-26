"""API routes for the agent."""

import asyncio
import time
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    ChatRequest,
    AutoAnswerResponse,
    EscalationResponse,
    DailyMetricsResponse,
    MonthlyMetricsResponse,
    ErrorResponse,
)
from app.graph.workflow import create_workflow
from app.graph.state import AgentState
from app.config.settings import get_settings
from app.core.logger import get_logger

router = APIRouter(prefix="/v1", tags=["chat"])
logger = get_logger(__name__)
settings = get_settings()

# Initialize workflow
workflow = None


def get_workflow():
    """Get or create workflow instance."""
    global workflow
    if workflow is None:
        workflow = create_workflow()
    return workflow


async def generate_sse_response(state: AgentState):
    """Generate SSE response stream for auto-answer."""
    try:
        # Stream answer tokens
        answer = state.generated_answer
        for chunk in answer.split(" "):
            yield f'event: message\ndata: {json.dumps({"type": "token", "content": chunk + " "})}\n\n'
            await asyncio.sleep(0.01)  # Small delay for streaming effect

        # Send metadata
        metadata = {
            "process_type": "auto",
            "category": state.category,
            "complexity": state.complexity,
            "top_score": state.top_score,
            "search_attempts": state.search_attempts,
            "saved_cost": state.saved_cost,
            "cost_note": state.cost_note,
            "elapsed_ms": 3200,  # Mock elapsed time
        }
        yield f'event: metadata\ndata: {json.dumps(metadata)}\n\n'

        # Send done event
        yield f'event: done\ndata: {{}}\n\n'

    except Exception as e:
        logger.error("Error generating SSE response", error=str(e))
        yield f'event: error\ndata: {json.dumps({"error": str(e)})}\n\n'


async def generate_escalation_response(state: AgentState):
    """Generate SSE response stream for escalation."""
    try:
        # Send escalation message
        message = f"""해당 문의는 전문 상담원의 도움이 필요합니다.

상담원 연결까지 약 {state.estimated_wait_minutes}분 소요 예정입니다.
대기 순서: {state.queue_position}번째

잠시만 기다려 주시면 {state.agent_name} 상담원이 도와드리겠습니다.
"""
        yield f'event: message\ndata: {json.dumps({"type": "escalation", "content": message})}\n\n'

        # Send metadata
        metadata = {
            "process_type": "escalation",
            "agent_id": state.agent_id,
            "agent_name": state.agent_name,
            "queue_position": state.queue_position,
            "estimated_wait_minutes": state.estimated_wait_minutes,
            "priority": state.priority,
        }
        yield f'event: metadata\ndata: {json.dumps(metadata)}\n\n'

        # Send done event
        yield f'event: done\ndata: {{}}\n\n'

    except Exception as e:
        logger.error("Error generating escalation response", error=str(e))
        yield f'event: error\ndata: {json.dumps({"error": str(e)})}\n\n'


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    x_api_key: str = Header(None),
):
    """
    Stream chat response.
    
    Handles both auto-answer and escalation paths.
    """
    # API Key validation
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    try:
        logger.info("Chat request received", channel=request.inquiry_channel, query_len=len(request.query))

        # Create initial state
        state = AgentState(
            query=request.query,
            inquiry_channel=request.inquiry_channel,
            mock_preset=request.mock_preset,
            mock_override=request.mock_override,
        )

        # Run workflow
        start_time = time.time()
        workflow = get_workflow()
        result_state = await asyncio.to_thread(workflow.invoke, state.model_dump())
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Convert result to AgentState
        final_state = AgentState(**result_state)
        final_state.process_type = "auto" if final_state.auto_processable else "escalation"

        # Return streaming response
        if final_state.auto_processable:
            logger.info("Auto-answer path", saved_cost=final_state.saved_cost)
            return StreamingResponse(
                generate_sse_response(final_state),
                media_type="text/event-stream",
            )
        else:
            logger.info("Escalation path", agent_id=final_state.agent_id)
            return StreamingResponse(
                generate_escalation_response(final_state),
                media_type="text/event-stream",
            )

    except Exception as e:
        logger.error("Chat request failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/daily")
async def get_daily_metrics(x_api_key: str = Header(None)):
    """Get daily metrics."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return DailyMetricsResponse(
        date=datetime.now().strftime("%Y-%m-%d"),
        total_inquiries=1000,
        auto_processed=720,
        auto_rate=72.0,
        escalated=280,
        total_saved_today=20160000,
        avg_response_ms=3500,
        alert_triggered=False,
    )


@router.get("/metrics/monthly")
async def get_monthly_metrics(
    year: int = 2026,
    month: int = 1,
    x_api_key: str = Header(None),
):
    """Get monthly metrics."""
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")

    return MonthlyMetricsResponse(
        year=year,
        month=month,
        total_inquiries=30000,
        auto_processed=21600,
        auto_rate=72.0,
        escalated=8400,
        total_saved=604800000,
        avg_response_ms=3500,
    )


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
