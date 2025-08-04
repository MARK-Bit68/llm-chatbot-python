import streamlit as st
import os

# Connect to Neo4j with error handling
def get_graph():
    """Get Neo4j graph connection with error handling"""
    try:
        from langchain_neo4j import Neo4jGraph
        
        def get_neo4j_config(key, default=""):
            """Get Neo4j config from environment variables only"""
            return os.getenv(key, default)
        
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        st.error(f"❌ Neo4j connection failed: {str(e)}")
        st.info("💡 Please install and start Neo4j to use the full RAG capabilities.")
        return None

# Initialize graph as None - will be created when needed
_graph = None

def get_graph_instance():
    """Get graph instance, creating it if needed"""
    global _graph
    if _graph is None:
        _graph = get_graph()
    return _graph

# For backward compatibility - but don't call it at import time
def graph():
    return get_graph_instance()
