# src/clara_ssot/tracing.py
import uuid
from contextvars import ContextVar

# 요청 컨텍스트별로 trace_id, span_id를 들고 있는 변수
trace_id_ctx: ContextVar[str | None] = ContextVar("trace_id", default=None)
span_id_ctx: ContextVar[str | None] = ContextVar("span_id", default=None)


def get_trace_id() -> str:
    """
    현재 컨텍스트의 trace_id를 가져오고,
    없으면 새로 하나 만들어서 저장한다.
    """
    tid = trace_id_ctx.get()
    if tid is None:
        tid = uuid.uuid4().hex
        trace_id_ctx.set(tid)
    return tid


def get_span_id() -> str:
    """
    현재 컨텍스트의 span_id를 가져오고,
    없으면 새로 하나 만들어서 저장한다.
    """
    sid = span_id_ctx.get()
    if sid is None:
        sid = uuid.uuid4().hex[:16]
        span_id_ctx.set(sid)
    return sid


def new_child_span() -> str:
    """
    새로운 span_id를 만들고 현재 컨텍스트에 설정한 뒤 반환.
    (어떤 작업 내부의 하위 작업 구분할 때 사용 가능)
    """
    sid = uuid.uuid4().hex[:16]
    span_id_ctx.set(sid)
    return sid
