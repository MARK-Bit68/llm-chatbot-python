#!/usr/bin/env python3
"""
Main Server - Modern React UI + FastAPI Backend
Serves pre-built React app with integrated API
"""

import os
import sys
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create the main FastAPI app first
app = FastAPI(
    title="SupplyGraph Analytics Platform",
    description="Modern React UI with Advanced Graph Analytics API",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Railway (must be available immediately)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["react_ui", "api"],
        "version": "2.0.0"
    }

# Try to import and mount the advanced API
try:
    from advanced_api_server import app as advanced_api_app
    app.mount("/api", advanced_api_app)
    print("✅ Advanced API mounted at /api")
except ImportError as e:
    print(f"⚠️ Could not import advanced API: {e}")
    
    # Create a simple fallback API
    @app.get("/api/health")
    async def api_fallback():
        return {"status": "fallback", "message": "Advanced API not available"}

# Serve React app if dist folder exists
if os.path.exists("dist"):
    # Serve static files
    app.mount("/static", StaticFiles(directory="dist/assets"), name="static")
    
    # Serve React app for all other routes
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # Check if it's an API route
        if full_path.startswith("api/") or full_path.startswith("health"):
            # Let FastAPI handle it
            return {"error": "Route not found"}
        
        # Serve React app
        if os.path.exists(f"dist/{full_path}") and not os.path.isdir(f"dist/{full_path}"):
            return FileResponse(f"dist/{full_path}")
        else:
            # Always serve index.html for SPA routing
            return FileResponse("dist/index.html")
    
    print("✅ React app configured to serve from /dist")
else:
    print("⚠️ React dist folder not found")
    
    @app.get("/")
    async def fallback_home():
        return {
            "message": "SupplyGraph Analytics API",
            "react_build": "not_found",
            "api_docs": "/docs",
            "api_health": "/health"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting SupplyGraph Analytics Platform")
    print(f"🌐 Port: {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📦 Dist folder exists: {os.path.exists('dist')}")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )