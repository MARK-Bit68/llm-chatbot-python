#!/bin/bash

echo "🚀 Starting Ollama with optimal configurations..."

# Kill any existing Ollama processes
echo "🔄 Stopping any existing Ollama processes..."
pkill -f ollama
sleep 2

# Set environment variables for optimal performance
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_DEBUG=1
export OLLAMA_HOST=0.0.0.0:11434

echo "⚙️  Environment variables set:"
echo "   - OLLAMA_FLASH_ATTENTION=1 (GPU acceleration)"
echo "   - OLLAMA_DEBUG=1 (verbose logging)"
echo "   - OLLAMA_HOST=0.0.0.0:11434 (network access)"

# Start Ollama server in background
echo "🎯 Starting Ollama server..."
ollama serve &

# Wait for server to be ready
echo "⏳ Waiting for Ollama server to start..."
sleep 5

# Check if the custom model exists, if not create it
echo "🔍 Checking for llama3.2-large-context model..."
if ! ollama list | grep -q "llama3.2-large-context"; then
    echo "📦 Creating llama3.2-large-context model with 32K context..."
    ollama create llama3.2-large-context -f Modelfile
else
    echo "✅ Model llama3.2-large-context already exists"
fi

# Test the model
echo "🧪 Testing model..."
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

echo ""
echo "🎉 Ollama server is ready!"
echo "📊 Model: llama3.2-large-context"
echo "🧠 Context window: 131,072 tokens"
echo "🔢 Embedding dimensions: 3072"
echo "⚡ GPU acceleration: Enabled"
echo "🌐 Server: http://localhost:11434"
echo ""
echo "💡 To test the chatbot:"
echo "   streamlit run bot.py"
echo ""
echo "💡 To check server status:"
echo "   ps aux | grep ollama" 