import streamlit as st
from langchain_neo4j import Neo4jGraph

def create_vector_index():
    """Create vector index for embeddings"""
    
    # Connect to Neo4j
    graph = Neo4jGraph(
        url=st.secrets["NEO4J_URI"],
        username=st.secrets["NEO4J_USERNAME"],
        password=st.secrets["NEO4J_PASSWORD"],
    )
    
    # Drop existing index if it exists
    drop_query = "DROP INDEX moviePlots IF EXISTS"
    graph.query(drop_query)
    print("✅ Dropped existing index")
    
    # Create new vector index
    create_query = """
    CREATE VECTOR INDEX moviePlots 
    FOR (m:Movie) 
    ON (m.plotEmbedding) 
    OPTIONS {indexConfig: {
      `vector.dimensions`: 4096,
      `vector.similarity_function`: 'cosine'
    }}
    """
    
    graph.query(create_query)
    print("✅ Created vector index")
    
    # Wait for index to be online
    print("⏳ Waiting for index to be online...")
    import time
    time.sleep(10)
    
    print("✅ Vector index is ready!")

if __name__ == "__main__":
    create_vector_index() 