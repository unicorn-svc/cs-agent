"""Pydantic 입출력 스키마 정의.

API 요청/응답의 데이터 검증 및 직렬화를 담당함.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


# --- Enum ---

class InquiryChannel(str, Enum):
    """문의 채널 종류."""
    WEB_CHAT = "웹채팅"
    KAKAO = "카카오톡"
    PHONE = "전화"
    EMAIL = "이메일"


class MockPreset(str, Enum):
    """MOCK 프리셋 종류."""
    DEFAULT = "default"
    EMPTY = "empty"
    ERROR = "error"
    TIMEOUT = "timeout"


# --- 요청 스키마 ---

class ChatRequest(BaseModel):
    """채팅 요청 스키마."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="고객 질문 텍스트",
    )
    inquiry_channel: InquiryChannel = Field(
        ...,
        description="문의 채널",
    )
    mock_preset: MockPreset = Field(
        default=MockPreset.DEFAULT,
        description="MOCK 프리셋",
    )
    mock_override: Optional[str] = Field(
        default="",
        max_length=1000,
        description="MOCK 오버라이드 JSON 문자열",
    )


# --- 중간 데이터 구조 ---

class ClassificationResult(BaseModel):
    """질문 분류 결과 (Node 3 출력, Structured Output)."""
    complexity: Literal["low", "high"] = Field(
        description="질문 복잡도",
    )
    category: str = Field(
        description="질문 카테고리 (제품사용, 배송, 결제, 환불, 계정, 기타)",
    )


class FAQItem(BaseModel):
    """FAQ 검색 결과 개별 항목."""
    title: str = Field(description="FAQ 항목 제목")
    content: str = Field(description="FAQ 답변 내용")
    score: float = Field(description="관련도 점수 (0-100)")


class SearchAttempt(BaseModel):
    """검색 시도 기록."""
    attempt: int
    query: str
    relevance: float
    top_score: float
    count: int


class FAQSearchResult(BaseModel):
    """FAQ 검색 결과 (Node 4 출력)."""
    results: list[FAQItem] = Field(default_factory=list)
    top_score: float = Field(default=0.0)
    count: int = Field(default=0)
    search_attempts: int = Field(default=1)
    evaluation_log: list[SearchAttempt] = Field(default_factory=list)


class CostAggregation(BaseModel):
    """비용 집계 결과 (Node 7 출력)."""
    saved_cost: int = Field(default=0, description="건당 절감액 (원)")
    auto_processed: int = Field(default=0, description="처리 건수")
    total_saved_today: int = Field(default=0, description="당일 누적 절감액 (원)")
    total_auto_today: int = Field(default=0, description="당일 누적 자동 처리 건수")
    cost_note: str = Field(default="", description="절감액 안내 문구")


class AgentAssignment(BaseModel):
    """상담원 배정 결과 (Node 9 출력)."""
    agent_id: str = Field(default="")
    agent_name: str = Field(default="")
    queue_position: int = Field(default=0)
    estimated_wait_minutes: int = Field(default=0)
    priority: Literal["normal", "high"] = Field(default="normal")
    status: Literal["queued", "no_agent_available", "system_error", "timeout"] = Field(
        default="queued",
    )


# --- SSE 응답 스키마 ---

class SSETokenEvent(BaseModel):
    """SSE 토큰 이벤트."""
    type: Literal["token"] = "token"
    content: str


class SSEEscalationEvent(BaseModel):
    """SSE 이관 안내 이벤트."""
    type: Literal["escalation"] = "escalation"
    content: str


class AutoAnswerMetadata(BaseModel):
    """자동 답변 메타데이터."""
    process_type: Literal["auto"] = "auto"
    category: str = ""
    complexity: str = ""
    top_score: float = 0.0
    search_attempts: int = 0
    saved_cost: int = 0
    cost_note: str = ""
    elapsed_ms: int = 0


class EscalationMetadata(BaseModel):
    """이관 안내 메타데이터."""
    process_type: Literal["escalation"] = "escalation"
    agent_id: str = ""
    agent_name: str = ""
    queue_position: int = 0
    estimated_wait_minutes: int = 0
    priority: str = ""


# --- 메트릭 응답 스키마 ---

class DailyMetricsResponse(BaseModel):
    """당일 처리 현황 응답."""
    date: date
    total_inquiries: int = 0
    auto_processed: int = 0
    auto_rate: float = 0.0
    escalated: int = 0
    total_saved_today: int = 0
    avg_response_ms: int = 0
    alert_triggered: bool = False


class MonthlyMetricsResponse(BaseModel):
    """월별 집계 보고서 응답."""
    year: int
    month: int
    total_inquiries: int = 0
    auto_processed: int = 0
    auto_rate: float = 0.0
    total_saved: int = 0
    avg_response_ms: int = 0


# --- 에러 응답 스키마 ---

class ErrorDetail(BaseModel):
    """에러 상세 정보."""
    code: str
    message: str
    details: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답."""
    error: ErrorDetail


# --- 헬스체크 ---

class HealthResponse(BaseModel):
    """헬스체크 응답."""
    status: str = "ok"
    version: str = "0.1.0"
    timestamp: datetime
