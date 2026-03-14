"""Schema Gatekeeper 테스트 — JSON Schema Validator를 E2E로 연결.

AI 에이전트가 파서를 수정했을 때, 결과 JSON이 DOC_baseline_schema.json을
통과하는지 자동으로 검증합니다. 실패 시 SchemaValidationException의
ProblemDetails 에러 메시지가 pytest 출력에 포함되어 AI가
어떤 필드가 문제인지 즉시 파악할 수 있습니다.
"""
# tests/test_schema_gatekeeper.py
from typing import Any, Dict

import pytest

from tractara.validation.json_schema_validator import (
    SchemaRegistry,
    SchemaValidationException,
)


@pytest.fixture(scope="module")
def registry() -> SchemaRegistry:
    """스키마 레지스트리를 로드합니다."""
    reg = SchemaRegistry()
    reg.load()
    return reg


# ===== 1. S1000D 파싱 결과 스키마 통과 ====================================
def test_s1000d_output_passes_schema(
    s1000d_doc_json: Dict[str, Any], registry: SchemaRegistry
):
    """S1000D 파싱 → DOC Baseline JSON → JSON Schema 검증 통과."""
    try:
        registry.validate("doc", s1000d_doc_json, "test://s1000d/golden")
    except SchemaValidationException as exc:
        # AI가 읽기 좋도록 에러 상세를 표시
        errors_summary = "\n".join(
            f"  - [{e.target}] {e.detail}" for e in exc.problem.errors
        )
        pytest.fail(
            f"S1000D DOC JSON이 스키마 검증 실패. "
            f"AI는 파서를 수정하여 아래 위반을 해결해야 합니다:\n{errors_summary}"
        )


# ===== 2. JATS 파싱 결과 스키마 통과 ======================================
def test_jats_output_passes_schema(
    jats_doc_json: Dict[str, Any], registry: SchemaRegistry
):
    """JATS 파싱 → DOC Baseline JSON → JSON Schema 검증 통과."""
    try:
        registry.validate("doc", jats_doc_json, "test://jats/golden")
    except SchemaValidationException as exc:
        errors_summary = "\n".join(
            f"  - [{e.target}] {e.detail}" for e in exc.problem.errors
        )
        pytest.fail(
            f"JATS DOC JSON이 스키마 검증 실패. "
            f"AI는 파서를 수정하여 아래 위반을 해결해야 합니다:\n{errors_summary}"
        )


# ===== 3. 의도적 위반 시 에러 메시지 구체성 검증 ===========================
def test_schema_error_produces_actionable_message(registry: SchemaRegistry):
    """스키마 위반 시 ProblemDetails에 target, detail, meta가 포함되는지 확인."""
    bad_doc: Dict[str, Any] = {
        "documentId": "TEST-BAD",
        "$schema": "https://tractara.org/schemas/doc-baseline/v1.0.0",
        "version": "1.0.0",
        "metadata": {
            # dc:title 누락 (required)
            "dc:type": "TechnicalReport",
            "dc:language": "ko",
        },
        "content": [
            {
                "blockId": "b1",
                "blockType": "INVALID_TYPE",  # enum 위반
                "text": "test",
            }
        ],
    }
    # dc:title 누락이므로 required 에러 발생 예상
    # 하지만 metadata 자체는 있으므로 더 구체적인 에러도 나와야 함
    bad_doc["metadata"].pop("dc:title", None)

    with pytest.raises(SchemaValidationException) as exc_info:
        registry.validate("doc", bad_doc, "test://bad/intentional")

    problem = exc_info.value.problem
    assert problem.errors, "에러 목록이 비어있으면 안 됩니다."

    for err in problem.errors:
        assert err.detail, f"에러 코드 '{err.code}'에 detail 메시지가 없음. " "AI가 문제를 파악할 수 없습니다."
        assert err.meta, (
            f"에러 코드 '{err.code}'에 meta가 없음. "
            "'validator', 'expected', 'actual' 정보가 필요합니다."
        )
