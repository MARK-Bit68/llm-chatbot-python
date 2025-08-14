#!/usr/bin/env python3
"""
SupplyGraph Analytics Platform - React UI + FastAPI Backend
Clean deployment for Railway
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
    description="Modern React UI with FastAPI Backend",
    version="3.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "services": ["react_ui", "api"],
        "port": os.environ.get("PORT", "8000")
    }

# Mock API endpoints for React UI
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "api_version": "3.0.0"}

@app.get("/api/graph/overview")
async def graph_overview():
    return {
        "node_statistics": {
            "total": 500,
            "products": 500,
            "categories": 5,
            "countries": 3
        },
        "relationship_statistics": {
            "total": 1200,
            "types": ["BELONGS_TO", "OPERATES_IN", "SUPPLIES"]
        },
        "status": "operational"
    }

@app.post("/api/chat")
async def chat_endpoint(data: dict):
    message = data.get("message", "")
    return {
        "response": f"Welcome to SupplyGraph Analytics! You said: '{message}'. The React UI is now fully operational on Railway.",
        "status": "success",
        "timestamp": "2025-08-14",
        "session_id": data.get("session_id", "default")
    }

# Serve React application
react_dist_path = "dist"
if os.path.exists(react_dist_path) and os.path.exists(os.path.join(react_dist_path, "index.html")):
    # Mount static assets
    if os.path.exists(os.path.join(react_dist_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(react_dist_path, "assets")), name="assets")
    
    # Serve React app for all other routes
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't serve React for API routes
        if full_path.startswith(("api/", "health", "docs")):
            return {"error": "Route not found", "path": full_path}
        
        # Serve specific files if they exist
        if full_path and "." in full_path.split("/")[-1]:
            file_path = os.path.join(react_dist_path, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # Default to React index.html for SPA routing
        return FileResponse(os.path.join(react_dist_path, "index.html"), media_type="text/html")

else:
    @app.get("/")
    async def root():
        return {
            "message": "SupplyGraph Analytics API",
            "status": "react_build_not_found",
            "version": "3.0.0",
            "endpoints": {
                "health": "/health",
                "api_docs": "/docs",
                "graph_overview": "/api/graph/overview"
            }
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)