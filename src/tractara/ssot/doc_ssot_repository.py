"""Doc SSoT Repository 모듈."""
# src/tractara/ssot/doc_ssot_repository.py
import json
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SSOT_DOC_DIR = BASE_DIR / "data" / "ssot" / "docs"
SSOT_DOC_DIR.mkdir(parents=True, exist_ok=True)


def upsert_doc(doc: Dict[str, Any]) -> None:
    """
    DOC SSoT 저장/갱신.
    파일명: {documentId}.json
    """
    doc_id = doc["documentId"]
    path = SSOT_DOC_DIR / f"{doc_id}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
