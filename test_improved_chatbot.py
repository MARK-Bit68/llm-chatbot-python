#!/usr/bin/env python3
"""
Test the improved chatbot with better SKU prioritization
"""
import streamlit as st
from llm import llm
from graph import get_graph
from langchain_neo4j import Neo4jVector
from llm import embeddings

def test_improved_chatbot():
    """Test the improved chatbot functionality"""
    print("🧪 Testing Improved Chatbot...")
    
    # Get graph connection
    graph = get_graph()
    if not graph:
        print("❌ No graph connection")
        return
    
    # Test query
    query = "What is the inventory plan for SKU001?"
    print(f"Query: {query}")
    
    try:
        # Test vector search with prioritization
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
            print()
        
        # Test prioritization logic
        query_lower = query.lower()
        if 'sku' in query_lower:
            import re
            sku_match = re.search(r'sku(\d+)', query_lower)
            if sku_match:
                target_sku = f"SKU{sku_match.group(1).upper()}"
                print(f"🎯 Target SKU: {target_sku}")
                
                # Simulate prioritization
                exact_matches = [doc for doc in results if doc.metadata.get('sku_id') == target_sku]
                other_results = [doc for doc in results if doc.metadata.get('sku_id') != target_sku]
                prioritized_results = exact_matches + other_results
                
                print(f"✅ Prioritized results:")
                for i, doc in enumerate(prioritized_results):
                    print(f"  {i+1}. SKU: {doc.metadata.get('sku_id')} - {doc.metadata.get('title')}")
        
        # Test improved prompt
        context_parts = []
        for i, doc in enumerate(results):
            context_parts.append(f"=== DATA SET {i+1} ===\nProduct: {doc.metadata.get('title')}\nSKU: {doc.metadata.get('sku_id')}\nDetails: {doc.page_content}\n")
        
        context = "\n".join(context_parts)
        
        prompt = f"""You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. Answer this question based on the provided data.

IMPORTANT: Focus ONLY on the specific SKU mentioned in the question. If the question asks about a particular SKU, only use data for that SKU in your response.

Question: {query}

Available Data: {context}

Instructions:
1. Identify which SKU the question is asking about
2. Use ONLY the data for that specific SKU
3. Provide a clear, detailed answer based on that SKU's data
4. If the question asks about a specific SKU but that SKU's data is not available, say so clearly

Answer:"""

        print(f"\n📝 Testing improved prompt...")
        print(f"Prompt length: {len(prompt)} characters")
        print(f"Context length: {len(context)} characters")
        
        # Test LLM response
        response = llm.invoke(prompt)
        print(f"\n🤖 LLM Response:")
        print(response)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_improved_chatbot() 