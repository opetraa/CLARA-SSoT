# src/clara_ssot/normalization/term_mapper.py
from dataclasses import dataclass
from typing import Any, Dict, List

from ..parsing.pdf_parser import ParsedDocument
from ..tracing import get_trace_id


@dataclass
class TermCandidate:
    term: str
    definition_en: str | None = None
    definition_ko: str | None = None


def extract_term_candidates(parsed: ParsedDocument) -> List[TermCandidate]:
    # TODO: 진짜 TERM extractor 만들기
    return [
        TermCandidate(
            term="AMP",
            definition_en=None,
            definition_ko="경년열화 관리 프로그램",
        )
    ]


def build_term_baseline_candidates(
    doc_baseline_id: str,
    candidates: List[TermCandidate],
) -> List[Dict[str, Any]]:
    term_jsons: List[Dict[str, Any]] = []
    for c in candidates:
        term_id = f"term:{c.term.lower()}"
        term_jsons.append(
            {
                "type": "term_entry",
                "termId": term_id,
                "term": c.term,
                "lang": "bilingual",
                "headword_en": "Aging Management Program",
                "headword_ko": c.definition_ko or "",
                "definition_en": (c.definition_en or "").strip()
                or "[PENDING_DEFINITION]",
                "definition_ko": c.definition_ko or "",
                "slots": {
                    "purpose_ko": "경년열화 관리를 위한 프로그램 (초안 후보)",
                },
                "examples": [],
                "negatives": [],
                "domain": ["nuclear", "LTO", "safety"],
                "relatedTerms": [],
                "relations": [],
                "taxonomyBindings": [],
                "provenance": {
                    "source": {"docId": doc_baseline_id},
                    "curationStatus": "candidate",
                    "trace_id": get_trace_id(),
                },
            }
        )
    return term_jsons
