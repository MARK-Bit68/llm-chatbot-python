#!/bin/bash

echo "🚀 Deploying FMCG Frontend (React) to Railway"
echo "=============================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install Railway CLI first:"
    echo "npm install -g @railway/cli"
    echo "or"
    echo "curl -fsSL https://railway.app/install.sh | sh"
    exit 1
fi

echo "1️⃣ Checking Railway authentication..."
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway first:"
    railway login
fi

echo ""
echo "2️⃣ Creating new Railway service for frontend..."

# Ask user for backend URL
echo "📝 Please provide your backend URL:"
echo "   Example: https://your-backend-service.railway.app"
read -p "Backend URL: " BACKEND_URL

if [ -z "$BACKEND_URL" ]; then
    echo "❌ Backend URL is required. Exiting..."
    exit 1
fi

echo ""
echo "3️⃣ Initializing new Railway project for frontend..."
railway init

echo ""
echo "4️⃣ Setting up frontend configuration..."

# Copy the frontend-specific railway config
cp railway-ui.toml railway.toml

echo "📋 Frontend configuration:"
cat railway.toml

echo ""
echo "5️⃣ Setting environment variables..."
railway variables set VITE_API_URL="$BACKEND_URL"
railway variables set NODE_ENV="production"
railway variables set VITE_APP_NAME="FMCG Supply Chain Assistant"

echo ""
echo "6️⃣ Building React application..."
npm run build

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix build errors and try again."
    exit 1
fi

echo ""
echo "7️⃣ Deploying to Railway..."
railway up

echo ""
echo "✅ Frontend deployment complete!"
echo ""
echo "🎉 Both services are now deployed!"
echo "=============================================="
echo "📊 Backend (Streamlit):  Your existing URL"
echo "🚀 Frontend (React):     Check Railway dashboard for new URL"
echo "=============================================="
echo ""
echo "📋 Post-deployment checklist:"
echo "✅ Test both UIs work independently"
echo "✅ Verify frontend can connect to backend API"
echo "✅ Check all pages load correctly"
echo "✅ Test chat functionality"
echo "✅ Verify database connections work"