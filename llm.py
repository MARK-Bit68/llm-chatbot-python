import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from monitoring import record_event

# Optional Streamlit import for session state
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

def get_openai_key():
    """Get OpenAI API key from environment variables only"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ CRITICAL ERROR: OPENAI_API_KEY not found!")
        print("   Please set OPENAI_API_KEY in Railway environment variables")
        print("   This is required for the RAG system to work")
    return api_key

def get_openai_model():
    """Get OpenAI model from environment variables and session overrides.

    Default model is set to 'gpt-4.1-nano'. A Streamlit session override under
    key 'selected_model' will take precedence when present.
    """
    # Streamlit session override if available
    default_model = "gpt-4.1-nano"
    try:
        if STREAMLIT_AVAILABLE and hasattr(st, "session_state") and st.session_state.get("selected_model"):
            return st.session_state["selected_model"]
    except Exception:
        pass
    env_model = os.getenv("OPENAI_MODEL", default_model)
    # Fallback if env/model invalid at runtime
    fallback_order = [env_model, default_model, "gpt-4o-mini", "gpt-4o", "gpt-5-nano"]
    for m in fallback_order:
        if m:
            return m
    return default_model

# Initialize LLM and embeddings as None - will be created when needed
llm = None
embeddings = None
current_model_name = None

def reset_llm():
    global llm
    llm = None


def get_llm():
    """Get LLM, creating it if needed"""
    global llm, current_model_name
    desired_model = get_openai_model()
    # Recreate LLM if model changed
    if llm is not None and current_model_name != desired_model:
        llm = None
    if llm is None:
        try:
            api_key = get_openai_key()
            model = desired_model
            if api_key and model:
                # Prefer low temperature and ample output tokens for models that allow it
                created = False
                last_err = None
                # Attempt with low temperature and larger output tokens first
                for attempt in (
                    {"temperature": 0.2, "max_tokens": 2048},
                    {"temperature": 0.2},
                    {"max_tokens": 2048},
                    {},
                ):
                    try:
                        llm = ChatOpenAI(
                            openai_api_key=api_key,
                            model=model,
                            **attempt,
                        )
                        created = True
                        # Emit signal if we had to drop params
                        if attempt.get("temperature") is None:
                            record_event("llm.temperature_omitted", {"model": model})
                        if attempt.get("max_tokens") is None and "max_tokens" in attempt:
                            record_event("llm.max_tokens_omitted", {"model": model})
                        break
                    except Exception as e:
                        last_err = e
                        # Retry with a simpler parameter set
                        continue
                if not created:
                    raise last_err or RuntimeError("Failed to create LLM")
                print("✅ LLM created successfully")
                record_event("llm.created", {"model": model})
                current_model_name = model
            else:
                print("⚠️ No OpenAI API key or model available for LLM")
                llm = None
        except Exception as e:
            print(f"Warning: Could not create LLM: {e}")
            llm = None
    return llm

def get_embeddings():
    """Get embeddings, creating them if needed"""
    global embeddings
    if embeddings is None:
        try:
            api_key = get_openai_key()
            if api_key:
                embeddings = OpenAIEmbeddings(openai_api_key=api_key)
                print("✅ Embeddings created successfully")
            else:
                print("❌ CRITICAL ERROR: Cannot create embeddings without OpenAI API key")
                print("   The RAG system requires embeddings to function properly")
                print("   Please set OPENAI_API_KEY in Railway environment variables")
                embeddings = None
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not create embeddings: {e}")
            print("   This will prevent the RAG system from working properly")
            embeddings = None
    return embeddings