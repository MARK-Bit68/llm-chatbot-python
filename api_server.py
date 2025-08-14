# FastAPI Backend - Uses your extracted AI logic
# This is what the React app should call

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from typing import Optional

# Import your extracted AI service
from core_ai_service import ai_service

app = FastAPI(
    title="FMCG Supply Chain API",
    description="API for FMCG Supply Chain Assistant",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local React dev
        "https://*.railway.app",   # Railway deployments
        "*"  # For development - restrict in production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_endpoint(chat_message: ChatMessage):
    """Chat with AI assistant using your existing logic"""
    result = ai_service.chat_with_ai(chat_message.message)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/api/dashboard")
async def dashboard_endpoint():
    """Get dashboard data from Neo4j"""
    result = ai_service.get_dashboard_data()
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/api/skus")
async def skus_endpoint(
    sku_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """Get SKU data with optional filtering"""
    result = ai_service.get_sku_data(sku_id=sku_id, category=category, limit=limit)
    
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result

@app.get("/api/health")
async def health_endpoint():
    """Health check for all services"""
    return ai_service.health_check()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "FMCG Supply Chain API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )