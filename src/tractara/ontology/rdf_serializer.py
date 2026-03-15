"""
RDFLib 기반 JSON -> RDF 직렬화 유틸리티.
Tractara TERM JSON 스키마를 W3C 표준 RDF 그래프로 변환하여 
시맨틱 검증(SHACL) 및 외부 직렬화에 활용합니다.
"""
from typing import Any, Dict

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, SKOS


def term_json_to_rdf_graph(
    term_json: Dict[str, Any], base_iri: str = "http://tractara.org/ontology/term#"
) -> Graph:
    """TERM JSON 딕셔너리를 입력받아 RDFLib Graph 객체를 반환합니다."""
    g = Graph()
    TERM = Namespace(base_iri)
    # 네임스페이스 바인딩
    g.bind("term", TERM)
    g.bind("skos", SKOS)

    term_id = term_json.get("termId")
    if not term_id:
        return g

    local_name = term_id.replace(":", "_")
    subject = TERM[local_name]

    # 1. 타입 매핑
    term_type = term_json.get("termType")
    if term_type == "TERM-CLASS":
        g.add((subject, RDF.type, URIRef("http://www.w3.org/2002/07/owl#Class")))
    elif term_type == "TERM-REL":
        g.add(
            (subject, RDF.type, URIRef("http://www.w3.org/2002/07/owl#ObjectProperty"))
        )
    elif term_type == "TERM-RULE":
        g.add((subject, RDF.type, URIRef("http://www.w3.org/2003/11/swrl#Imp")))

    # 2. 필수 문자열/어노테이션 추가
    if term_json.get("definition_en"):
        g.add(
            (
                subject,
                TERM.definition_en,
                Literal(term_json["definition_en"], lang="en"),
            )
        )
    if term_json.get("definition_ko"):
        g.add(
            (
                subject,
                TERM.definition_ko,
                Literal(term_json["definition_ko"], lang="ko"),
            )
        )

    headword_en = term_json.get("headword_en")
    if headword_en:
        g.add((subject, RDFS.label, Literal(headword_en, lang="en")))

    headword_ko = term_json.get("headword_ko")
    if headword_ko:
        g.add((subject, RDFS.label, Literal(headword_ko, lang="ko")))

    # 3. 부정 키워드 매핑 (SHACL 충돌 검사용)
    for neg in term_json.get("negatives", []):
        g.add((subject, TERM.negativeKeyword, Literal(neg)))

    # 4. Relations 매핑
    for rel in term_json.get("relations", []):
        rel_type = rel.get("relationType", "")
        target = rel.get("target", "")
        if rel_type and target:
            # skos: 인 경우 내장 네임스페이스 사용
            if rel_type.startswith("skos:"):
                # 예: "skos:broader" -> "broader"
                prop = SKOS[rel_type.split(":")[-1]]  # type: ignore[valid-type, misc]
            else:
                prop = TERM[rel_type.replace(":", "_")]

            target_node = TERM[target.replace(":", "_")]
            g.add((subject, prop, target_node))

    return g


def serialize(graph: Graph, output_format: str = "json-ld") -> str:
    """RDF Graph를 지정된 포맷으로 직렬화하여 반환합니다."""
    return graph.serialize(format=output_format)


def sparql_query(graph: Graph, query_str: str) -> Any:
    """메모리상 그래프에 SPARQL 쿼리를 수행합니다."""
    return list(graph.query(query_str))
