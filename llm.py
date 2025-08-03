import streamlit as st
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings

# Create the LLM
llm = Ollama(
    model="llama3.2-large-context",
    base_url="http://localhost:11434"
)

# Create the Embedding model
embeddings = OllamaEmbeddings(
    model="llama3.2-large-context",
    base_url="http://localhost:11434"
)