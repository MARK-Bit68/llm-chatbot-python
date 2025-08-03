#!/bin/bash

# Full stack startup script for FMCG RAG Chatbot
# This script starts all required services and components

echo "🚀 Starting FMCG RAG Chatbot Full Stack..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Check if Neo4j is running
echo "🔍 Checking Neo4j status..."
if ! brew services list | grep -q "neo4j.*started"; then
    echo "🔄 Starting Neo4j..."
    brew services start neo4j
    echo "⏳ Waiting for Neo4j to start..."
    sleep 10
else
    echo "✅ Neo4j is already running"
fi

# Check Neo4j connection
echo "🔗 Testing Neo4j connection..."
python3 -c "
import streamlit as st
from langchain_neo4j import Neo4jGraph

try:
    graph = Neo4jGraph(
        url=st.secrets['NEO4J_URI'],
        username=st.secrets['NEO4J_USERNAME'],
        password=st.secrets['NEO4J_PASSWORD'],
    )
    graph.query('RETURN 1 as test')
    print('✅ Neo4j connection successful')
except Exception as e:
    print(f'❌ Neo4j connection failed: {e}')
    exit(1)
"

# Check if data exists
echo "📊 Checking existing data..."
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
    sku_count = result[0]['count']
    print(f'📈 Found {sku_count} SKU nodes in database')
    
    if sku_count == 0:
        print('⚠️  No SKU data found. You may need to process Excel data first.')
    else:
        print('✅ SKU data found in database')
        
    # Check vector index
    result = graph.query('SHOW INDEXES')
    indexes = [r['name'] for r in result if 'skuPlots' in str(r.get('name', ''))]
    if indexes:
        print(f'✅ Vector index found: {indexes[0]}')
    else:
        print('⚠️  Vector index not found. You may need to create it.')
        
except Exception as e:
    print(f'❌ Error checking data: {e}')
"

# Check if Ollama is running
echo "🤖 Checking Ollama status..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "🔄 Starting Ollama..."
    ollama serve &
    echo "⏳ Waiting for Ollama to start..."
    sleep 5
else
    echo "✅ Ollama is already running"
fi

# Check if required models are available
echo "📋 Checking required models..."
if ! ollama list | grep -q "llama2"; then
    echo "📥 Pulling llama2 model..."
    ollama pull llama2
else
    echo "✅ llama2 model is available"
fi

# Start the chatbot
echo "🎯 Starting FMCG RAG Chatbot..."
echo "🌐 The chatbot will be available at: http://localhost:8501"
echo "📊 Neo4j Browser available at: http://localhost:7474"
echo ""
echo "💡 Tips:"
echo "  - Use the sidebar to upload and process Excel data"
echo "  - Create vector index for similarity search"
echo "  - Try sample questions about your FMCG data"
echo ""
echo "🔄 Starting Streamlit..."
streamlit run bot.py 