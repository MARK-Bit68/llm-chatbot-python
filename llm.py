import streamlit as st
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

def get_openai_key():
    """Get OpenAI API key from secrets or environment variables"""
    try:
        # Try to get from Streamlit secrets first
        return st.secrets["OPENAI_API_KEY"]
    except:
        # Fall back to environment variable
        return os.getenv("OPENAI_API_KEY")

def get_openai_model():
    """Get OpenAI model from secrets or environment variables"""
    try:
        # Try to get from Streamlit secrets first
        return st.secrets["OPENAI_MODEL"]
    except:
        # Fall back to environment variable
        return os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Create the LLM
try:
    llm = ChatOpenAI(
        openai_api_key=get_openai_key(),
        model=get_openai_model(),
        temperature=0.1  # Low temperature for factual, consistent responses
    )
except Exception as e:
    print(f"Warning: Could not create LLM: {e}")
    llm = None

# Create the Embedding model
try:
    embeddings = OpenAIEmbeddings(
        openai_api_key=get_openai_key()
    )
except Exception as e:
    print(f"Warning: Could not create embeddings: {e}")
    embeddings = None