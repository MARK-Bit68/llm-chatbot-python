#!/usr/bin/env python3
"""
Debug Neo4j database and embeddings
"""
import streamlit as st
from graph import get_graph
from llm import embeddings

def debug_neo4j():
    """Debug Neo4j database contents"""
    print("🔍 Debugging Neo4j Database...")
    
    # Get graph connection
    graph = get_graph()
    if not graph:
        print("❌ No graph connection")
        return
    
    # Check if nodes exist
    result = graph.query("MATCH (m:Movie) RETURN count(m) as count")
    print(f"📊 Total Movie nodes: {result[0]['count']}")
    
    # List all SKUs
    result = graph.query("MATCH (m:Movie) RETURN m.sku_id, m.title LIMIT 10")
    print(f"📋 SKUs in database:")
    for row in result:
        print(f"  - SKU: {row['m.sku_id']}, Title: {row['m.title']}")
    
    # Check embedding dimensions
    result = graph.query("MATCH (m:Movie) WHERE m.plotEmbedding IS NOT NULL RETURN m.sku_id, size(m.plotEmbedding) as dim LIMIT 5")
    print(f"🔢 Embedding dimensions:")
    for row in result:
        print(f"  - SKU: {row['m.sku_id']}, Dimensions: {row['dim']}")
    
    # Test embedding generation
    print(f"🧪 Testing embedding generation...")
    test_text = "SKU001 inventory plan"
    embedding = embeddings.embed_query(test_text)
    print(f"  - Test embedding dimension: {len(embedding)}")
    print(f"  - Test embedding first 5 values: {embedding[:5]}")

if __name__ == "__main__":
    debug_neo4j() 