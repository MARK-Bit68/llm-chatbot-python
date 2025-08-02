import streamlit as st

# Connect to Neo4j with error handling
def get_graph():
    """Get Neo4j graph connection with error handling"""
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=st.secrets["NEO4J_URI"],
            username=st.secrets["NEO4J_USERNAME"],
            password=st.secrets["NEO4J_PASSWORD"],
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        st.error(f"❌ Neo4j connection failed: {str(e)}")
        st.info("💡 Please install and start Neo4j to use the full RAG capabilities.")
        return None

# Global graph instance
graph = get_graph()
