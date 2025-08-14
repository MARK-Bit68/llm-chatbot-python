#!/bin/bash

echo "🚀 Starting FMCG Supply Chain - Full Stack Development"
echo "=============================================="

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "🧹 Cleaning up processes..."
    if [ ! -z "$STREAMLIT_PID" ]; then
        echo "Stopping Streamlit backend..."
        kill $STREAMLIT_PID 2>/dev/null
    fi
    if [ ! -z "$REACT_PID" ]; then
        echo "Stopping React frontend..."
        kill $REACT_PID 2>/dev/null
    fi
    echo "✅ Cleanup complete"
    exit
}

# Set trap to cleanup on script exit
trap cleanup EXIT INT TERM

echo "1️⃣ Starting Streamlit Backend..."
echo "   Port: 8501"
echo "   URL: http://localhost:8501"
STREAMLIT_CONFIG=.streamlit/config.toml streamlit run bot.py --server.port=8501 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

echo ""
echo "⏳ Waiting for Streamlit to start..."
sleep 8

# Check if Streamlit started successfully
if curl -s http://localhost:8501 > /dev/null; then
    echo "✅ Streamlit backend is running"
else
    echo "❌ Streamlit failed to start"
    exit 1
fi

echo ""
echo "2️⃣ Starting React Frontend..."
echo "   Port: 3000"
echo "   URL: http://localhost:3000"
npm run dev &
REACT_PID=$!

echo ""
echo "⏳ Waiting for React to start..."
sleep 10

# Check if React started successfully
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ React frontend is running"
else
    echo "❌ React failed to start"
    exit 1
fi

echo ""
echo "🎉 Both services are running!"
echo "=============================================="
echo "📊 Streamlit (Original): http://localhost:8501"
echo "🚀 React (New UI):       http://localhost:3000"
echo "=============================================="
echo ""
echo "🧪 Testing URLs:"
echo "   • Original Streamlit Chat: http://localhost:8501"
echo "   • New React Dashboard:     http://localhost:3000"
echo "   • New React Chat:          http://localhost:3000/chat"
echo "   • New React Analytics:     http://localhost:3000/analytics"
echo "   • New React SKU Explorer:  http://localhost:3000/skus"
echo "   • New React Settings:      http://localhost:3000/settings"
echo ""
echo "💡 Pro tip: Open both in different browser tabs to compare!"
echo ""
echo "Press Ctrl+C to stop both services..."

# Keep script running until user interrupts
while true; do
    sleep 1
done