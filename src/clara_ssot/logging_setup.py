# src/clara_ssot/logging_setup.py
import json
import logging
import sys

from .tracing import get_span_id, get_trace_id


class JsonLogFormatter(logging.Formatter):
    """
    로그를 JSON 한 줄 형태로 출력해주는 포매터.
    trace_id, span_id를 함께 남긴다.
    """

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": getattr(record, "trace_id", get_trace_id()),
            "span_id": getattr(record, "span_id", get_span_id()),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging() -> None:
    """
    루트 로거를 JSON 포맷으로 설정.
    나중에 startup 이벤트에서 한 번만 호출하면 된다.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(handler)
