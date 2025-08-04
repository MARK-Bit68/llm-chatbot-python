import streamlit as st
import os
from langchain_neo4j import Neo4jGraph

def create_vector_index():
    """Create vector index for embeddings"""
    
    def get_neo4j_config(key, default=""):
        """Get Neo4j config from environment variables only"""
        return os.getenv(key, default)
    
    # Connect to Neo4j
    graph = Neo4jGraph(
        url=get_neo4j_config("NEO4J_URI"),
        username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
        password=get_neo4j_config("NEO4J_PASSWORD"),
    )
    
    # Drop existing index if it exists
    drop_query = "DROP INDEX skuPlots IF EXISTS"
    graph.query(drop_query)
    print("✅ Dropped existing index")
    
    # Create new vector index
    create_query = """
    CREATE VECTOR INDEX skuPlots 
    FOR (sku:SKU) 
    ON (sku.plotEmbedding) 
    OPTIONS {indexConfig: {
      `vector.dimensions`: 1536,
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