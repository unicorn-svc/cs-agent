"""Node 2: Question classification using LLM."""

import json
from typing import Any, Optional

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings
from app.core.logger import get_logger
from app.core.exceptions import LLMError
from app.graph.state import AgentState

logger = get_logger(__name__)
settings = get_settings()


def classify_question(state: AgentState) -> dict[str, Any]:
    """Classify customer question by complexity and category using LLM."""
    try:
        # Mock path: skip LLM when mock_preset is active
        if state.mock_preset and state.mock_preset != "":
            if state.mock_preset in ("empty", "error", "timeout"):
                llm_output = '{"complexity": "high", "category": "기타"}'
            else:
                # Heuristic: phone channel or escalation keywords -> high complexity
                escalation_keywords = ["환불", "분쟁", "소송", "법적", "결제 오류"]
                is_escalation = (
                    state.inquiry_channel == "전화"
                    or any(kw in state.query for kw in escalation_keywords)
                )
                if is_escalation:
                    llm_output = '{"complexity": "high", "category": "환불"}'
                else:
                    llm_output = '{"complexity": "low", "category": "제품사용"}'
            logger.info("Question classified (mock)", llm_output=llm_output)
            return {"llm_output": llm_output}

        llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
        )

        system_prompt = """당신은 고객 문의 분류 전문가입니다.

고객의 질문을 분석하여 아래 기준으로 분류하세요.

## 분류 기준

- complexity: "low" (단순 FAQ, 제품 사용법, 정책 안내) 또는 "high" (개인정보 관련, 환불/결제 분쟁, 복합 문의)
- category: 질문의 주제 카테고리 (예: "제품사용", "배송", "결제", "환불", "계정", "기타")

## 응답 형식

반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.

{"complexity": "low 또는 high", "category": "카테고리명"}
"""

        user_prompt = f"""[문의 채널] {state.inquiry_channel}

[고객 질문] {state.query}
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        llm_output = response.content

        logger.info("Question classified", llm_output=llm_output[:100])

        return {"llm_output": llm_output}

    except Exception as e:
        logger.error("Question classification failed", error=str(e))
        raise LLMError(f"Failed to classify question: {str(e)}")
