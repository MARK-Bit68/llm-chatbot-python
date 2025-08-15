import time
import uuid
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

# Optional Streamlit import for session state
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

# Fallback storage when Streamlit session_state is unavailable
_fallback_enabled = False
_fallback_trace = []


def _ensure_trace_initialized() -> None:
    global _fallback_enabled, _fallback_trace
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state"):
            # Accessing session_state can raise if not in a Streamlit context
            if "monitoring_enabled" not in st.session_state:
                st.session_state.monitoring_enabled = False
            if "trace" not in st.session_state:
                st.session_state.trace = []  # type: ignore[var-annotated]
        else:
            # Use module-level fallback to avoid crashing in non-Streamlit contexts
            if _fallback_trace is None:
                _fallback_trace = []
    except Exception:
        # Use module-level fallback to avoid crashing in non-Streamlit contexts
        if _fallback_trace is None:
            _fallback_trace = []


def enable_monitoring(enable: bool) -> None:
    global _fallback_enabled
    _ensure_trace_initialized()
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state"):
            st.session_state.monitoring_enabled = enable
        else:
            _fallback_enabled = enable
    except Exception:
        _fallback_enabled = enable


def record_event(event_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    global _fallback_enabled, _fallback_trace
    _ensure_trace_initialized()
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state"):
            if not st.session_state.monitoring_enabled:
                return
            event = {
                "id": str(uuid.uuid4()),
                "ts": time.time(),
                "type": event_type,
                "details": details or {},
            }
            st.session_state.trace.append(event)
        else:
            # Fallback mode (non-Streamlit)
            if not _fallback_enabled:
                return
            _fallback_trace.append({
                "id": str(uuid.uuid4()),
                "ts": time.time(),
                "type": event_type,
                "details": details or {},
            })
    except Exception:
        # Fallback mode (non-Streamlit)
        if not _fallback_enabled:
            return
        _fallback_trace.append({
            "id": str(uuid.uuid4()),
            "ts": time.time(),
            "type": event_type,
            "details": details or {},
        })


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
    global _fallback_trace
    _ensure_trace_initialized()
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state"):
            return list(st.session_state.trace)
        else:
            return list(_fallback_trace)
    except Exception:
        return list(_fallback_trace)


def clear_trace() -> None:
    global _fallback_trace
    _ensure_trace_initialized()
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state"):
            st.session_state.trace = []
        else:
            _fallback_trace = []
    except Exception:
        _fallback_trace = []


def render_debug_panel() -> None:
    """Render a collapsible debug panel with the current trace."""
    _ensure_trace_initialized()
    try:
        if not st.session_state.monitoring_enabled:
            return
    except Exception:
        # Outside Streamlit: nothing to render
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


