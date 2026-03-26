"""FAQ 지식베이스 의미 검색 도구.

LightRAG 기반 FAQ 검색 (Real) 및 Mock 구현을 제공함.
DSL Node 4의 search_faq() 대응.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class FAQKnowledgeBase:
    """Real FAQ 지식베이스 검색 (LightRAG 검색).

    이미 빌드된 LightRAG 인덱스를 로드하여 검색을 수행함.
    Groq LPU(LLM) + OpenAI(임베딩) 조합 사용.
    event loop 충돌 방지를 위해 매 검색마다 별도 스레드에서
    LightRAG 인스턴스 생성 + 쿼리를 동일 loop에서 실행함.
    """

    def __init__(self, settings: Any = None) -> None:
        self._settings = settings
        self._lr_settings = None
        self._search_mode = "naive"
        self._default_top_k = 60

    def _load_lr_settings(self) -> None:
        """LightRAG 설정을 로드함 (1회만)."""
        if self._lr_settings is not None:
            return

        lightrag_root = Path(__file__).resolve().parent.parent.parent / "lightrag"
        if str(lightrag_root) not in sys.path:
            sys.path.insert(0, str(lightrag_root))

        from config.settings import Settings as LightRAGSettings
        self._lr_settings = LightRAGSettings.from_env()
        self._search_mode = self._lr_settings.default_search_mode
        self._default_top_k = self._lr_settings.top_k
        logger.info(
            "LightRAG 설정 로드 완료",
            working_dir=str(self._lr_settings.working_dir_path),
            search_mode=self._search_mode,
        )

    def search(
        self,
        query: str,
        category: str,
        top_k: int = 5,
    ) -> dict:
        """FAQ 의미 검색을 수행함 (LightRAG 검색).

        Args:
            query: 검색 질문 텍스트
            category: 질문 카테고리
            top_k: 반환할 최대 결과 수

        Returns:
            results, top_score, count를 포함하는 dict
        """
        try:
            self._load_lr_settings()

            search_query = f"[{category}] {query}" if category and category != "기타" else query

            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result_text = pool.submit(
                    self._run_query_in_new_loop, search_query
                ).result(timeout=30)

            if result_text and result_text.strip():
                results = [
                    {
                        "title": f"FAQ-{category}-001",
                        "content": result_text.strip(),
                        "score": 85.0,
                    },
                ]
                return {
                    "results": results,
                    "top_score": 85.0,
                    "count": 1,
                }

            return {"results": [], "top_score": 0.0, "count": 0}

        except Exception as e:
            logger.error("FAQ 검색 실패", error=str(e))
            return {"results": [], "top_score": 0.0, "count": 0}

    def _run_query_in_new_loop(self, search_query: str) -> str:
        """별도 스레드에서 새 event loop를 만들어 LightRAG 생성 + 쿼리를 실행함.

        이렇게 하면 PriorityQueue와 쿼리가 동일한 event loop에 바인딩됨.
        """
        from config.lightrag_init import create_lightrag
        from lightrag import QueryParam

        async def _do_query():
            rag = create_lightrag(self._lr_settings)
            await rag.initialize_storages()
            result = await rag.aquery(
                search_query,
                param=QueryParam(
                    mode=self._search_mode,
                    top_k=self._default_top_k,
                ),
            )
            return result

        return asyncio.run(_do_query())


class MockFAQKnowledgeBase(FAQKnowledgeBase):
    """Mock FAQ 검색 구현.

    DSL Node 4의 해시 기반 MOCK 전략을 재현함.
    프리셋 및 오버라이드를 지원함.
    """

    def __init__(
        self,
        preset: str = "default",
        override: str = "",
    ) -> None:
        super().__init__(settings=None)
        self._preset = preset
        self._override = override

    def _ensure_initialized(self) -> None:
        """Mock은 초기화 불필요."""
        pass

    def search(
        self,
        query: str,
        category: str,
        top_k: int = 5,
    ) -> dict:
        """Mock FAQ 검색 - DSL 해시 전략 재현."""
        # 오버라이드 처리
        if self._override and self._override.strip():
            try:
                return json.loads(self._override)
            except json.JSONDecodeError:
                pass

        # 프리셋별 처리
        if self._preset == "empty":
            return {"results": [], "top_score": 0.0, "count": 0}

        if self._preset == "error":
            logger.warning("Mock FAQ 검색 에러 프리셋")
            return {"results": [], "top_score": 0.0, "count": 0}

        if self._preset == "timeout":
            logger.warning("Mock FAQ 검색 타임아웃 프리셋")
            return {"results": [], "top_score": 0.0, "count": 0}

        # default 프리셋: 해시 기반 변형
        variant = sum(ord(c) for c in query) % 3

        if variant == 0:
            return {
                "results": [
                    {
                        "title": f"FAQ-{category}-001",
                        "content": (
                            "해당 제품의 사용 방법은 다음과 같습니다. "
                            "1) 전원 버튼을 3초간 누릅니다. "
                            "2) LED가 점멸하면 연결 준비 완료입니다. "
                            "3) 기기와 페어링하세요."
                        ),
                        "score": 88.0,
                    },
                    {
                        "title": f"FAQ-{category}-002",
                        "content": "추가 도움이 필요하시면 사용 설명서 12페이지를 참고해 주세요.",
                        "score": 76.0,
                    },
                ],
                "top_score": 88.0,
                "count": 2,
            }
        elif variant == 1:
            return {"results": [], "top_score": 0.0, "count": 0}
        else:
            return {
                "results": [
                    {
                        "title": "FAQ-일반-099",
                        "content": "죄송합니다. 관련 FAQ를 찾을 수 없습니다.",
                        "score": 35.0,
                    },
                ],
                "top_score": 35.0,
                "count": 1,
            }
