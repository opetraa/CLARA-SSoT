# src/tractara/validation/json_schema_validator.py
import json
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft7Validator, ValidationError

from ..problem_details import MachineReadableError, ProblemDetails
from ..tracing import get_span_id, get_trace_id

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"


class SchemaValidationException(Exception):
    def __init__(self, problem: ProblemDetails) -> None:
        self.problem = problem
        super().__init__(problem.detail)


class SchemaRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, Draft7Validator] = {}

    def load(self) -> None:
        term_schema = json.loads(
            (SCHEMA_DIR / "TERM_baseline_schema.json").read_text(encoding="utf-8")
        )
        doc_schema = json.loads(
            (SCHEMA_DIR / "DOC_baseline_schema.json").read_text(encoding="utf-8")
        )
        self._validators["term"] = Draft7Validator(term_schema)
        self._validators["doc"] = Draft7Validator(doc_schema)

    def _format_path(self, err: ValidationError, instance_path: str) -> str:
        """
        ["content", 0, "sectionLabel"] → "content[0].sectionLabel" 로 변환
        """
        path_elems = list(err.path)
        if not path_elems:
            return instance_path

        segments: list[str] = []
        for pe in path_elems:
            if isinstance(pe, int):
                # 직전에 필드명이 있다고 가정하고 [idx] 붙이기
                if segments:
                    segments[-1] = f"{segments[-1]}[{pe}]"
                else:
                    segments.append(f"[{pe}]")
            else:
                segments.append(str(pe))
        return ".".join(segments)

    def validate(
        self,
        kind: Literal["term", "doc"],
        instance: dict[str, Any],
        instance_path: str,
    ) -> None:
        if kind not in self._validators:
            raise RuntimeError(f"Schema validator for kind='{kind}' is not loaded")

        validator = self._validators[kind]
        errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)

        if not errors:
            return

        problems: list[MachineReadableError] = []
        error_code = f"{kind.upper()}_SCHEMA_VALIDATION_FAILED"

        for err in errors:
            target_path = self._format_path(err, instance_path)

            # jsonschema.ValidationError는 validator_value / instance를 가지고 있어서
            # 어떤 값을 기대했고(actual), 실제로 무엇이 들어왔는지 알 수 있다.
            expected = getattr(err, "validator_value", None)
            actual = err.instance

            problems.append(
                MachineReadableError(
                    code=error_code,
                    target=target_path,
                    detail=err.message,
                    meta={
                        "validator": err.validator,  # "type", "minLength", "enum", ...
                        "expected": expected,  # 기대값 (예: "string", 10, ["A", "B"])
                        "actual": actual,  # 실제 들어온 값 그 자체
                        "path": target_path,  # 사람이 읽기 좋은 표현
                        "errorClass": "system_bug",
                    },
                )
            )

        raise SchemaValidationException(
            problem=ProblemDetails(
                type=f"https://tractara.org/problems/{kind}-schema-validation",
                title=f"{kind.upper()} baseline schema validation failed",
                status=400,
                detail=f"{len(errors)} validation error(s) for {kind}",
                instance=instance_path,
                errors=problems,
                trace_id=get_trace_id(),
                span_id=get_span_id(),
            )
        )


schema_registry = SchemaRegistry()
