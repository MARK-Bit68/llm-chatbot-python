#!/usr/bin/env python3
"""
Debug Neo4j database and embeddings
"""
import streamlit as st
from llm import embeddings
from graph import graph

def debug_neo4j():
    """Debug Neo4j database and embeddings"""
    print("🔍 Debugging Neo4j Database...")
    
    # Check total SKU nodes
    result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
    print(f"📊 Total SKU nodes: {result[0]['count']}")
    
    # List some SKUs
    result = graph.query("MATCH (sku:SKU) RETURN sku.sku_id, sku.name LIMIT 10")
    print(f"📋 SKUs in database:")
    for row in result:
        print(f"  - {row['sku.sku_id']}: {row['sku.name']}")
    
    # Check embedding dimensions
    result = graph.query("MATCH (sku:SKU) WHERE sku.plotEmbedding IS NOT NULL RETURN sku.sku_id, size(sku.plotEmbedding) as dim LIMIT 5")
    print(f"🔢 Embedding dimensions:")
    for row in result:
        print(f"  - {row['sku.sku_id']}: {row['dim']} dimensions")
    
    # Test embedding generation
    print("🧪 Testing embedding generation...")
    test_text = "Test FMCG product data for embedding generation"
    test_embedding = embeddings.embed_query(test_text)
    print(f"  - Test embedding dimension: {len(test_embedding)}")
    print(f"  - Test embedding first 5 values: {test_embedding[:5]}")

if __name__ == "__main__":
    debug_neo4j() 