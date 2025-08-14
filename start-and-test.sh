#!/bin/bash

echo "🚀 Starting FMCG Supply Chain UI Test Suite"

# Function to cleanup background processes
cleanup() {
    echo "🧹 Cleaning up..."
    if [ ! -z "$DEV_PID" ]; then
        kill $DEV_PID 2>/dev/null
    fi
    exit
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Start React dev server in background
echo "📦 Starting React development server..."
npm run dev &
DEV_PID=$!

echo "⏳ Waiting for server to start..."
sleep 15

# Check if server is running
echo "🔍 Checking if server is accessible..."
curl -s http://localhost:3000 > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ React dev server is running"
    
    # Run a simple test to verify the app loads
    echo "🧪 Running basic connectivity test..."
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
    if [ "$RESPONSE" = "200" ]; then
        echo "✅ App responds with HTTP 200"
        echo "🎉 UI test passed - React app is running successfully!"
        echo ""
        echo "📋 Test Results:"
        echo "   ✅ Development server: STARTED"
        echo "   ✅ HTTP connectivity: OK"
        echo "   ✅ Response code: 200"
        echo ""
        echo "🌐 You can now access the app at: http://localhost:3000"
        echo "📱 Test it manually in your browser to verify all features work"
        
        # Keep server running for manual testing
        echo "⏰ Keeping server running for 60 seconds for manual testing..."
        sleep 60
    else
        echo "❌ Server returned HTTP $RESPONSE"
        exit 1
    fi
else
    echo "❌ Server is not accessible"
    exit 1
fi