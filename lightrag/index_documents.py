"""LightRAG 문서 인덱싱 스크립트

사용법:
    python index_documents.py              # 전체 인덱싱
    python index_documents.py --force      # 인덱스 초기화 후 재인덱싱
    python index_documents.py --mode test  # 테스트용 소량 인덱싱
"""
import argparse
import asyncio
import logging
import shutil
import sys
from datetime import datetime
from pathlib import Path

from config.settings import Settings
from config.lightrag_init import create_lightrag
from indexing.document_loader import DocumentLoader

# 로깅 설정
log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = log_dir / f"indexing_{timestamp}.log"

file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
))

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler],
)

logger = logging.getLogger(__name__)


def parse_args():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="LightRAG 문서 인덱싱 (고객상담 FAQ)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 인덱스를 삭제하고 처음부터 재인덱싱",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "test"],
        default="full",
        help="인덱싱 모드: full(전체), test(소량 테스트)",
    )
    return parser.parse_args()


def clear_index(working_dir: Path):
    """인덱스 데이터 전체 삭제"""
    if working_dir.exists():
        shutil.rmtree(working_dir)
        logger.info("인덱스 초기화 완료: %s", working_dir)
    else:
        logger.info("초기화할 인덱스 없음: %s", working_dir)


async def main():
    """메인 인덱싱 실행 함수"""
    args = parse_args()

    logger.info("=" * 50)
    logger.info("LightRAG 인덱싱 시작 (고객상담 FAQ)")
    logger.info("=" * 50)

    # 설정 로드
    settings = Settings.from_env()
    logger.info(
        "설정: llm=%s (Groq LPU), embedding=%s (dim=%d, OpenAI)",
        settings.groq_model,
        settings.embedding_model,
        settings.embedding_dim,
    )

    # --force: 인덱스 초기화
    if args.force:
        clear_index(settings.working_dir_path)

    # LightRAG 인스턴스 생성
    rag = create_lightrag(settings)
    await rag.initialize_storages()

    # 문서 로드
    loader = DocumentLoader(settings)
    if args.mode == "test":
        logger.info("문서 로드 중... (테스트 모드)")
        all_files = loader.get_all_files()
        if not all_files:
            logger.warning(
                "FAQ 데이터 없음: %s", settings.faq_data_dir
            )
            sys.exit(1)
        documents = loader.load_specific_files(all_files[:1])
    else:
        logger.info("문서 로드 중... (전체 모드)")
        documents = loader.load_all()

    if not documents:
        logger.warning("로드된 문서 없음. 종료.")
        sys.exit(1)

    total = len(documents)
    logger.info("총 %d건 인덱싱 시작", total)

    # 배치 인덱싱
    contents = [doc["content"] for doc in documents]
    sources = [doc["source"] for doc in documents]

    logger.info(
        "문서 목록: %s",
        ", ".join(sources[:10])
        + (f" 외 {total - 10}건" if total > 10 else ""),
    )

    try:
        track_id = await rag.ainsert(contents)
        logger.info(
            "배치 인덱싱 완료: %d건 (track_id=%s)",
            total, track_id,
        )
        success_count = total
        fail_count = 0
    except Exception as e:
        logger.error("배치 인덱싱 실패: %s", e)
        success_count = 0
        fail_count = total

    logger.info("=" * 50)
    logger.info(
        "인덱싱 완료: 성공 %d건, 실패 %d건 / 총 %d건",
        success_count, fail_count, total,
    )
    logger.info("로그 파일: %s", log_file)
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
