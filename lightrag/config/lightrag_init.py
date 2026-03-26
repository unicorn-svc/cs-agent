"""LightRAG 인스턴스 팩토리 모듈

Groq LPU(LLM) + OpenAI(임베딩) 연동 LightRAG 인스턴스를 생성.
"""
import logging
from functools import partial

from lightrag import LightRAG
from lightrag.llm.openai import openai_complete, openai_embed
from lightrag.utils import EmbeddingFunc, always_get_an_event_loop

from config.settings import Settings

logger = logging.getLogger(__name__)


def create_lightrag(settings: Settings) -> LightRAG:
    """LightRAG 인스턴스 생성

    Groq LPU(LLM) + OpenAI(임베딩) 조합.
    openai_embed.func 사용으로 EmbeddingFunc 이중 래핑 방지.

    Args:
        settings: 시스템 전역 설정

    Returns:
        초기화된 LightRAG 인스턴스
    """
    working_dir = settings.working_dir_path
    working_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "LightRAG 초기화: working_dir=%s, "
        "llm=%s (Groq LPU), embedding=%s (dim=%d, OpenAI)",
        working_dir,
        settings.groq_model,
        settings.embedding_model,
        settings.embedding_dim,
    )

    rag = LightRAG(
        working_dir=str(working_dir),
        # LLM: Groq LPU (OpenAI 호환 API)
        llm_model_func=openai_complete,
        llm_model_name=settings.groq_model,
        llm_model_kwargs={
            "base_url": settings.groq_base_url,
            "api_key": settings.groq_api_key,
        },
        # 청크 분할 설정
        chunk_token_size=settings.chunk_token_size,
        chunk_overlap_token_size=settings.chunk_overlap_token_size,
        # 임베딩: OpenAI API
        embedding_func=EmbeddingFunc(
            embedding_dim=settings.embedding_dim,
            max_token_size=settings.embedding_max_token_size,
            func=partial(
                openai_embed.func,
                model=settings.embedding_model,
                api_key=settings.openai_api_key,
            ),
        ),
        # 타임아웃
        default_embedding_timeout=settings.embedding_timeout,
        default_llm_timeout=settings.llm_timeout,
    )

    # v1.4.9+ 스토리지 수동 초기화
    loop = always_get_an_event_loop()
    if not loop.is_running():
        loop.run_until_complete(rag.initialize_storages())

    logger.info("LightRAG 인스턴스 생성 완료")
    return rag
