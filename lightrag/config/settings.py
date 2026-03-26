"""시스템 전역 설정 모듈

LightRAG + Groq LPU(LLM) + OpenAI(임베딩) 조합 설정.
환경 변수 또는 기본값으로 초기화.
"""
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class Settings:
    """시스템 전역 설정

    Groq LPU(LLM) + OpenAI(임베딩) 조합의 설정값 관리.
    환경 변수로 오버라이드 가능.
    """

    # 프로젝트 경로
    project_root: Path      # lightrag 프로젝트 루트
    data_dir: Path           # LightRAG 데이터 저장 디렉토리
    faq_data_dir: Path       # 고객상담 FAQ 데이터 디렉토리

    # Groq LPU 설정 (LLM)
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # OpenAI 임베딩 설정
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536
    embedding_max_token_size: int = 8191

    # LightRAG 설정
    working_dir: str = "lightrag_data"
    llm_context_size: int = 8192
    chunk_token_size: int = 2000
    chunk_overlap_token_size: int = 200

    # 타임아웃 설정 (초)
    embedding_timeout: int = 120
    llm_timeout: int = 300

    # 검색 설정
    default_search_mode: str = "hybrid"
    top_k: int = 60

    @property
    def working_dir_path(self) -> Path:
        """LightRAG 작업 디렉토리 절대 경로"""
        return self.project_root / self.working_dir

    @classmethod
    def from_env(cls) -> "Settings":
        """환경 변수 및 기본값으로 Settings 인스턴스 생성

        cs-agent 프로젝트 루트 .env 및 lightrag/.env에서 로드.
        """
        project_root = Path(__file__).resolve().parent.parent
        cs_agent_root = project_root.parent  # cs-agent 루트

        # 1) cs-agent 루트 .env에서 API 키 로드
        root_env = cs_agent_root / ".env"
        load_dotenv(root_env, override=True)

        # 2) lightrag 로컬 .env에서 LightRAG 설정 로드
        local_env = project_root / ".env"
        load_dotenv(local_env, override=True)

        return cls(
            project_root=project_root,
            data_dir=project_root / "lightrag_data",
            faq_data_dir=project_root / "data",
            # Groq LPU
            groq_api_key=os.getenv("GROQ_API_KEY", ""),
            groq_base_url=os.getenv(
                "GROQ_BASE_URL",
                "https://api.groq.com/openai/v1",
            ),
            groq_model=os.getenv(
                "GROQ_MODEL", "llama-3.3-70b-versatile"
            ),
            # OpenAI 임베딩
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", "text-embedding-3-small"
            ),
            embedding_dim=int(os.getenv(
                "EMBEDDING_DIM", "1536"
            )),
            embedding_max_token_size=int(os.getenv(
                "EMBEDDING_MAX_TOKEN_SIZE", "8191"
            )),
            # LightRAG
            working_dir=os.getenv(
                "LIGHTRAG_WORKING_DIR", "lightrag_data"
            ),
            llm_context_size=int(os.getenv(
                "LLM_CONTEXT_SIZE", "8192"
            )),
            # 타임아웃
            embedding_timeout=int(os.getenv(
                "EMBEDDING_TIMEOUT", "120"
            )),
            llm_timeout=int(os.getenv(
                "LLM_TIMEOUT", "300"
            )),
            # 검색
            default_search_mode=os.getenv(
                "DEFAULT_SEARCH_MODE", "hybrid"
            ),
            top_k=int(os.getenv("TOP_K", "60")),
        )
