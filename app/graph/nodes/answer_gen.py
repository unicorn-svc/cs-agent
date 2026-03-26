"""Node 6: Auto-answer generation using LLM."""

import json
from typing import Any

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings
from app.core.logger import get_logger
from app.core.exceptions import LLMError
from app.graph.state import AgentState

logger = get_logger(__name__)
settings = get_settings()


def generate_answer(state: AgentState) -> dict[str, Any]:
    """Generate auto-answer based on FAQ search results."""
    try:
        # Mock path: skip LLM when mock_preset is active
        if state.mock_preset and state.mock_preset != "":
            mock_answer = "전원 버튼을 3초간 누르시면 LED가 점멸하며 연결 준비가 완료됩니다. 이후 기기와 페어링하세요."
            logger.info("Answer generated (mock)", length=len(mock_answer))
            return {"generated_answer": mock_answer}

        llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
        )

        system_prompt = """당신은 비용 효율을 최우선으로 하는 고객센터 자동 응답 에이전트입니다.

## 행동 규칙

- 정중하고 간결한 존댓말을 사용하세요.
- 200자 이내로 핵심 답변만 제공하세요.
- 불필요한 안부 인사나 감사 표현을 하지 마세요.
- FAQ 검색 결과에 없는 내용은 추측하여 답변하지 마세요.
- 검색 결과의 내용을 바탕으로 고객 질문에 직접 답변하세요.

## FAQ 검색 결과

"""

        # Parse FAQ results
        try:
            faq_items = json.loads(state.faq_results)
            faq_text = ""
            for item in faq_items:
                faq_text += f"- {item.get('title', '')}: {item.get('content', '')}\n"
        except json.JSONDecodeError:
            faq_text = state.faq_results

        system_prompt += faq_text

        user_prompt = state.query

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = llm.invoke(messages)
        generated_answer = response.content

        logger.info("Answer generated", length=len(generated_answer))

        return {"generated_answer": generated_answer}

    except Exception as e:
        logger.error("Answer generation failed", error=str(e))
        raise LLMError(f"Failed to generate answer: {str(e)}")
