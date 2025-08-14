#!/bin/bash
echo "🕐 Checking Railway deployment status..."
echo "Deployment started at: $(date)"
echo ""
echo "🌐 Testing URL: https://llm-chatbot-python-production-d789.up.railway.app"
echo ""
echo "⏱️ Waiting 5 minutes for Railway deployment to complete..."
sleep 300

echo ""
echo "🔄 Testing deployment now..."
node scripts/test_deployed_only.js

echo ""
echo "📊 If still showing Streamlit:"
echo "  • Railway may need more time (up to 10 minutes total)"
echo "  • Check Railway dashboard for build progress"
echo "  • Look for any build errors in Railway logs"
echo ""
echo "✅ Expected modern UI features:"
echo "  • React-based interface"
echo "  • SupplyGraph product explorer"
echo "  • Advanced analytics dashboard" 
echo "  • Working /health endpoint"