# src/clara_ssot/curation/term_curation_service.py
from collections import defaultdict
from typing import Any, Dict, List


def merge_term_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    여러 문서에서 나온 TERM 후보들을 termId 기준으로 병합.
    - definition_en / definition_ko / slots.* 와 같이 부분적으로만 채워진 필드를 합친다.
    """
    grouped: dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for c in candidates:
        grouped[c["termId"]].append(c)

    merged_terms: List[Dict[str, Any]] = []
    for term_id, items in grouped.items():
        base = items[0].copy()
        for other in items[1:]:
            # definition_en/ko 가 비어있거나 [PENDING...]이면 다른 값으로 채워넣기
            if base.get("definition_en", "").startswith("[PENDING") and other.get(
                "definition_en"
            ):
                base["definition_en"] = other["definition_en"]
            if not base.get("definition_ko") and other.get("definition_ko"):
                base["definition_ko"] = other["definition_ko"]

            # slots.* merge (간단히 '없으면 채우기' 방식)
            slots = base.setdefault("slots", {})
            other_slots = other.get("slots", {})
            for k, v in other_slots.items():
                if not slots.get(k) and v:
                    slots[k] = v

        merged_terms.append(base)

    return merged_terms
