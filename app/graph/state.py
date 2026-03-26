"""LangGraph StateGraph 상태 정의.

DSL의 노드 간 데이터 흐름을 AgentState TypedDict로 정의함.
각 노드는 이 상태 객체를 읽고 업데이트하여 데이터를 전달함.
"""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict, total=False):
    """워크플로우 전체 상태 스키마.

    각 필드는 DSL 노드의 입출력 변수에 1:1 대응함.
    total=False로 설정하여 노드가 필요한 필드만 업데이트 가능.
    """

    # 입력 (Node 1: 시작)
    query: str  # 고객 질문 (sys.query)
    inquiry_channel: str  # 문의 채널
    mock_preset: str  # MOCK 프리셋 (default/empty/error/timeout)
    mock_override: str  # MOCK 오버라이드 JSON

    # Node 2-3 출력: 질문 분류
    classification_raw: str  # LLM 원본 출력
    complexity: str  # "low" | "high"
    category: str  # 카테고리명

    # Node 4 출력: FAQ 검색 + 관련도 평가
    faq_results: str  # JSON 문자열 (FAQ 검색 결과)
    top_score: float  # 최고 관련도 점수
    faq_count: int  # 검색 결과 수
    search_attempts: int  # 검색 시도 횟수
    evaluation_log: str  # 평가 로그 JSON

    # Node 5 라우팅: 자동처리 가능 여부
    auto_processable: bool

    # Node 6 출력: 자동 답변 생성
    generated_answer: str  # LLM 생성 답변

    # Node 7 출력: 비용 절감 집계
    saved_cost: int  # 건당 절감 비용
    auto_processed: int  # 처리 건수
    total_saved_today: int  # 당일 누적 절감액
    total_auto_today: int  # 당일 누적 자동 처리 건수
    cost_note: str  # 절감 비용 안내 문구

    # Node 8 출력: 자동 답변
    auto_answer_text: str  # 최종 자동 답변 텍스트

    # Node 9 출력: 상담원 배정
    agent_id: str  # 배정 상담원 ID
    agent_name: str  # 배정 상담원 이름
    queue_position: int  # 대기 순서
    estimated_wait_minutes: int  # 예상 대기 시간
    priority: str  # 우선순위 (normal/high)
    assign_status: str  # 배정 상태

    # Node 10 출력: 상담원 이관 안내
    escalation_message: str  # 이관 안내 메시지

    # 메타데이터
    process_type: str  # "auto" | "escalation"
    elapsed_ms: int  # 처리 소요 시간 (ms)
    error: str  # 에러 메시지 (있는 경우)
