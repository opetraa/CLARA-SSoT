from pathlib import Path
from src.clara_ssot.parsing.pdf_parser import parse_pdf
from src.clara_ssot.normalization.doc_mapper import build_doc_baseline
from src.clara_ssot.normalization.term_mapper import extract_term_candidates

# 1. 테스트용 PDF 경로 (실제 파일이 있는 경로로 수정하세요)
pdf_path = Path("data/sample.pdf")

if not pdf_path.exists():
    print(f"❌ {pdf_path} 파일이 없습니다! 테스트용 PDF를 준비해 주세요.")
else:
    # 2. 파싱 실행 (4단계 로직)
    parsed = parse_pdf(pdf_path)

    # 3. DOC 스키마 변환 (5단계 로직)
    doc_baseline = build_doc_baseline(parsed)

    # 4. 결과 확인
    first_block = doc_baseline["content"][0]
    print("--- 추출 결과 확인 ---")
    print(f"텍스트: {first_block.get('text')[:30]}...")
    print(f"좌표(bbox): {first_block.get('bbox')}")  # 👈 이게 나오면 성공!
    print(f"신뢰도: {first_block.get('extractionConfidence')}")

    # 5. TERM 후보 추출 테스트 (키를 넣지 않음 = 더미 모드)
    term_candidates = extract_term_candidates(parsed, llm_api_key=None)

    print("\n--- TERM 추출 결과 확인 ---")
for c in term_candidates:
    # 👈 "AMP (경년열화 관리 프로그램)"이 나오면 성공!
    print(f"용어: {c.term} ({c.definition_ko})")
