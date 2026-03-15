"""
Owlready2 기반 SWRL 규칙 빌더 및 추론기 실행 모듈.
JSON 형태로 저장된 TERM-RULE을 동적 파싱하여 SWRL 구문으로 변환하며, 
Java 기반 Pellet 추론기를 호출하여 데이터 그래프 전체에 대한 논리적 연역을 수행합니다.
"""
import logging
from typing import Any, Dict, Optional

import owlready2

from .term_ontology import TermOntologyManager

logger = logging.getLogger(__name__)


class TermRuleEngine:
    """Tractara 구조화 규칙(TERM-RULE)을 SWRL로 변환하고 내장 추론기를 통해 실행합니다."""

    def __init__(self, ontology_manager: TermOntologyManager):
        self.manager = ontology_manager
        self.onto = ontology_manager.onto

    def _build_context_term(self, context_obj: Dict[str, Any]) -> str:
        """
        문맥 조건(Class/Property 제약) 매핑
        예: {"class_ref": "term:class:operating_temperature", "args": ["?m", "?t"]}
        -> "operating_temperature(?m, ?t)"
        """
        class_ref = context_obj.get("class_ref", "")
        if not class_ref:
            class_ref = context_obj.get("predicate_ref", "")

        local_name = self.manager.get_local_name(class_ref)
        args_str = ", ".join(context_obj.get("args", []))
        return f"{local_name}({args_str})"

    def _build_operator_term(self, op_obj: Dict[str, Any]) -> str:
        """
        수학적/논리적 연산자(SWRL built-in) 매핑
        예: {"operator_ref": "greaterThanOrEqual", "args": ["?t", 371]}
        -> "greaterThanOrEqual(?t, 371)"
        """
        builtin = op_obj.get("operator_ref", "")
        # args 파싱 (숫자, 문자열, 파라미터형 구분)
        args = []
        for arg in op_obj.get("args", []):
            if isinstance(arg, str) and not arg.startswith("?"):
                # OWL Individual을 참조할 때 처리 (따옴표 문자열 등)
                args.append(str(arg))
            else:
                args.append(str(arg))

        args_str = ", ".join(args)
        return f"{builtin}({args_str})"

    def add_rule_from_term(self, term_rule_json: Dict[str, Any]) -> Optional[Any]:
        """
        TERM-RULE JSON을 SWRL 문자열로 변환하여 온톨로지에 적용합니다.

        Expected structure in `term_rule_json.slots`:
        {
           "context_terms": [
               {"class_ref": "term:class:austenitic_stainless_steel", "args": ["?m"]},
               {"class_ref": "term:class:operating_temperature", "args": ["?m", "?t"]}
           ],
           "conditions": [
               {"operator_ref": "greaterThanOrEqual", "args": ["?t", 371]}
           ],
           "consequence": {
               "predicate_ref": "term:rel:requires_evaluation_of",
               "args": ["?m", "Creep"]
           }
        }
        """
        term_id = term_rule_json.get("termId")
        if not term_id:
            return None

        slots = term_rule_json.get("slots", {})

        body_parts = []
        # 1. 문맥/조건 파싱 (Context Terms)
        for ctx in slots.get("context_terms", []):
            val = self._build_context_term(ctx)
            if val:
                body_parts.append(val)

        # 2. 연산자 조건 파싱 (Built-ins)
        for cond in slots.get("conditions", []):
            val = self._build_operator_term(cond)
            if val:
                body_parts.append(val)

        body = ", ".join(body_parts)

        # 3. 결론부 파싱 (Consequence)
        conseq = slots.get("consequence", {})
        pred_ref = conseq.get("predicate_ref", "")
        if not pred_ref:
            logger.error("Missing consequence.predicate_ref in RULE: %s", term_id)
            return None

        pred_name = self.manager.get_local_name(pred_ref)
        pred_args = ", ".join(str(a) for a in conseq.get("args", []))
        head = f"{pred_name}({pred_args})"

        swrl_str = f"{body} -> {head}"
        logger.info("Registered SWRL Rule [%s]: %s", term_id, swrl_str)

        # 4. 온톨로지에 규칙 추가
        with self.onto:
            rule = owlready2.Imp()
            try:
                rule.set_as_rule(swrl_str)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Failed to parse SWRL rule: '%s' \nError: %s", swrl_str, e)
                return None

        return rule

    def run_reasoner(self, use_pellet: bool = True):
        """
        전역 온톨로지 상태에 대해 Pellet (또는 HermiT) 추론기를 실행합니다.
        실행 후 온톨로지 내 Individual 들의 관계가 자동 연역/업데이트됩니다.
        """
        logger.info("Starting Reasoning Engine...")
        with self.onto:
            if use_pellet:
                # Pellet Reasoner
                owlready2.sync_reasoner_pellet(
                    infer_property_values=True, infer_data_property_values=True
                )
            else:
                # HermiT Reasoner
                owlready2.sync_reasoner(infer_property_values=True)

        logger.info("Reasoning phase completed.")
