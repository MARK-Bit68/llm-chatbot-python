#!/usr/bin/env python3
"""
Test Railway deployment - just print and run server briefly
"""
print("🚀 Railway test starting...")
print("📁 Current directory contents:")
import os
for item in sorted(os.listdir(".")):
    if not item.startswith("."):
        print(f"   {item}")

print("📦 Python version:")
import sys
print(f"   {sys.version}")

print("🔧 Environment variables:")
print(f"   PORT = {os.environ.get('PORT', 'not set')}")
print(f"   RAILWAY_STATIC_URL = {os.environ.get('RAILWAY_STATIC_URL', 'not set')}")

print("🌐 Starting FastAPI server...")
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "test_server_healthy"}

@app.get("/")
def root():
    return {"message": "Railway test successful!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"   Starting on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)