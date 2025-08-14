#!/usr/bin/env python3
"""
Fixed Main Server - React UI + API with proper static file handling
"""

import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Create the main FastAPI app
app = FastAPI(
    title="SupplyGraph Analytics Platform",
    description="Modern React UI with API Backend",
    version="2.1.0"
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
        "services": ["react_ui", "api"],
        "version": "2.1.0"
    }

# API endpoints
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "api": "operational"}

@app.get("/api/graph/overview")
async def graph_overview():
    return {
        "node_statistics": {"total": 500, "products": 500, "categories": 5},
        "relationship_statistics": {"total": 1200},
        "status": "operational"
    }

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    return {
        "response": "Welcome to SupplyGraph Analytics! The React UI is now working with Railway deployment.",
        "status": "success",
        "timestamp": "2025-08-14"
    }

# Check if React build exists
react_dist_exists = os.path.exists("dist") and os.path.exists("dist/index.html")

if react_dist_exists:
    print("✅ React build found - configuring static file serving")
    
    # Mount static assets with proper paths
    if os.path.exists("dist/assets"):
        app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")
        print("✅ Mounted /assets for React static files")
    
    # Serve React app for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't serve React for API routes
        if full_path.startswith("api") or full_path == "health" or full_path == "docs":
            return {"error": "API route not found", "path": full_path}
        
        # Check if it's a specific file request
        if full_path and "." in full_path.split("/")[-1]:
            file_path = f"dist/{full_path}"
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # Default to serving React index.html for SPA routing
        return FileResponse("dist/index.html", media_type="text/html")
    
    print("✅ React SPA routing configured")
else:
    print("⚠️ React build not found - serving API only")
    
    @app.get("/")
    async def root():
        return {
            "message": "SupplyGraph Analytics API",
            "status": "react_build_missing",
            "api_docs": "/docs",
            "health": "/health"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting SupplyGraph Analytics Platform")
    print(f"🌐 Port: {port}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📦 React build available: {react_dist_exists}")
    
    # Start server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )