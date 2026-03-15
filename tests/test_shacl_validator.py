# tests/test_shacl_validator.py
import pytest

from tractara.ontology.rdf_serializer import term_json_to_rdf_graph
from tractara.validation.shacl_validator import load_shapes, validate_term


def test_shacl_shapes_load():
    """SHACL shape 파일이 정상 로드되는지 확인"""
    g = load_shapes()
    assert len(g) > 0


def test_valid_term_shacl():
    """영어/한국어 정의가 모두 있는 TERM-CLASS는 패스해야 함"""
    term_json = {
        "termId": "term:class:valid_term",
        "termType": "TERM-CLASS",
        "definition_en": "Valid English",
        "definition_ko": "유효한 한국어",
    }
    g = term_json_to_rdf_graph(term_json)

    conforms, res_graph, res_text = validate_term(g)
    assert conforms is True


def test_invalid_term_missing_definition():
    """필수 필드 누락 시 SHACL 검증 실패해야 함"""
    term_json = {
        "termId": "term:class:invalid_term",
        "termType": "TERM-CLASS",
        "definition_en": "Valid English",
        # definition_ko is missing
    }
    g = term_json_to_rdf_graph(term_json)

    conforms, res_graph, res_text = validate_term(g)
    assert conforms is False
    assert "definition_ko" in res_text
