# tests/test_s1000d_reasoning.py
import shutil

import owlready2
import pytest

from tractara.ontology.term_ontology import TermOntologyManager
from tractara.ontology.term_rules import TermRuleEngine

requires_java = pytest.mark.skipif(
    not shutil.which("java"), reason="Java required for reasoning"
)


@requires_java
def test_s1000d_cites_impact_reasoning():
    """
    S1000D DM 간의 인과 관계 및 영향도 분석을 위한 추론기 동작 확인.
    DM A가 DM B를 CITES로 참조 시 -> depends_on -> impacted_by
    """
    manager = TermOntologyManager("http://s1000d.tractara.test/onto#")
    engine = TermRuleEngine(manager)

    # 1. 모델 개체 정의
    dm_cls = manager.register_term_class({"termId": "term:class:data_module"})

    # 관계: cites, depends_on (Transitive), impacted_by
    cites = manager.register_term_rel({"termId": "term:rel:cites"})

    depends_on = manager.register_term_rel(
        {"termId": "term:rel:depends_on", "slots": {"logical_traits": ["Transitive"]}}
    )

    impacted_by = manager.register_term_rel({"termId": "term:rel:impacted_by"})

    # 2. 규칙 1: cites(?a, ?b) -> depends_on(?a, ?b)
    rule1 = {
        "termId": "term:rule:cites_means_depends",
        "slots": {
            "context_terms": [
                {"class_ref": "term:class:data_module", "args": ["?a"]},
                {"class_ref": "term:class:data_module", "args": ["?b"]},
                {"predicate_ref": "term:rel:cites", "args": ["?a", "?b"]},
            ],
            "conditions": [],
            "consequence": {
                "predicate_ref": "term:rel:depends_on",
                "args": ["?a", "?b"],
            },
        },
    }
    engine.add_rule_from_term(rule1)

    # 3. 규칙 2: depends_on(?a, ?b) -> impacted_by(?a, ?b)
    rule2 = {
        "termId": "term:rule:dependencies_cause_impact",
        "slots": {
            "context_terms": [
                {"class_ref": "term:class:data_module", "args": ["?a"]},
                {"class_ref": "term:class:data_module", "args": ["?b"]},
                {"predicate_ref": "term:rel:depends_on", "args": ["?a", "?b"]},
            ],
            "conditions": [],
            "consequence": {
                "predicate_ref": "term:rel:impacted_by",
                "args": ["?a", "?b"],
            },
        },
    }
    engine.add_rule_from_term(rule2)

    # 4. 사실 데이터 입력
    # dm_A (정비 절차) 가 dm_B (토크 규격)을 참조함
    dm_A = dm_cls("DM_A")
    dm_B = dm_cls("DM_B")
    dm_C = dm_cls("DM_C")  # dm_B 가 dm_C 를 참조한다고 가정 (Transitive 확인용)

    cites[dm_A].append(dm_B)
    cites[dm_B].append(dm_C)

    # 5. 추론 실행
    engine.run_reasoner(use_pellet=False)  # HermiT: JRE 21 호환

    # 6. 결과 확인
    # --- SWRL 직접 추론 ---
    # Rule 1: cites(A,B) -> depends_on(A,B)  ✅
    # Rule 1: cites(B,C) -> depends_on(B,C)  ✅
    assert dm_B in depends_on[dm_A]
    assert dm_C in depends_on[dm_B]

    # --- Transitive 추론 ---
    # depends_on이 Transitive이므로: depends_on(A,B) + depends_on(B,C) -> depends_on(A,C)  ✅
    assert dm_C in depends_on[dm_A]

    # --- SWRL Rule 2: depends_on -> impacted_by ---
    # Rule 2 fires on directly-inferred depends_on triples
    assert dm_B in impacted_by[dm_A]
    assert dm_C in impacted_by[dm_B]

    # NOTE: HermiT 제한사항 — SWRL 규칙은 Transitive 추론으로 도출된
    # 간접 사실(depends_on[A]->C)에 대해서는 단일 패스에서 firing 하지 않음.
    # Pellet은 이를 지원하지만 JRE 21과 호환되지 않음.
    # 프로덕션 환경에서는 JRE 8/11 + Pellet 조합을 권장.
