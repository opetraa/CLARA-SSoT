"""
pySHACL 기반 시맨틱 무결성 검증 모듈.
로드된 RDF 그래프가 SHACL 규칙에 부합하는지 평가합니다.
"""
import logging
import os
from typing import List, Tuple

from pyshacl import validate
from rdflib import Graph

from ..problem_details import MachineReadableError, ProblemDetails

logger = logging.getLogger(__name__)

SHAPES_FILE = os.path.join(
    os.path.dirname(__file__), "..", "schemas", "term_shapes.ttl"
)


def load_shapes() -> Graph:
    """SHACL 형태(Shapes) 정의 파일을 로드합니다."""
    g = Graph()
    try:
        g.parse(SHAPES_FILE, format="turtle")
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Failed to load SHACL shapes: %s", e)
    return g


def validate_term(term_rdf_graph: Graph) -> Tuple[bool, Graph, str]:
    """
    RDF 데이터 그래프를 pySHACL을 통해 검증합니다.

    Returns:
        conforms (bool): 검증 통과 여부
        results_graph (Graph): 검증 결과 그래프
        results_text (str): 텍스트 형태의 리포트
    """
    shapes_graph = load_shapes()

    if len(shapes_graph) == 0:
        logger.warning("Empty SHACL shapes graph, skipping semantic validation.")
        return True, Graph(), "No shapes loaded."

    conforms, results_graph, results_text = validate(
        term_rdf_graph,
        shacl_graph=shapes_graph,
        inference="rdfs",
        abort_on_first=False,
        meta_shacl=False,
        advanced=True,
        debug=False,
    )

    return conforms, results_graph, results_text


def get_validation_report(
    term_id: str, conforms: bool, results_text: str
) -> List[ProblemDetails]:
    """
    검증 실패 시 FastAPI가 응답할 수 있는 ProblemDetails 에러 포맷으로 변환합니다.
    """
    if conforms:
        return []

    error = MachineReadableError(
        code="SHACL_SEMANTIC_VALIDATION_FAILED",
        target=term_id,
        detail="The semantic relationships or logical integrity of the term violates defined shapes.",
        meta={"shacl_report": results_text, "errorClass": "system_bug"},
    )

    prob = ProblemDetails(
        type="https://tractara.org/problems/term-shacl-validation",
        title="SHACL Ontology Semantic Violation",
        status=422,
        detail="The ontology logic provided does not conform to the SHACL shapes defined for this domain.",
        instance=term_id,
        trace_id="",
        span_id="",
        errors=[error],
    )
    return [prob]
