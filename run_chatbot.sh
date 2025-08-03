#!/bin/bash

# Quick chatbot startup script
# This script starts the FMCG RAG chatbot with basic checks

echo "🚀 Starting FMCG RAG Chatbot..."

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check Neo4j connection and data
echo "🔍 Checking Neo4j and data..."
python3 -c "
import streamlit as st
from langchain_neo4j import Neo4jGraph

try:
    graph = Neo4jGraph(
        url=st.secrets['NEO4J_URI'],
        username=st.secrets['NEO4J_USERNAME'],
        password=st.secrets['NEO4J_PASSWORD'],
    )
    result = graph.query('MATCH (sku:SKU) RETURN count(sku) as count')
    count = result[0]['count']
    print(f'✅ Neo4j connected. Found {count} SKU nodes')
    
    if count == 0:
        print('⚠️  No SKU data found. Use the sidebar to process Excel data.')
    else:
        print('✅ SKU data available for queries.')
        
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    print('Please ensure Neo4j is running: brew services start neo4j')
"

# Start the chatbot
echo "🎯 Starting chatbot..."
echo "🌐 Available at: http://localhost:8501"
echo ""
streamlit run bot.py 