import streamlit as st
import os

# tag::graph[]
from langchain_neo4j import Neo4jGraph

def get_neo4j_config(key, default=""):
    """Get Neo4j config from secrets or environment variables"""
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

graph = Neo4jGraph(
    url=get_neo4j_config("NEO4J_URI"),
    username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
    password=get_neo4j_config("NEO4J_PASSWORD"),
)
#end::graph[]