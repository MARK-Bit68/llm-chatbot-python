#!/usr/bin/env python3
"""
SupplyGraph Analytics Platform - React UI + FastAPI Backend
Real backend integration with Neo4j and AI functionality
"""

import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import real backend functionality
try:
    from llm import get_llm
    from monitoring import record_event, timeit
    from solutions.graph import get_graph
    from solutions.tools.cypher_supplygraph import (
        enhanced_cypher_qa, get_dashboard_data, get_product_details,
        get_products_by_group, get_products_by_subgroup, get_products_by_plant,
        get_products_by_storage, get_production_data, get_sales_data,
        get_group_statistics, get_subgroup_statistics, get_plant_statistics,
        get_storage_statistics, get_related_products, search_products,
        get_product_overview
    )
    BACKEND_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Backend modules not available: {e}")
    BACKEND_AVAILABLE = False

# Create the main FastAPI app
app = FastAPI(
    title="SupplyGraph Analytics Platform",
    description="Modern React UI with FastAPI Backend - Real Neo4j and AI Integration",
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

# Pydantic models for API requests
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

class ProductSearchRequest(BaseModel):
    search: str = ""
    group: str = ""
    page: int = 1
    limit: int = 20

# Health check endpoint for Railway
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "3.0.0",
        "services": ["react_ui", "api", "neo4j", "ai"],
        "backend_available": BACKEND_AVAILABLE,
        "port": os.environ.get("PORT", "8000")
    }

# API health check
@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy", 
        "api_version": "3.0.0",
        "backend_available": BACKEND_AVAILABLE
    }

# Real graph overview endpoint
@app.get("/api/graph/overview")
async def graph_overview():
    if not BACKEND_AVAILABLE:
        return {
            "node_statistics": {"total": 0, "products": 0, "categories": 0, "countries": 0},
            "relationship_statistics": {"total": 0, "types": []},
            "status": "backend_unavailable"
        }
    
    try:
        # Get real data from Neo4j
        graph = get_graph()
        dashboard_data = get_dashboard_data(graph)
        
        return {
            "node_statistics": {
                "total": dashboard_data.get("total_nodes", 0),
                "products": dashboard_data.get("total_products", 0),
                "categories": dashboard_data.get("total_groups", 0),
                "countries": dashboard_data.get("total_countries", 0)
            },
            "relationship_statistics": {
                "total": dashboard_data.get("total_relationships", 0),
                "types": dashboard_data.get("relationship_types", [])
            },
            "status": "operational",
            "data_source": "neo4j"
        }
    except Exception as e:
        print(f"Error getting graph overview: {e}")
        return {
            "node_statistics": {"total": 0, "products": 0, "categories": 0, "countries": 0},
            "relationship_statistics": {"total": 0, "types": []},
            "status": "error",
            "error": str(e)
        }

# Real chat endpoint with AI
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not BACKEND_AVAILABLE:
        return {
            "response": "Backend services are not available. Please check the deployment.",
            "status": "backend_unavailable",
            "timestamp": "2025-08-14",
            "session_id": request.session_id
        }
    
    try:
        # Use real AI chat functionality
        graph = get_graph()
        llm = get_llm()
        
        # Get AI response using the real backend
        response = enhanced_cypher_qa(request.message, graph, llm)
        
        return {
            "response": response,
            "status": "success",
            "timestamp": "2025-08-14",
            "session_id": request.session_id,
            "ai_model": "gpt-4.1-nano"
        }
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return {
            "response": f"Error processing your request: {str(e)}",
            "status": "error",
            "timestamp": "2025-08-14",
            "session_id": request.session_id
        }

# Products API endpoint
@app.get("/api/products")
async def get_products(search: str = "", group: str = "", page: int = 1, limit: int = 20):
    if not BACKEND_AVAILABLE:
        return {
            "products": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "totalPages": 0,
            "status": "backend_unavailable"
        }
    
    try:
        graph = get_graph()
        
        if search:
            products = search_products(graph, search)
        elif group:
            products = get_products_by_group(graph, group)
        else:
            # Get all products
            products = get_product_overview(graph)
        
        # Pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_products = products[start_idx:end_idx] if isinstance(products, list) else []
        
        return {
            "products": paginated_products,
            "total": len(products) if isinstance(products, list) else 0,
            "page": page,
            "limit": limit,
            "totalPages": (len(products) + limit - 1) // limit if isinstance(products, list) else 0,
            "status": "success"
        }
    except Exception as e:
        print(f"Error getting products: {e}")
        return {
            "products": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "totalPages": 0,
            "status": "error",
            "error": str(e)
        }

# Analytics endpoints
@app.get("/api/analytics/dashboard")
async def get_analytics_dashboard():
    if not BACKEND_AVAILABLE:
        return {"status": "backend_unavailable", "data": {}}
    
    try:
        graph = get_graph()
        dashboard_data = get_dashboard_data(graph)
        
        return {
            "status": "success",
            "data": dashboard_data
        }
    except Exception as e:
        print(f"Error getting analytics dashboard: {e}")
        return {"status": "error", "error": str(e)}

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
            "backend_available": BACKEND_AVAILABLE,
            "endpoints": {
                "health": "/health",
                "api_docs": "/docs",
                "graph_overview": "/api/graph/overview",
                "chat": "/api/chat",
                "products": "/api/products",
                "analytics": "/api/analytics/dashboard"
            }
        }

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 RAILWAY STARTUP DEBUG")
    print("=" * 50)
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"🐍 Python executable: {sys.executable}")
    print(f"🌐 PORT environment: {os.environ.get('PORT', 'NOT SET')}")
    print(f"📦 FastAPI available: {'✅' if 'fastapi' in str(__import__('fastapi')) else '❌'}")
    print(f"🦄 Uvicorn available: {'✅' if 'uvicorn' in str(__import__('uvicorn')) else '❌'}")
    print(f"🔗 Backend modules available: {'✅' if BACKEND_AVAILABLE else '❌'}")
    print("=" * 50)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)