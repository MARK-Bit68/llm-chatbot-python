#!/bin/bash

echo "🚀 Railway Deployment Monitor"
echo "=============================="
echo "⏱️ Checking every minute, timeout after 5 minutes"
echo "🌐 URL: https://llm-chatbot-python-production-d789.up.railway.app"
echo ""

# Function to test the deployment
test_deployment() {
    local attempt=$1
    echo "🔍 Attempt $attempt/5 - $(date '+%H:%M:%S')"
    
    # Quick curl test first (faster than Puppeteer)
    response_code=$(curl -s -o /dev/null -w "%{http_code}" "https://llm-chatbot-python-production-d789.up.railway.app" --max-time 30)
    
    if [ "$response_code" -eq 200 ]; then
        echo "✅ HTTP 200 - Site is responding"
        
        # Check if it's the new React app or old Streamlit
        page_content=$(curl -s "https://llm-chatbot-python-production-d789.up.railway.app" --max-time 30)
        
        if [[ "$page_content" == *"SupplyGraph Analytics Platform"* ]] || [[ "$page_content" == *"Product Explorer"* ]] || [[ "$page_content" == *"Advanced Dashboard"* ]]; then
            echo "🎉 SUCCESS: Modern React UI is LIVE!"
            echo "✅ React app with SupplyGraph integration detected"
            
            # Test health endpoint
            health_response=$(curl -s "https://llm-chatbot-python-production-d789.up.railway.app/health" --max-time 10)
            if [[ "$health_response" == *"healthy"* ]]; then
                echo "💚 Health check: PASSED"
            else
                echo "⚠️ Health check: Not responding properly"
            fi
            
            echo ""
            echo "🌐 Your modern UI is ready at:"
            echo "   https://llm-chatbot-python-production-d789.up.railway.app/"
            
            # Run full Puppeteer test
            echo ""
            echo "📸 Running visual test with Puppeteer..."
            node scripts/test_deployed_only.js
            
            return 0
            
        elif [[ "$page_content" == *"FMCG Supply Chain Assistant"* ]]; then
            echo "⚠️ Still showing old Streamlit app"
            echo "   Railway may still be deploying new version..."
            return 1
            
        else
            echo "❓ Unknown response - checking content..."
            echo "   First 200 chars: ${page_content:0:200}"
            return 1
        fi
        
    elif [ "$response_code" -eq 503 ] || [ "$response_code" -eq 502 ]; then
        echo "🔄 Server restarting (HTTP $response_code) - Railway is likely deploying"
        return 1
        
    elif [ "$response_code" -eq 000 ]; then
        echo "❌ Connection failed - Railway may be building"
        return 1
        
    else
        echo "⚠️ Unexpected response: HTTP $response_code"
        return 1
    fi
}

# Monitor for up to 5 minutes
for i in {1..5}; do
    if test_deployment $i; then
        echo ""
        echo "✅ Deployment monitoring completed successfully!"
        exit 0
    fi
    
    if [ $i -lt 5 ]; then
        echo "⏳ Waiting 60 seconds before next check..."
        echo ""
        sleep 60
    fi
done

echo ""
echo "⏰ TIMEOUT: 5 minutes elapsed"
echo "❌ Modern UI deployment not detected"
echo ""
echo "🔍 Troubleshooting steps:"
echo "  1. Check Railway dashboard for build status"
echo "  2. Look for build errors in Railway logs"
echo "  3. Verify railway.toml is being used"
echo "  4. Check if main.py is the entry point"
echo ""
echo "🌐 Current site still accessible at:"
echo "   https://llm-chatbot-python-production-d789.up.railway.app/"

exit 1