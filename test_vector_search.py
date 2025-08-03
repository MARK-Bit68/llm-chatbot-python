#!/usr/bin/env python3
"""
Test vector search functionality
"""
import streamlit as st
from langchain_neo4j import Neo4jVector
from llm import embeddings
from graph import graph

def test_vector_search():
    """Test vector search functionality"""
    
    # Create Neo4jVector retriever
    neo4jvector = Neo4jVector.from_existing_index(
        embeddings,
        graph=graph,
        index_name="skuPlots",
        node_label="SKU",
        text_node_property="plot",
        embedding_node_property="plotEmbedding",
        retrieval_query="""
RETURN
    node.plot AS text,
    score,
    {
        title: node.name,
        sku_id: node.sku_id,
        tmdbId: node.sku_id,
        data_type: node.data_type
    } AS metadata
"""
    )
    
    retriever = neo4jvector.as_retriever(search_kwargs={"k": 5})
    
    # Test query
    query = "What are the supply chain details for SKU001?"
    results = retriever.invoke(query)
    
    print(f"Query: {query}")
    print(f"Found {len(results)} results")
    
    for i, doc in enumerate(results):
        print(f"Result {i+1}:")
        print(f"  Content: {doc.page_content[:100]}...")
        print(f"  Metadata: {doc.metadata}")
        print()

if __name__ == "__main__":
    test_vector_search() 