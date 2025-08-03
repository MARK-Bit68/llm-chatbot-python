#!/usr/bin/env python3
"""
Debug why vector search isn't working for exact SKU matching
"""
import streamlit as st
from llm import embeddings
from graph import graph
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def debug_embeddings():
    """Debug embeddings in Neo4j database"""
    print("🔍 Debugging Embeddings...")
    
    # Check total SKU nodes with embeddings
    result = graph.query("MATCH (sku:SKU) WHERE sku.plotEmbedding IS NOT NULL RETURN count(sku) as count")
    print(f"📊 Total SKU nodes with embeddings: {result[0]['count']}")
    
    # List some SKUs with embeddings
    result = graph.query("MATCH (sku:SKU) WHERE sku.plotEmbedding IS NOT NULL RETURN sku.sku_id, sku.plot LIMIT 10")
    print(f"📋 SKUs with embeddings:")
    for row in result:
        print(f"  - {row['sku.sku_id']}: {row['sku.plot'][:100]}...")
    
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
    debug_embeddings() 