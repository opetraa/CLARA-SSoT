"""PDF 볌크 인제스트 스크립트."""
# !/usr/bin/env python3
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

# 1. 프로젝트 루트 경로 설정 및 sys.path 추가 (Imports 전에 수행해야 함)
# 이 파일은 src/tractara/scripts/ingest_bulk.py 에 위치함
current_file = Path(__file__).resolve()
# src/tractara/scripts/ -> src/tractara/ -> src/ -> root (Tractara)
project_root = current_file.parents[3]
sys.path.append(str(project_root))

# 2. 프로젝트 모듈 임포트 (sys.path 설정 후)
try:
    from tractara.api.pipeline import ingest_single_document
    from tractara.logging_setup import configure_logging
    from tractara.validation.json_schema_validator import schema_registry
except ImportError as e:
    print(f"❌ Error importing project modules: {e}")
    print(f"   Current sys.path: {sys.path}")
    sys.exit(1)

# .env 로드
load_dotenv(override=True)

logger = logging.getLogger("bulk_ingest")


def main():
    """PDF 볌크 인제스트 실행."""
    # 1. 로깅 및 스키마 초기화
    configure_logging()
    schema_registry.load()

    # 2. 데이터 디렉토리 설정
    # 사용자가 지정한 경로: /workspaces/Tractara/data
    # 로컬 개발 환경 호환성을 위해 프로젝트 루트 기준 data 폴더도 확인
    target_dir = Path("/workspaces/Tractara/data")
    if not target_dir.exists():
        target_dir = project_root / "data"

    if not target_dir.exists():
        logger.error("❌ 데이터 디렉토리를 찾을 수 없습니다: %s", target_dir)
        logger.error("프로젝트 루트에 'data' 폴더를 생성하고 PDF 파일을 넣어주세요.")
        sys.exit(1)

    # 3. PDF 파일 탐색
    pdf_files = list(target_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning("⚠️  %s 디렉토리에 PDF 파일이 없습니다.", target_dir)
        return

    logger.info("🚀 일괄 수집 시작: %s 내 %d개 PDF 파일", target_dir, len(pdf_files))

    # 4. 파일별 수집 실행
    success_count = 0
    fail_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info("[%d/%d] 처리 중: %s ...", i, len(pdf_files), pdf_path.name)
        try:
            # 파이프라인 실행
            result = ingest_single_document(pdf_path)

            doc_id = result.get("documentId", "Unknown ID")
            term_count = result.get("promotedTermCount", 0)

            logger.info(
                "✅ 성공: %s (DocID: %s, Terms: %s)", pdf_path.name, doc_id, term_count
            )
            success_count += 1

        except (OSError, RuntimeError, ValueError) as e:
            logger.error("❌ 실패: %s", pdf_path.name)
            logger.error("   이유: %s", str(e))
            fail_count += 1

    # 5. 최종 리포트
    logger.info("=" * 60)
    logger.info("📊 일괄 수집 완료 리포트")
    logger.info("   - 총 파일 수 : %d", len(pdf_files))
    logger.info("   - 성공       : %d", success_count)
    logger.info("   - 실패       : %d", fail_count)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
