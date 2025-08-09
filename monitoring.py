import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

import streamlit as st


def _ensure_trace_initialized() -> None:
    if "monitoring_enabled" not in st.session_state:
        st.session_state.monitoring_enabled = False
    if "trace" not in st.session_state:
        st.session_state.trace = []  # type: ignore[var-annotated]


def enable_monitoring(enable: bool) -> None:
    _ensure_trace_initialized()
    st.session_state.monitoring_enabled = enable


def record_event(event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    _ensure_trace_initialized()
    if not st.session_state.monitoring_enabled:
        return
    event = {
        "id": str(uuid.uuid4()),
        "ts": time.time(),
        "type": event_type,
        "details": details or {},
    }
    st.session_state.trace.append(event)


@contextmanager
def timeit(label: str, extra: Optional[Dict[str, Any]] = None):
    start = time.perf_counter()
    record_event("timer.start", {"label": label, **(extra or {})})
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        record_event("timer.end", {"label": label, "elapsed_ms": round(elapsed_ms, 2), **(extra or {})})


def get_trace() -> List[Dict[str, Any]]:
    _ensure_trace_initialized()
    # Return a shallow copy to avoid external mutation
    return list(st.session_state.trace)


def clear_trace() -> None:
    _ensure_trace_initialized()
    st.session_state.trace = []


def render_debug_panel() -> None:
    """Render a collapsible debug panel with the current trace."""
    _ensure_trace_initialized()
    if not st.session_state.monitoring_enabled:
        return
    with st.expander("🛠️ Debug Trace", expanded=False):
        trace = get_trace()
        if not trace:
            st.info("No trace events yet.")
            return
        for evt in trace[-200:]:  # limit to last 200 events
            ts_readable = time.strftime("%H:%M:%S", time.localtime(evt.get("ts", time.time())))
            st.markdown(f"**[{ts_readable}] {evt.get('type','event')}**")
            details = evt.get("details", {})
            if details:
                st.json(details)


