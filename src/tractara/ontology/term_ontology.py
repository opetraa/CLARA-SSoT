"""
Owlready2 기반 TERM 온톨로지 매니저.
TERM-CLASS 및 TERM-REL 데이터를 받아 동적으로 OWL Class와 Property로 매핑합니다.
"""
import types
from typing import Any, Dict, List, Optional

import owlready2


class TermOntologyManager:
    """Tractara 구조화 단어를 OWL Ontology 자원으로 관리합니다."""

    def __init__(self, base_iri: str = "http://tractara.org/ontology/term#"):
        self.base_iri = base_iri
        self.onto = owlready2.get_ontology(base_iri)

        with self.onto:
            # 기본 최상위 개념 클래스 정의
            class TermConcept(owlready2.Thing):
                pass

            self.TermConcept = TermConcept

            # 대표 Annotation Properties 동적 선언
            # pylint: disable=unused-variable
            class definition_en(owlready2.AnnotationProperty):
                pass

            class definition_ko(owlready2.AnnotationProperty):
                pass

            class purpose_en(owlready2.AnnotationProperty):
                pass

            class purpose_ko(owlready2.AnnotationProperty):
                pass

            class scope_en(owlready2.AnnotationProperty):
                pass

            class scope_ko(owlready2.AnnotationProperty):
                pass

            class mechanism_en(owlready2.AnnotationProperty):
                pass

            class mechanism_ko(owlready2.AnnotationProperty):
                pass

            # 분류 정보 체인딩용 DataProperty
            class taxonomy_binding(owlready2.DataProperty):
                range = [str]

            # pylint: enable=unused-variable

    def load(self, path: str) -> None:
        """저장된 온톨로지를 불러옵니다."""
        self.onto.load(path)

    def save(self, path: str, file_format: str = "rdfxml") -> None:
        """온톨로지를 파일로 저장합니다."""
        self.onto.save(file=path, format=file_format)

    def get_local_name(self, term_id: str) -> str:
        """
        termId는 term:class:amp 형태를 갖습니다.
        OWL IRI에서 유효한 Local Name으로 사용하기 위해 콜론을 언더스코어로 변환합니다.
        """
        return term_id.replace(":", "_")

    def get_class(self, term_id: str) -> Optional[Any]:
        """등록된 OWL Class 조회"""
        local_name = self.get_local_name(term_id)
        return getattr(self.onto, local_name, None)

    def get_property(self, term_id: str) -> Optional[Any]:
        """등록된 OWL Property 조회"""
        local_name = self.get_local_name(term_id)
        return getattr(self.onto, local_name, None)

    def register_term_class(self, term_json: Dict[str, Any]) -> Any:
        """
        TERM-CLASS JSON을 OWL Class로 매핑합니다.
        relations에 onto:is_a 가 존재하면, 부모-자식 상속(subclass) 관계로 처리합니다.
        """
        term_id = term_json.get("termId")
        if not term_id:
            return None

        local_name = self.get_local_name(term_id)

        with self.onto:
            # 1. 부모 상속 관계 추적 (onto:is_a 처리)
            parent_classes: List[Any] = [self.TermConcept]
            relations = term_json.get("relations", [])
            for rel in relations:
                if rel.get("relationType") == "onto:is_a":
                    target_id = rel.get("target")
                    if target_id:
                        parent_class = self.get_class(target_id)
                        if parent_class:
                            parent_classes.append(parent_class)

            # 보다 구체적인 부모가 1개 이상 존재하면 기본 TermConcept은 제거
            if len(parent_classes) > 1:
                parent_classes = [p for p in parent_classes if p != self.TermConcept]

            # 2. 클래스 생성 (깨끗한 namespace — 어노테이션을 넣지 않음)
            cls = types.new_class(local_name, tuple(parent_classes))
            cls.namespace = self.onto  # type: ignore[attr-defined]

            # 3. 어노테이션을 클래스 생성 후 별도로 설정
            if term_json.get("definition_en"):
                cls.definition_en = [term_json["definition_en"]]  # type: ignore[attr-defined]
            if term_json.get("definition_ko"):
                cls.definition_ko = [term_json["definition_ko"]]  # type: ignore[attr-defined]

            slots = term_json.get("slots", {})
            for key, val in slots.items():
                if isinstance(val, str) and hasattr(self.onto, key):
                    setattr(cls, key, [val])

            # rdfs:label을 이용한 동의어(어휘) 등록
            labels: List[str] = []
            if term_json.get("headword_en"):
                labels.append(term_json["headword_en"])
            if term_json.get("headword_ko"):
                labels.append(term_json["headword_ko"])
            synonyms = term_json.get("synonyms", {})
            labels.extend(synonyms.get("en", []))
            labels.extend(synonyms.get("ko", []))

            # 중복 제거
            labels = list(dict.fromkeys(filter(None, labels)))
            if labels:
                cls.label = labels  # type: ignore[attr-defined]

        return cls

    def register_term_rel(self, term_json: Dict[str, Any]) -> Any:
        """
        TERM-REL JSON을 OWL ObjectProperty (또는 DataProperty)로 매핑합니다.
        논리적 특성 (Transitive 등)과 domain, range 정보를 반영합니다.
        """
        term_id = term_json.get("termId")
        if not term_id:
            return None

        local_name = self.get_local_name(term_id)

        with self.onto:
            slots = term_json.get("slots", {})

            # DataProperty vs ObjectProperty
            if slots.get("property_type") == "DataProperty":
                parents: List[Any] = [owlready2.DataProperty]
            else:
                parents = [owlready2.ObjectProperty]

            logic_traits = slots.get("logical_traits", [])
            if "Transitive" in logic_traits:
                parents.append(owlready2.TransitiveProperty)
            if "Asymmetric" in logic_traits:
                parents.append(owlready2.AsymmetricProperty)
            if "Symmetric" in logic_traits:
                parents.append(owlready2.SymmetricProperty)

            # 깨끗한 namespace만으로 Property 생성
            prop = types.new_class(local_name, tuple(parents))
            prop.namespace = self.onto  # type: ignore[attr-defined]

            # 라벨 설정
            if term_json.get("headword_en"):
                prop.label = [term_json["headword_en"]]  # type: ignore[attr-defined]

            # Domain / Range 제약 조건
            domain_id = slots.get("domain")
            if domain_id:
                domain_class = self.get_class(domain_id)
                if domain_class:
                    prop.domain = [domain_class]  # type: ignore[attr-defined]

            range_id = slots.get("range")
            if range_id:
                range_class = self.get_class(range_id)
                if range_class:
                    prop.range = [range_class]  # type: ignore[attr-defined]

            # Inverse Property 관계 수립 (양방향 연결)
            inverse_target_id = slots.get("inverse_property")
            if inverse_target_id:
                inverse_prop = self.get_property(inverse_target_id)
                if inverse_prop:
                    prop.inverse_property = inverse_prop  # type: ignore[attr-defined]

        return prop
