#!/usr/bin/env python3
"""
Minimal Main Server - Just API endpoints
Absolute minimum to test Railway deployment
"""

import os
from fastapi import FastAPI
import uvicorn

# Create the main FastAPI app
app = FastAPI(title="SupplyGraph Test", version="1.0.0")

# Health check endpoint (Railway requirement)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "minimal server working"}

@app.get("/")
async def root():
    return {"message": "SupplyGraph minimal server is running!", "port": os.environ.get("PORT", "8000")}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Starting minimal server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")