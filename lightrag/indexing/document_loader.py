"""고객상담 FAQ 문서 로더 모듈

lightrag/data/*.md 파일을 로드하여 LightRAG 인덱싱용 dict 형식으로 반환.
청크 분할은 LightRAG 내부에서 자동 처리.
"""
import logging
from pathlib import Path

from config.settings import Settings

logger = logging.getLogger(__name__)


class DocumentLoader:
    """고객상담 FAQ 문서 로더

    반환 형식: {"content": str, "source": str, "source_type": str}
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def load_all(self) -> list[dict]:
        """전체 FAQ 마크다운 파일 로드

        Returns:
            list[dict]: 문서 목록
        """
        return self._load_markdown(
            self.settings.faq_data_dir, "고객상담FAQ"
        )

    def load_specific_files(
        self, file_paths: list[Path],
    ) -> list[dict]:
        """특정 파일만 로드 (테스트용)

        Args:
            file_paths: 로드할 파일 경로 목록

        Returns:
            list[dict]: 문서 목록
        """
        docs = []
        for file_path in file_paths:
            if not file_path.exists():
                logger.warning("파일 없음: %s", file_path)
                continue

            try:
                content = file_path.read_text(
                    encoding="utf-8"
                )
                if not content.strip():
                    continue

                docs.append({
                    "content": content,
                    "source": str(file_path.name),
                    "source_type": "고객상담FAQ",
                })
            except Exception as e:
                logger.warning(
                    "파일 읽기 실패: %s (%s)",
                    file_path, e,
                )
                continue

        logger.info("[테스트] %d건 로드", len(docs))
        return docs

    def get_all_files(self) -> list[Path]:
        """FAQ 데이터 디렉토리의 모든 마크다운 파일 경로 반환

        Returns:
            list[Path]: 정렬된 파일 경로 목록
        """
        data_dir = self.settings.faq_data_dir
        if not data_dir.exists():
            logger.warning("디렉토리 없음: %s", data_dir)
            return []
        return sorted(data_dir.glob("*.md"))

    def _load_markdown(
        self,
        dir_path: Path,
        source_type: str,
    ) -> list[dict]:
        """마크다운 파일 로드

        Args:
            dir_path: 디렉토리 경로
            source_type: 소스 유형

        Returns:
            list[dict]: 문서 목록
        """
        docs = []
        if not dir_path.exists():
            logger.warning("디렉토리 없음: %s", dir_path)
            return docs

        for md_file in sorted(dir_path.glob("*.md")):
            try:
                content = md_file.read_text(
                    encoding="utf-8"
                )
                if not content.strip():
                    continue

                docs.append({
                    "content": content,
                    "source": str(md_file.name),
                    "source_type": source_type,
                })
            except Exception as e:
                logger.warning(
                    "파일 읽기 실패: %s (%s)",
                    md_file, e,
                )
                continue

        logger.info(
            "[%s] %d건 로드: %s",
            source_type, len(docs), dir_path,
        )
        return docs
