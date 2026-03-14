"""S1000D 파싱 결과 Golden Test — AI 에이전트 자동 채점기.

이 테스트는 AI가 파서를 수정할 때 `make test`로 즉시 채점할 수 있는
"정답지" 역할을 합니다. 각 assertion에 사람이 읽기 좋은 에러 메시지를 포함하여
AI가 에러 로그만 보고 코드를 바로 수정할 수 있도록 합니다.
"""
# tests/test_golden_s1000d.py
import re
from typing import Any, Dict, List


# ----- helper ----------------------------------------------------------
def _content(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    return doc["content"]


# ===== 1. 블록 타입 순서 검증 =============================================
def test_block_types_match_golden(s1000d_doc_json: Dict[str, Any]):
    """전체 블록 순서와 blockType이 황금 정답과 일치하는지 확인."""
    expected = [
        "title",  # Bicycle - Maintenance
        "section",  # preliminaryRqmts
        "section",  # Removal of Wheel (levelledPara)
        "warning",  # Always wear safety goggles.
        "note",  # Ensure the bike is on a stand.
        "note",  # This is an empty step note.
        "procedureStep",  # Use wrench ...
        "section",  # closeRqmts
    ]
    actual = [b["blockType"] for b in _content(s1000d_doc_json)]
    for i, (exp, act) in enumerate(zip(expected, actual)):
        assert act == exp, (
            f"블록 {i}번: expected blockType='{exp}' but got '{act}'. "
            f"블록 텍스트: '{_content(s1000d_doc_json)[i].get('text', '')[:60]}'"
        )
    assert len(actual) == len(expected), (
        f"블록 수 불일치: expected {len(expected)} but got {len(actual)}. "
        f"실제 타입 목록: {actual}"
    )


# ===== 2. note는 절대 paragraph가 되면 안 됨 ==============================
def test_note_never_becomes_paragraph(s1000d_doc_json: Dict[str, Any]):
    """<note> 태그는 반드시 blockType='note'로 매핑되어야 합니다."""
    for i, block in enumerate(_content(s1000d_doc_json)):
        text = block.get("text", "")
        # note 내용이 들어간 블록이 paragraph로 매핑되면 Fail
        if "Ensure the bike is on a stand" in text or "empty step note" in text:
            assert block["blockType"] == "note", (
                f"블록 {i}번: note 태그의 내용이 '{block['blockType']}'로 변환됨. "
                f"반드시 'note'여야 합니다. 텍스트: '{text[:80]}'"
            )


# ===== 3. extensions 필드 금지 ============================================
def test_no_extensions_in_output(s1000d_doc_json: Dict[str, Any]):
    """결과 JSON 최상위에 'extensions' 키가 존재하면 Fail."""
    assert "extensions" not in s1000d_doc_json, (
        "extensions 필드 감지 — 아키텍처 위반. "
        "모든 데이터는 기존 스키마 필드(metadata, content, provenance 등)에 매핑해야 합니다."
    )


# ===== 4. structuredContent 허용 키 검증 ==================================
_ALLOWED_STRUCTURED_KEYS = {
    "conditions",
    "actions",
    "acceptanceCriteria",
    "applicTree",
    "applicRefId",
    "s1000d_dmCode",
}


def test_structured_content_keys_whitelisted(s1000d_doc_json: Dict[str, Any]):
    """structuredContent 내부에 허가된 키만 존재하는지 확인."""
    for i, block in enumerate(_content(s1000d_doc_json)):
        sc = block.get("structuredContent")
        if sc is None:
            continue
        extra_keys = set(sc.keys()) - _ALLOWED_STRUCTURED_KEYS
        assert not extra_keys, (
            f"블록 {i}번 structuredContent에 미허가 키 감지: {extra_keys}. "
            f"허용 키: {_ALLOWED_STRUCTURED_KEYS}"
        )


# ===== 5. relationType 제어 어휘 검증 =====================================
_SCHEMA_RELATION_ENUMS = {
    "CITES",
    "REFERENCES",
    "IS_CITED_BY",
    "SUPERSEDES",
    "IS_SUPERSEDED_BY",
    "SUPPLEMENTS",
    "IS_SUPPLEMENTED_BY",
    "REQUIRES",
    "IS_REQUIRED_BY",
    "RELATED_TO",
    "DERIVES_FROM",
    "HAS_VERSION",
    "IMPLEMENTS",
    "CONTRADICTS",
}
_CUSTOM_PATTERN = re.compile(r"^custom:[a-zA-Z0-9_.-]+$")


def test_relation_types_in_vocabulary(s1000d_doc_json: Dict[str, Any]):
    """relationType이 스키마 enum 또는 custom: 패턴을 따르는지 확인."""
    relations = s1000d_doc_json.get("relations", [])
    for rel in relations:
        rt = rel.get("relationType", "")
        ok = rt in _SCHEMA_RELATION_ENUMS or _CUSTOM_PATTERN.match(rt)
        assert ok, (
            f"미허가 관계 타입: '{rt}'. "
            f"스키마 enum {_SCHEMA_RELATION_ENUMS} 또는 'custom:XXX' 패턴이어야 합니다."
        )


# ===== 6. 빈 proceduralStep 블록 미생성 ==================================
def test_empty_step_suppression(s1000d_doc_json: Dict[str, Any]):
    """빈 <proceduralStep>(텍스트/조건/액션 없음)은 블록으로 생성되면 안 됩니다."""
    for i, block in enumerate(_content(s1000d_doc_json)):
        if block["blockType"] == "procedureStep":
            text = block.get("text", "").strip()
            sc = block.get("structuredContent", {})
            has_conditions = bool(sc.get("conditions"))
            has_actions = bool(sc.get("actions"))
            has_substance = text or has_conditions or has_actions
            assert has_substance, (
                f"빈 절차단계가 블록 {i}번으로 생성됨. "
                f"text='{text}', conditions={sc.get('conditions')}, actions={sc.get('actions')}"
            )


# ===== 7. parentId 참조 무결성 ============================================
def test_parentid_integrity(s1000d_doc_json: Dict[str, Any]):
    """모든 parentId가 동일 문서 내 유효한 blockId를 참조하는지 확인."""
    content = _content(s1000d_doc_json)
    all_ids = {b["blockId"] for b in content}
    for i, block in enumerate(content):
        pid = block.get("parentId")
        if pid is not None:
            assert pid in all_ids, (
                f"고아 블록 발견: 블록 {i}번(blockId={block['blockId']})의 "
                f"parentId='{pid}'가 어떤 blockId와도 매치되지 않음."
            )
