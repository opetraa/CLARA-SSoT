"""
Ontology API 엔드포인트.
런타임 데모 및 테스트 시점에 온톨로지를 명시적으로 로드하고 추론할 수 있도록 지원합니다.
"""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..ontology.term_ontology import TermOntologyManager
from ..ontology.term_rules import TermRuleEngine
from ..ssot.term_ssot_repository import get_all_terms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ontology", tags=["ontology"])

# In-memory singleton for demo
_manager = TermOntologyManager()
_engine = TermRuleEngine(_manager)


class OntologyResponse(BaseModel):
    status: str
    message: str
    inferred_facts: int = 0


@router.post("/load", response_model=OntologyResponse)
async def load_ontology(
    term_type: Optional[str] = Query(
        None,
        description="TERM-CLASS, TERM-REL, or TERM-RULE. 미지정 시 전체 로드.",
    ),
    limit: int = Query(0, ge=0, description="최대 로드 개수. 0이면 제한 없음."),
    offset: int = Query(0, ge=0, description="건너뛸 항목 수 (배치 로딩용)."),
):
    """
    SSoT에서 승격된 TERM 데이터를 읽어 OWL 온톨로지로 로드합니다.

    대규모 TERM 셋에서는 term_type 필터와 limit/offset으로 배치 로딩 가능.
    """
    try:
        terms = get_all_terms(term_type=term_type, limit=limit, offset=offset)
        count_class = 0
        count_rel = 0
        count_rule = 0

        for term in terms:
            t_type = term.get("termType")
            if t_type == "TERM-CLASS":
                res = _manager.register_term_class(term)
                if res:
                    count_class += 1
            elif t_type == "TERM-REL":
                res = _manager.register_term_rel(term)
                if res:
                    count_rel += 1
            elif t_type == "TERM-RULE":
                res = _engine.add_rule_from_term(term)
                if res:
                    count_rule += 1

        return OntologyResponse(
            status="success",
            message=f"Ontology loaded successfully. (Classes: {count_class}, Rels: {count_rel}, Rules: {count_rule})",
            inferred_facts=0,
        )
    except Exception as e:
        logger.error("Failed to load ontology: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/reason", response_model=OntologyResponse)
async def run_reasoning():
    """
    로드된 온톨로지에 대해 Pellet 추론기를 실행합니다.
    """
    try:
        _engine.run_reasoner(use_pellet=True)
        return OntologyResponse(
            status="success",
            message="Reasoning completed successfully.",
            inferred_facts=0,
        )
    except Exception as e:
        logger.error("Failed to run reasoner: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
