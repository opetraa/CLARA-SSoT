"""Term SSoT Repository 모듈."""
# src/tractara/ssot/term_ssot_repository.py
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SSOT_TERM_DIR = BASE_DIR / "data" / "ssot" / "terms"

# termType → 서브디렉토리 매핑
_TYPE_SUBDIR: Dict[str, str] = {
    "TERM-CLASS": "class",
    "TERM-REL": "rel",
    "TERM-RULE": "rule",
}


def _term_subdir(term: Dict[str, Any]) -> Path:
    """termType 필드를 읽어 해당 서브디렉토리 경로를 반환한다."""
    term_type = term.get("termType", "TERM-CLASS")
    subdir_name = _TYPE_SUBDIR.get(term_type, "class")
    subdir = SSOT_TERM_DIR / subdir_name
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir


def upsert_terms(terms: List[Dict[str, Any]]) -> None:
    """
    TERM SSoT 저장/갱신.
    termType별 서브디렉토리로 분리 저장:
      data/ssot/terms/class/   ← TERM-CLASS
      data/ssot/terms/rel/     ← TERM-REL
      data/ssot/terms/rule/    ← TERM-RULE

    파일명: {termId 마지막 세그먼트}.json
    예: term:class:operating_temperature → class/operating_temperature.json
    """
    for term in terms:
        term_id: str = term["termId"]
        # termId에서 파일명 세그먼트 추출 (term:class:xxx → xxx)
        filename_stem = term_id.split(":")[-1]
        subdir = _term_subdir(term)
        path = subdir / f"{filename_stem}.json"
        path.write_text(
            json.dumps(term, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def get_all_terms(
    *,
    term_type: Optional[str] = None,
    limit: int = 0,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """
    SSoT에 저장된 TERM JSON을 로드하여 반환합니다.

    Args:
        term_type: 필터링할 termType ("TERM-CLASS", "TERM-REL", "TERM-RULE").
                   None이면 전체 로드.
        limit: 반환할 최대 개수. 0이면 제한 없음.
        offset: 건너뛸 항목 수. limit과 함께 사용하여 배치 로딩 가능.

    Returns:
        TERM JSON 딕셔너리 리스트
    """
    terms: List[Dict[str, Any]] = []
    if not SSOT_TERM_DIR.exists():
        return terms

    # term_type이 지정되면 해당 서브디렉토리만 탐색
    if term_type and term_type in _TYPE_SUBDIR:
        search_dir = SSOT_TERM_DIR / _TYPE_SUBDIR[term_type]
        if not search_dir.exists():
            return terms
        file_iter = search_dir.glob("*.json")
    else:
        file_iter = SSOT_TERM_DIR.rglob("*.json")

    for file_path in sorted(file_iter):
        try:
            with file_path.open("r", encoding="utf-8") as f:
                terms.append(json.load(f))
        except (OSError, ValueError):
            pass

    # offset/limit 적용
    if offset > 0:
        terms = terms[offset:]
    if limit > 0:
        terms = terms[:limit]

    return terms
