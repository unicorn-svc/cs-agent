"""환경 설정 관리 모듈.

API Key, 임계값, 외부 시스템 URL 등 모든 환경 설정을 관리함.
.env 파일 또는 환경 변수에서 값을 로드함.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 환경 설정."""

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

    # OpenAI (LightRAG 임베딩용)
    openai_api_key: str = ""

    # Mock 모드
    use_mock: bool = True

    # 처리 타임아웃 (초)
    processing_timeout: int = 30
    llm_retry_count: int = 2

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


def get_settings() -> Settings:
    """설정 싱글톤 반환."""
    return Settings()
