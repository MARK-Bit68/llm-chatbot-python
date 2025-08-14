#!/bin/bash

# Enhanced FMCG SOP Dataset - Memgraph Setup Script
# This script helps set up Memgraph and run the FMCG graph analyzer

echo "🚀 Enhanced FMCG SOP Dataset - Memgraph Setup"
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if Memgraph is already running
if docker ps | grep -q memgraph; then
    echo "✅ Memgraph is already running"
else
    echo "🐳 Starting Memgraph..."
    docker run -d \
        --name memgraph-fmcg \
        -p 7687:7687 \
        -p 7444:7444 \
        -p 3000:3000 \
        memgraph/memgraph-platform
    
    echo "⏳ Waiting for Memgraph to start..."
    sleep 10
    
    # Check if Memgraph started successfully
    if docker ps | grep -q memgraph; then
        echo "✅ Memgraph started successfully"
    else
        echo "❌ Failed to start Memgraph"
        exit 1
    fi
fi

# Check if Python script exists
if [ ! -f "memgraph_fmcg_analyzer.py" ]; then
    echo "❌ memgraph_fmcg_analyzer.py not found in current directory"
    exit 1
fi

# Check if Excel file exists
if [ ! -f "Enhanced_FMCG_SOP_Dataset.xlsx" ]; then
    echo "❌ Enhanced_FMCG_SOP_Dataset.xlsx not found in current directory"
    echo "   Please ensure the Excel file is in the same directory as this script"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install pandas openpyxl gqlalchemy

# Run the analyzer
echo "🔍 Running FMCG Graph Analyzer..."
python memgraph_fmcg_analyzer.py

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Useful commands:"
echo "   - Stop Memgraph: docker stop memgraph-fmcg"
echo "   - Start Memgraph: docker start memgraph-fmcg"
echo "   - Remove Memgraph: docker rm memgraph-fmcg"
echo "   - View logs: docker logs memgraph-fmcg"
echo ""
echo "🌐 Access points:"
echo "   - Memgraph Lab: http://localhost:3000"
echo "   - Memgraph Database: localhost:7687"
echo ""
echo "💡 Tips:"
echo "   - Memgraph Lab will open automatically in your browser"
echo "   - Use the sample queries provided in the output above"
echo "   - Explore the graph structure visually in Memgraph Lab"
