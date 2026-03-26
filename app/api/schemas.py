"""Pydantic schemas for API requests and responses."""

from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class InquiryChannel(str, Enum):
    """Inquiry channel types."""

    WEB = "웹채팅"
    KAKAO = "카카오톡"
    PHONE = "전화"
    EMAIL = "이메일"


class MockPreset(str, Enum):
    """MOCK preset types."""

    DEFAULT = "default"
    EMPTY = "empty"
    ERROR = "error"
    TIMEOUT = "timeout"


class ChatRequest(BaseModel):
    """Chat request schema."""

    query: str = Field(..., min_length=1, max_length=1000, description="Customer question")
    inquiry_channel: InquiryChannel = Field(default=InquiryChannel.WEB, description="Inquiry channel")
    mock_preset: MockPreset = Field(default=MockPreset.DEFAULT, description="MOCK preset")
    mock_override: Optional[str] = Field(default="", max_length=1000, description="MOCK override JSON")

    @field_validator("query")
    @classmethod
    def reject_control_characters(cls, v: str) -> str:
        """SSE injection 방지: 제어 문자 포함 시 거부."""
        if "\n" in v or "\r" in v or "\0" in v:
            raise ValueError("query must not contain control characters (newline, carriage return, null)")
        return v


class FAQItem(BaseModel):
    """FAQ item in search results."""

    title: str
    content: str
    score: float


class ClassificationResult(BaseModel):
    """Classification result."""

    complexity: str
    category: str
    top_score: float
    search_attempts: int


class AutoAnswerMetadata(BaseModel):
    """Metadata for auto-answer response."""

    process_type: str = "auto"
    category: str
    complexity: str
    top_score: float
    search_attempts: int
    saved_cost: int
    cost_note: str
    elapsed_ms: int


class AutoAnswerResponse(BaseModel):
    """Auto-answer response."""

    message: str
    metadata: AutoAnswerMetadata


class EscalationMetadata(BaseModel):
    """Metadata for escalation response."""

    process_type: str = "escalation"
    agent_id: str
    agent_name: str
    queue_position: int
    estimated_wait_minutes: int
    priority: str


class EscalationResponse(BaseModel):
    """Escalation response."""

    message: str
    metadata: EscalationMetadata


class DailyMetricsResponse(BaseModel):
    """Daily metrics response."""

    date: str
    total_inquiries: int
    auto_processed: int
    auto_rate: float
    escalated: int
    total_saved_today: int
    avg_response_ms: int
    alert_triggered: bool


class MonthlyMetricsResponse(BaseModel):
    """Monthly metrics response."""

    year: int
    month: int
    total_inquiries: int
    auto_processed: int
    auto_rate: float
    escalated: int
    total_saved: int
    avg_response_ms: int


class ErrorResponse(BaseModel):
    """Error response."""

    error: dict = Field(default_factory=dict)
    code: str
    message: str
    details: Optional[str] = None
