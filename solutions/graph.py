import os

# tag::graph[]
from langchain_neo4j import Neo4jGraph

def get_neo4j_config(key, default=""):
    """Get Neo4j config from environment variables only"""
    return os.getenv(key, default)

# Initialize graph as None - will be created when needed
_graph = None

def get_graph():
    """Get graph instance, creating it if needed"""
    global _graph
    if _graph is None:
        try:
            _graph = Neo4jGraph(
                url=get_neo4j_config("NEO4J_URI"),
                username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
                password=get_neo4j_config("NEO4J_PASSWORD"),
            )
        except Exception as e:
            print(f"Error creating graph: {e}")
            _graph = None
    return _graph

# For backward compatibility - but don't call it at import time
def graph():
    return get_graph()
#end::graph[]