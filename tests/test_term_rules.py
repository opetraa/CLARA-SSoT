# tests/test_term_rules.py
import shutil

import owlready2
import pytest

from tractara.ontology.term_ontology import TermOntologyManager
from tractara.ontology.term_rules import TermRuleEngine

requires_java = pytest.mark.skipif(
    not shutil.which("java"), reason="Java required for reasoning"
)


@pytest.fixture
def manager() -> TermOntologyManager:
    return TermOntologyManager("http://tractara.test/rules#")


@pytest.fixture
def engine(manager) -> TermRuleEngine:
    return TermRuleEngine(manager)


def test_swrl_rule_creation(manager: TermOntologyManager, engine: TermRuleEngine):
    """SWRL 생성 및 등록 확인 (구문 검증, ObjectProperty-only)"""
    manager.register_term_class({"termId": "term:class:equipment"})
    manager.register_term_class({"termId": "term:class:hazard"})
    manager.register_term_rel({"termId": "term:rel:exposed_to"})
    manager.register_term_rel({"termId": "term:rel:needs_mitigation"})

    rule_json = {
        "termId": "term:rule:hazard_mitigation",
        "termType": "TERM-RULE",
        "slots": {
            "context_terms": [
                {"class_ref": "term:class:equipment", "args": ["?e"]},
                {"class_ref": "term:class:hazard", "args": ["?h"]},
                {"predicate_ref": "term:rel:exposed_to", "args": ["?e", "?h"]},
            ],
            "conditions": [],
            "consequence": {
                "predicate_ref": "term:rel:needs_mitigation",
                "args": ["?e", "?h"],
            },
        },
    }

    rule = engine.add_rule_from_term(rule_json)
    assert rule is not None


def test_swrl_builtin_string_generation(
    manager: TermOntologyManager, engine: TermRuleEngine
):
    """SWRL 내장 함수(greaterThan 등)가 올바른 문자열로 변환되는지 구문 레벨 검증."""
    result = engine._build_operator_term(
        {"operator_ref": "greaterThanOrEqual", "args": ["?t", 371]}
    )
    assert result == "greaterThanOrEqual(?t, 371)"

    result = engine._build_operator_term(
        {"operator_ref": "lessThan", "args": ["?x", 100]}
    )
    assert result == "lessThan(?x, 100)"


@requires_java
def test_pellet_reasoner_infers_facts(
    manager: TermOntologyManager, engine: TermRuleEngine
):
    """ObjectProperty 기반 SWRL 규칙 추론 확인 (Pellet)"""
    # 1. 온톨로지 모델링
    component_cls = manager.register_term_class({"termId": "term:class:component"})
    defect_cls = manager.register_term_class({"termId": "term:class:defect"})

    manager.register_term_rel({"termId": "term:rel:has_defect"})
    manager.register_term_rel({"termId": "term:rel:requires_review"})

    has_defect = manager.get_property("term:rel:has_defect")
    requires_review = manager.get_property("term:rel:requires_review")

    # 2. 규칙: has_defect(?c, ?d) -> requires_review(?c, ?d)
    rule_json = {
        "termId": "term:rule:defect_review_rule",
        "slots": {
            "context_terms": [
                {"class_ref": "term:class:component", "args": ["?c"]},
                {"class_ref": "term:class:defect", "args": ["?d"]},
                {"predicate_ref": "term:rel:has_defect", "args": ["?c", "?d"]},
            ],
            "conditions": [],
            "consequence": {
                "predicate_ref": "term:rel:requires_review",
                "args": ["?c", "?d"],
            },
        },
    }
    engine.add_rule_from_term(rule_json)

    # 3. 인스턴스 팩트 생성
    comp1 = component_cls("comp_1")
    crack = defect_cls("crack_1")
    has_defect[comp1].append(crack)

    # 4. Pellet 추론 (SWRL 완전 지원)
    engine.run_reasoner(use_pellet=False)  # HermiT: JRE 21 호환, ObjectProperty SWRL 지원

    # 5. 확인: has_defect -> requires_review 추론됨
    assert crack in requires_review[comp1]
