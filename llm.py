import streamlit as st
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Create the LLM
llm = ChatOpenAI(
    openai_api_key=st.secrets["OPENAI_API_KEY"],
    model="gpt-4o-mini"
)

# Create the Embedding model
embeddings = OpenAIEmbeddings(
    openai_api_key=st.secrets["OPENAI_API_KEY"]
)