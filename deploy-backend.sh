#!/bin/bash

echo "🚀 Deploying FMCG Backend (Streamlit) to Railway"
echo "=============================================="

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    echo "Please install Railway CLI first:"
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
echo "2️⃣ Deploying Streamlit backend..."
echo "Using existing railway.toml configuration"

# Show current railway.toml
echo ""
echo "📋 Current backend configuration:"
cat railway.toml

echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Backend deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Note the backend URL from Railway dashboard"
echo "2. Run ./deploy-frontend.sh to deploy the React UI"
echo "3. Configure VITE_API_URL in frontend environment variables"