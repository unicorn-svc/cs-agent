"""Node 2: 질문 분류 (LLM).

고객 질문의 복잡도와 FAQ 처리 가능 여부를 판단하여
JSON 형식으로 분류 결과를 출력함.
DSL Node 2 (질문 분류)에 대응.
"""

from __future__ import annotations

import structlog
from langchain_groq import ChatGroq

from app.config.settings import get_settings
from app.graph.state import AgentState

logger = structlog.get_logger()

SYSTEM_PROMPT = """당신은 고객 문의 분류 전문가입니다.

고객의 질문을 분석하여 아래 기준으로 분류하세요.

## 분류 기준

- complexity: "low" (단순 FAQ, 제품 사용법, 배송 조회, 정책 안내, 단순 계정 설정) 또는 "high" (환불 분쟁, 결제 오류, 개인정보 관련, 복합 문의)
- category: 질문의 주제 카테고리 (제품사용, 배송, 결제, 환불, 계정, 기타)

## 분류 예시

### low 예시
- "충전 케이블 연결 방법을 알려주세요" → low, 제품사용
- "배송 현황을 확인하고 싶습니다" → low, 배송
- "비밀번호 변경 방법" → low, 계정

### high 예시
- "결제가 두 번 되었는데 환불해주세요" → high, 환불
- "개인정보 삭제를 요청합니다" → high, 계정
- "불량품 교환과 환불을 동시에 처리하고 싶습니다" → high, 환불

## 응답 형식

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.
{"complexity": "low 또는 high", "category": "카테고리명"}
"""

USER_PROMPT_TEMPLATE = """[문의 채널] {inquiry_channel}
[고객 질문] {query}
"""


def classify_question(state: AgentState) -> AgentState:
    """LLM을 사용하여 고객 질문을 분류함.

    Args:
        state: 현재 워크플로우 상태

    Returns:
        classification_raw 필드가 업데이트된 상태
    """
    settings = get_settings()
    query = state.get("query", "")
    inquiry_channel = state.get("inquiry_channel", "웹채팅")

    logger.info(
        "질문 분류 시작",
        query=query[:50],
        channel=inquiry_channel,
    )

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            max_tokens=settings.groq_max_tokens,
            temperature=settings.groq_temperature,
            base_url="https://api.groq.com",
        )

        user_prompt = USER_PROMPT_TEMPLATE.format(
            inquiry_channel=inquiry_channel,
            query=query,
        )

        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt),
        ]

        response = llm.invoke(messages)
        raw_text = response.content if hasattr(response, "content") else str(response)

        logger.info("질문 분류 완료", raw_output=raw_text[:100])

        return {"classification_raw": raw_text}

    except Exception as e:
        logger.error("질문 분류 LLM 호출 실패", error=str(e))
        # 실패 시 상담원 이관 경로로 폴백
        return {
            "classification_raw": '{"complexity": "high", "category": "기타"}',
            "error": f"LLM 분류 실패: {str(e)}",
        }
