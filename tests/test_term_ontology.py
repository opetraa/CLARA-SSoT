# tests/test_term_ontology.py
from typing import Any, Dict

import owlready2
import pytest

from tractara.ontology.term_ontology import TermOntologyManager


@pytest.fixture
def manager() -> TermOntologyManager:
    return TermOntologyManager("http://tractara.test/ontology#")


def test_register_term_class(manager: TermOntologyManager):
    """TERM-CLASS 동적 매핑 기본 검증"""
    term_json = {
        "termId": "term:class:amp",
        "termType": "TERM-CLASS",
        "headword_en": "Aging Management Program",
        "definition_en": "A program...",
        "slots": {"purpose_en": "To manage aging"},
    }

    cls = manager.register_term_class(term_json)
    assert cls is not None
    assert cls.__name__ == "term_class_amp"
    assert issubclass(cls, manager.TermConcept)

    # Check definition
    assert "A program..." in cls.definition_en
    # Check slots
    assert "To manage aging" in cls.purpose_en
    # Check label
    assert "Aging Management Program" in cls.label


def test_register_term_class_hierarchy(manager: TermOntologyManager):
    """상속 관계(onto:is_a) 검증"""
    parent_json = {"termId": "term:class:stainless_steel", "termType": "TERM-CLASS"}
    child_json = {
        "termId": "term:class:316ss",
        "termType": "TERM-CLASS",
        "relations": [
            {"relationType": "onto:is_a", "target": "term:class:stainless_steel"}
        ],
    }

    parent_cls = manager.register_term_class(parent_json)
    child_cls = manager.register_term_class(child_json)

    assert issubclass(child_cls, parent_cls)
    assert parent_cls in child_cls.mro()


def test_register_term_rel(manager: TermOntologyManager):
    """TERM-REL 객체 속성 매핑 검증"""
    rel_json = {
        "termId": "term:rel:requires_inspection",
        "termType": "TERM-REL",
        "headword_en": "Requires Inspection",
        "slots": {"logical_traits": ["Transitive"]},
    }

    prop = manager.register_term_rel(rel_json)
    assert prop is not None
    assert prop.__name__ == "term_rel_requires_inspection"

    import owlready2

    assert issubclass(prop, owlready2.ObjectProperty)
    assert issubclass(prop, owlready2.TransitiveProperty)
    assert "Requires Inspection" in prop.label
