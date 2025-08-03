#!/usr/bin/env python3
"""
Debug why vector search isn't working for exact SKU matching
"""
import streamlit as st
from llm import embeddings
from graph import get_graph
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def debug_embeddings():
    """Debug embedding similarity for SKU matching"""
    print("🔍 Debugging Embedding Similarity...")
    
    # Get graph connection
    graph = get_graph()
    if not graph:
        print("❌ No graph connection")
        return
    
    # Test queries
    test_queries = [
        "SKU001",
        "What is the inventory plan for SKU001?",
        "SKU002", 
        "What is the inventory plan for SKU002?",
        "inventory plan",
        "SKU"
    ]
    
    try:
        # Get all SKUs from database
        result = graph.query("MATCH (m:Movie) RETURN m.sku_id, m.plot LIMIT 10")
        skus_in_db = []
        for row in result:
            skus_in_db.append({
                'sku_id': row['m.sku_id'],
                'plot': row['m.plot']
            })
        
        print(f"📊 SKUs in database: {[sku['sku_id'] for sku in skus_in_db]}")
        
        # Test each query
        for query in test_queries:
            print(f"\n🔍 Testing query: '{query}'")
            
            # Get query embedding
            query_embedding = embeddings.embed_query(query)
            print(f"  Query embedding dimension: {len(query_embedding)}")
            
            # Get embeddings for each SKU
            similarities = []
            for sku in skus_in_db:
                sku_embedding = embeddings.embed_query(sku['plot'])
                similarity = cosine_similarity([query_embedding], [sku_embedding])[0][0]
                similarities.append({
                    'sku_id': sku['sku_id'],
                    'similarity': similarity,
                    'plot_preview': sku['plot'][:100] + "..."
                })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            print(f"  📈 Similarity scores:")
            for i, sim in enumerate(similarities):
                print(f"    {i+1}. {sim['sku_id']}: {sim['similarity']:.4f}")
                if i == 0:
                    print(f"       Plot: {sim['plot_preview']}")
            
            # Check if exact SKU match is found
            query_lower = query.lower()
            if 'sku' in query_lower:
                import re
                sku_match = re.search(r'sku(\d+)', query_lower)
                if sku_match:
                    target_sku = f"SKU{sku_match.group(1).upper()}"
                    exact_match = next((s for s in similarities if s['sku_id'] == target_sku), None)
                    if exact_match:
                        rank = next(i for i, s in enumerate(similarities) if s['sku_id'] == target_sku) + 1
                        print(f"  🎯 Exact match '{target_sku}' found at rank #{rank}")
                    else:
                        print(f"  ❌ Exact match '{target_sku}' NOT found in results")
        
        # Test direct SKU queries
        print(f"\n🎯 Testing Direct SKU Queries:")
        for sku in skus_in_db:
            direct_query = f"Tell me about {sku['sku_id']}"
            print(f"\n  Query: '{direct_query}'")
            
            query_embedding = embeddings.embed_query(direct_query)
            similarities = []
            for other_sku in skus_in_db:
                sku_embedding = embeddings.embed_query(other_sku['plot'])
                similarity = cosine_similarity([query_embedding], [sku_embedding])[0][0]
                similarities.append({
                    'sku_id': other_sku['sku_id'],
                    'similarity': similarity
                })
            
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            print(f"    Results:")
            for i, sim in enumerate(similarities):
                print(f"      {i+1}. {sim['sku_id']}: {sim['similarity']:.4f}")
            
            # Check if target SKU is #1
            if similarities[0]['sku_id'] == sku['sku_id']:
                print(f"    ✅ Target SKU is #1!")
            else:
                print(f"    ❌ Target SKU is #{next(i for i, s in enumerate(similarities) if s['sku_id'] == sku['sku_id']) + 1}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_embeddings() 