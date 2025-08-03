#!/usr/bin/env python3
"""
Test vector search functionality
"""
import streamlit as st
from llm import embeddings
from graph import get_graph

def test_vector_search():
    """Test vector search directly"""
    print("🔍 Testing Vector Search...")
    
    # Get graph connection
    graph = get_graph()
    if not graph:
        print("❌ No graph connection")
        return
    
    # Test query
    query = "What is the inventory plan for SKU001?"
    print(f"Query: {query}")
    
    try:
        from langchain_neo4j import Neo4jVector
        
        # Create Neo4jVector retriever
        neo4jvector = Neo4jVector.from_existing_index(
            embeddings,
            graph=graph,
            index_name="moviePlots",
            node_label="Movie",
            text_node_property="plot",
            embedding_node_property="plotEmbedding",
            retrieval_query="""
RETURN
    node.plot AS text,
    score,
    {
        title: node.title,
        sku_id: node.sku_id,
        tmdbId: node.tmdbId,
        data_type: node.data_type
    } AS metadata
"""
        )
        
        retriever = neo4jvector.as_retriever(search_kwargs={"k": 5})
        results = retriever.invoke(query)
        
        print(f"\n📊 Vector search found {len(results)} results:")
        for i, doc in enumerate(results):
            print(f"Result {i+1}:")
            print(f"  - SKU: {doc.metadata.get('sku_id', 'Unknown')}")
            print(f"  - Title: {doc.metadata.get('title', 'Unknown')}")
            print(f"  - Score: {doc.metadata.get('score', 'Unknown')}")
            print(f"  - Text preview: {doc.page_content[:100]}...")
            print()
        
        # Check if SKU001 is in results
        sku001_found = any(doc.metadata.get('sku_id') == 'SKU001' for doc in results)
        print(f"✅ SKU001 found in results: {sku001_found}")
        
    except Exception as e:
        print(f"❌ Vector search error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_vector_search() 