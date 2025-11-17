# src/clara_ssot/ssot/term_ssot_repository.py
import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SSOT_TERM_DIR = BASE_DIR / "data" / "ssot" / "terms"
SSOT_TERM_DIR.mkdir(parents=True, exist_ok=True)


def upsert_terms(terms: List[Dict[str, Any]]) -> None:
    """
    TERM SSoT 저장/갱신.
    termId 별로 각각 한 파일로 저장.
    파일명: {termId}.json
    """
    for term in terms:
        term_id = term["termId"]
        path = SSOT_TERM_DIR / f"{term_id}.json"
        path.write_text(
            json.dumps(term, ensure_ascii=False, indent=2), encoding="utf-8"
        )
