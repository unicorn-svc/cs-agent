"""LightRAG FAQ 검색 스크립트

CLI에서 질문을 입력하면 LightRAG hybrid 검색으로 FAQ 답변을 반환.

사용법:
    python search.py "충전 케이블 연결 방법"
    python search.py "요금 조회" --mode hybrid
    python search.py "인터넷 속도 느림" --top_k 5
"""
import argparse
import asyncio
import io
import logging
import sys

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, encoding="utf-8", errors="replace"
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer, encoding="utf-8", errors="replace"
    )

from lightrag import QueryParam

from config.settings import Settings
from config.lightrag_init import create_lightrag

# 로깅 설정
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="LightRAG FAQ 검색"
    )
    parser.add_argument(
        "query",
        type=str,
        help="검색 질문 텍스트",
    )
    parser.add_argument(
        "--mode",
        choices=["naive", "local", "global", "hybrid"],
        default=None,
        help="검색 모드 (기본: settings의 default_search_mode)",
    )
    parser.add_argument(
        "--top_k",
        type=int,
        default=None,
        help="반환할 최대 결과 수 (기본: settings의 top_k)",
    )
    return parser.parse_args()


async def search(
    query: str,
    mode: str | None = None,
    top_k: int | None = None,
) -> str:
    """LightRAG 검색 수행

    Args:
        query: 검색 질문 텍스트
        mode: 검색 모드 (naive/local/global/hybrid)
        top_k: 반환할 최대 결과 수

    Returns:
        검색 결과 텍스트
    """
    settings = Settings.from_env()
    search_mode = mode or settings.default_search_mode
    search_top_k = top_k or settings.top_k

    rag = create_lightrag(settings)
    await rag.initialize_storages()

    result = await rag.aquery(
        query,
        param=QueryParam(mode=search_mode, top_k=search_top_k),
    )

    return result


async def main():
    """메인 실행 함수"""
    args = parse_args()

    print(f"\n{'='*60}")
    print(f"  질문: {args.query}")
    print(f"  검색 모드: {args.mode or '(default: hybrid)'}")
    print(f"{'='*60}\n")

    try:
        result = await search(
            query=args.query,
            mode=args.mode,
            top_k=args.top_k,
        )
        print("[ 검색 결과 ]")
        print("-" * 60)
        print(result)
        print("-" * 60)
    except Exception as e:
        print(f"검색 실패: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
