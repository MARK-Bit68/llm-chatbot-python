#!/usr/bin/env python3
"""
Main Server - Modern React UI + FastAPI Backend
Replaces Streamlit with modern web application
"""

import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import the advanced API server
from advanced_api_server import app as advanced_api_app

def build_react_app():
    """Build the React application for production"""
    try:
        print("📦 Installing dependencies...")
        result = subprocess.run(['npm', 'install'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode != 0:
            print(f"npm install stderr: {result.stderr}")
            return False
        
        print("📦 Building React application...")
        result = subprocess.run(['npm', 'run', 'build'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode != 0:
            print(f"npm build stderr: {result.stderr}")
            return False
            
        print("✅ React build completed successfully")
        return True
    except Exception as e:
        print(f"❌ Build failed: {e}")
        return False

# Create the main FastAPI app
app = FastAPI(
    title="SupplyGraph Analytics Platform",
    description="Modern React UI with Advanced Graph Analytics API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the advanced API under /api
app.mount("/api", advanced_api_app)

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["react_ui", "advanced_api"],
        "version": "2.0.0"
    }

# API status endpoint
@app.get("/api-status")  
async def api_status():
    """Check if the advanced API backend is working"""
    try:
        # Import and check our services
        from core.ai_agent_service import ai_agent_service
        from core.graph_analytics_engine import analytics_engine
        
        agent_status = ai_agent_service.get_agent_status()
        health = analytics_engine.health_check()
        
        return {
            "ai_agent_available": agent_status.get("agent_available", False),
            "graph_engine_status": health.get("overall_status", "unknown"),
            "tools_count": agent_status.get("tools_count", 0)
        }
    except Exception as e:
        return {
            "ai_agent_available": False,
            "graph_engine_status": "error",
            "error": str(e)
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting SupplyGraph Analytics Platform")
    print("📦 Building React application...")
    
    # Build React app first
    build_success = build_react_app()
    
    if build_success and os.path.exists("dist"):
        # Mount React app at root
        app.mount("/", StaticFiles(directory="dist", html=True), name="react")
        print("✅ Modern React UI mounted at /")
    else:
        print("⚠️ React build failed or dist not found")
        
        # Fallback: serve a simple HTML page
        @app.get("/")
        async def fallback_home():
            return {
                "message": "SupplyGraph Analytics API",
                "react_build": "failed",
                "api_docs": "/docs",
                "api_health": "/health"
            }
    
    print(f"🌐 Services starting on port {port}:")
    print(f"   • Modern React UI: http://localhost:{port}/")
    print(f"   • Advanced API: http://localhost:{port}/api/")
    print(f"   • API Documentation: http://localhost:{port}/docs")
    print(f"   • Health Check: http://localhost:{port}/health")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )