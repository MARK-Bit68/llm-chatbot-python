#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Start Ollama if not running
if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Start the chatbot
echo "Starting FMCG RAG Chatbot..."
streamlit run bot.py 