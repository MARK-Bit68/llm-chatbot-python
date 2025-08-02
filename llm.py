import streamlit as st
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings

# Create the LLM
llm = Ollama(
    model="llama2",
    base_url="http://localhost:11434"
)

# Create the Embedding model
embeddings = OllamaEmbeddings(
    model="llama2",
    base_url="http://localhost:11434"
)