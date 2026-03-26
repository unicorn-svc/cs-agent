"""환경 설정 관리 모듈.

API Key, 임계값, 외부 시스템 URL 등 모든 환경 설정을 관리함.
.env 파일 또는 환경 변수에서 값을 로드함.

필수 환경 변수:
    GROQ_API_KEY: Groq API 인증 키 (프로덕션 배포 시 실제 키 설정 필수)
    OPENAI_API_KEY: OpenAI API 키 (LightRAG 임베딩용, 프로덕션 배포 시 실제 키 설정 필수)

보안 주의사항:
    - API 키를 소스 코드나 로그에 노출하지 않아야 함
    - .env 파일은 .gitignore에 포함되어 있으며, 플레이스홀더 값만 커밋해야 함
"""

from __future__ import annotations

import logging
from typing import List

from pydantic_settings import BaseSettings

_PLACEHOLDER_VALUES = frozenset({
    "your-groq-api-key-here",
    "your-openai-api-key-here",
})

_logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """애플리케이션 환경 설정.

    모든 설정은 환경 변수 또는 .env 파일에서 로드됨.
    API 키는 반드시 실제 값으로 설정해야 하며, 플레이스홀더 값이 감지되면 경고를 출력함.
    """

    # Groq API
    groq_api_key: str = ""
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"
    groq_max_tokens: int = 512
    groq_temperature: float = 0.1

    # 서비스 API 인증
    api_key: str = ""

    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001

    # PostgreSQL
    postgres_dsn: str = "postgresql://csagent:csagent@localhost:5432/csagent"

    # 상담원 업무 시스템
    agent_system_api_url: str = "http://localhost:9000/api/v1"

    # 알림 Webhook
    notify_webhook_url: str = ""

    # 임계값
    auto_rate_alert_threshold: int = 60
    faq_score_threshold: int = 75
    faq_relevance_threshold: int = 90
    max_search_attempts: int = 3
    cost_per_case: int = 28000  # 상담원 1건 처리 비용 (원)

    # 서버 설정
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"
    log_level: str = "INFO"
    environment: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # OpenAI (LightRAG 임베딩용)
    openai_api_key: str = ""

    # Mock 모드
    use_mock: bool = True

    # 처리 타임아웃 (초)
    processing_timeout: int = 30
    llm_retry_count: int = 2

    # CORS 허용 오리진
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    def get_allowed_origins(self) -> List[str]:
        """CORS 허용 오리진 목록 반환."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    def validate_api_keys(self) -> None:
        """API 키가 플레이스홀더인지 검증하고 경고 로그 출력.

        프로덕션 환경에서 플레이스홀더 값이 감지되면 WARNING 로그를 출력함.
        개발 환경에서도 경고하지만, 프로덕션에서는 더 강한 경고를 출력함.
        """
        is_production = self.app_env == "production" or self.environment == "production"
        env_label = "PRODUCTION" if is_production else "DEVELOPMENT"

        if self.groq_api_key in _PLACEHOLDER_VALUES or not self.groq_api_key:
            _logger.warning(
                "[%s] GROQ_API_KEY가 설정되지 않았거나 플레이스홀더 값임. "
                "실제 API 키를 환경 변수에 설정하세요.",
                env_label,
            )

        if self.openai_api_key in _PLACEHOLDER_VALUES or not self.openai_api_key:
            _logger.warning(
                "[%s] OPENAI_API_KEY가 설정되지 않았거나 플레이스홀더 값임. "
                "실제 API 키를 환경 변수에 설정하세요.",
                env_label,
            )


def get_settings() -> Settings:
    """설정 싱글톤 반환."""
    return Settings()
