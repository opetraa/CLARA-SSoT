# src/clara_ssot/landing/landing_repository.py
import json
from pathlib import Path
from typing import Any, Dict, List

# BASE_DIR = 프로젝트 루트 (clara-ssot) 까지 올라감
BASE_DIR = Path(__file__).resolve().parent.parent.parent
LANDING_DIR = BASE_DIR / "data" / "landing"
LANDING_DIR.mkdir(parents=True, exist_ok=True)


def save_doc_landing(doc: Dict[str, Any]) -> str:
    """
    DOC baseline JSON을 Landing Zone에 저장.
    파일명: {documentId}.doc.json
    """
    doc_id = doc["documentId"]
    docs_dir = LANDING_DIR / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    path = docs_dir / f"{doc_id}.doc.json"
    path.write_text(json.dumps(doc, ensure_ascii=False,
                    indent=2), encoding="utf-8")
    return doc_id


def save_term_candidates_landing(doc_id: str, terms: List[Dict[str, Any]]) -> None:
    """
    TERM baseline candidates 리스트를 Landing Zone에 저장.
    파일명: {documentId}.terms.json
    """
    terms_dir = LANDING_DIR / "terms"
    terms_dir.mkdir(parents=True, exist_ok=True)
    path = terms_dir / f"{doc_id}.terms.json"
    path.write_text(json.dumps(terms, ensure_ascii=False,
                    indent=2), encoding="utf-8")
