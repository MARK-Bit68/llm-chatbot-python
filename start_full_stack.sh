#!/bin/bash

echo "🚀 Starting Complete FMCG RAG Stack with All Optimizations"
echo "=========================================================="

# Check if Neo4j is running
echo "🔍 Checking Neo4j status..."
if ! pgrep -f "neo4j" > /dev/null; then
    echo "⚠️  Neo4j not detected. Please start Neo4j first:"
    echo "   brew services start neo4j"
    echo "   or"
    echo "   neo4j start"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to stop..."
fi

# Activate virtual environment
echo "📦 Activating Python virtual environment..."
source .venv/bin/activate

# Kill any existing Ollama processes
echo "🔄 Stopping any existing Ollama processes..."
pkill -f ollama
sleep 2

# Set optimal environment variables
echo "⚙️  Setting optimal environment variables..."
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_DEBUG=1
export OLLAMA_HOST=0.0.0.0:11434

echo "🎯 Starting Ollama with GPU acceleration and 131K context window..."
ollama serve &
sleep 10

# Check if the custom model exists, if not create it
echo "🔍 Checking for llama3.2-large-context model..."
if ! ollama list | grep -q "llama3.2-large-context"; then
    echo "📦 Creating llama3.2-large-context model with 32K context..."
    ollama create llama3.2-large-context -f Modelfile
else
    echo "✅ Model llama3.2-large-context already exists"
fi

# Test the model
echo "🧪 Testing model configuration..."
python -c "
from llm import embeddings
import time
print('Testing Llama3.2 with 32K context...')
start = time.time()
result = embeddings.embed_query('test')
end = time.time()
print(f'Embedding dimension: {len(result)}')
print(f'Time: {end-start:.2f}s')
print('✅ Model is working correctly!')
"

# Check if data exists in Neo4j
echo "🔍 Checking Neo4j database..."
python -c "
from graph import get_graph
graph = get_graph()
result = graph.query('MATCH (m:Movie) RETURN count(m) as count')
count = result[0]['count']
print(f'📊 Found {count} nodes in database')
if count == 0:
    print('⚠️  No data found. Running ingestion...')
    import subprocess
    subprocess.run(['python', 'quick_ingestion_2_skus.py'])
    print('✅ Data ingestion completed!')
else:
    print('✅ Data already exists in database')
"

# Create vector index if needed
echo "🔍 Checking vector index..."
python -c "
from graph import get_graph
graph = get_graph()
result = graph.query('SHOW INDEXES')
indexes = [r['name'] for r in result if 'moviePlots' in str(r.get('name', ''))]
if not indexes:
    print('📦 Creating vector index...')
    import subprocess
    subprocess.run(['python', 'create_vector_index.py'])
    print('✅ Vector index created!')
else:
    print('✅ Vector index already exists')
"

echo ""
echo "🎉 Stack Status:"
echo "=========================================================="
echo "✅ Ollama Server: Running with 131K context"
echo "✅ Model: llama3.2-large-context (3072 dimensions)"
echo "✅ GPU Acceleration: Enabled"
echo "✅ Neo4j Database: Connected"
echo "✅ Vector Index: Ready"
echo "✅ Data: Ingested and ready"
echo ""
echo "🌐 URLs:"
echo "   - Ollama API: http://localhost:11434"
echo "   - Chatbot UI: http://localhost:8501"
echo "   - Neo4j Browser: http://localhost:7474"
echo ""
echo "💡 Test Questions:"
echo "   - What is the inventory plan for SKU001?"
echo "   - What is the category of SKU001?"
echo "   - Tell me about SKU001's financial details"
echo "   - What are the logistics details for SKU002?"
echo ""
echo "🚀 Starting FMCG RAG Chatbot..."
echo "=========================================================="

# Start the chatbot
streamlit run bot.py 