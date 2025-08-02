import streamlit as st

def write_message(role, content, save = True):
    """
    This is a helper function that saves a message to the
     session state and then writes a message to the UI
    """
    # Append to session state
    if save:
        st.session_state.messages.append({"role": role, "content": content})

    # Write to UI
    with st.chat_message(role):
        st.markdown(content)

def get_session_id():
    """Get session ID for Neo4j chat history"""
    try:
        # Try the new import path first
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx().session_id
    except ImportError:
        try:
            # Fallback to old import path
            from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
            return get_script_run_ctx().session_id
        except ImportError:
            # If both fail, return a simple session ID
            return "default_session"
