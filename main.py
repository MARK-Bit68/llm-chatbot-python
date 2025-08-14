#!/usr/bin/env python3
"""
Simple Main Server - Just React UI + Basic API
No complex dependencies - should deploy easily to Railway
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create the main FastAPI app
app = FastAPI(
    title="SupplyGraph Analytics Platform",
    description="Modern React UI with Basic API",
    version="2.0.1"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (Railway requirement)
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "services": ["react_ui", "basic_api"],
        "version": "2.0.1",
        "mode": "simple"
    }

# Basic API endpoints
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "api": "basic"}

@app.get("/api/status")
async def api_status():
    return {
        "status": "operational",
        "features": ["react_ui", "basic_api"],
        "complex_ai": "disabled_for_deployment"
    }

# Mock endpoints for the React UI to work
@app.get("/api/graph/overview")
async def mock_graph_overview():
    return {
        "node_statistics": {"total": 100, "products": 50, "categories": 5},
        "relationship_statistics": {"total": 200},
        "status": "mock_data"
    }

@app.post("/api/chat")
async def mock_chat(data: dict):
    return {
        "response": "This is a mock response. Full AI features will be available once dependencies are resolved.",
        "status": "mock",
        "timestamp": "2025-08-14"
    }

# Serve React app if dist folder exists
if os.path.exists("dist"):
    print("✅ Found dist folder - configuring React app serving")
    
    # Mount static assets
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
    
    # Handle all other routes for React SPA
    @app.get("/{full_path:path}")
    async def serve_react(full_path: str):
        # API routes should not serve React
        if full_path.startswith("api/") or full_path == "health":
            return {"error": "API route not found"}
        
        # Check if specific file exists
        file_path = f"dist/{full_path}"
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # Default to index.html for SPA routing
        return FileResponse("dist/index.html")
    
    print("✅ React app configured to serve from /dist")
else:
    print("⚠️ React dist folder not found")
    
    @app.get("/")
    async def fallback_home():
        return {
            "message": "SupplyGraph Analytics API",
            "status": "no_react_build",
            "api_docs": "/docs",
            "api_health": "/health"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting SupplyGraph Analytics Platform (Simple Mode)")
    print(f"🌐 Port: {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📦 Dist folder exists: {os.path.exists('dist')}")
    print("🔧 Mode: Simple (no AI dependencies)")
    
    # Start the server
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )