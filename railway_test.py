#!/usr/bin/env python3
"""
Railway Startup Test - Verify environment before main app
"""
import os
import sys

print("🧪 Railway Startup Test")
print("=" * 30)

# Test 1: Python version
print(f"🐍 Python version: {sys.version}")

# Test 2: PORT environment
port = os.environ.get("PORT")
print(f"🌐 PORT env var: {port if port else 'NOT SET'}")

# Test 3: Import dependencies
try:
    import fastapi
    print("✅ FastAPI import: OK")
except ImportError as e:
    print(f"❌ FastAPI import: {e}")

try:
    import uvicorn
    print("✅ Uvicorn import: OK")
except ImportError as e:
    print(f"❌ Uvicorn import: {e}")

# Test 4: Create simple FastAPI app
try:
    from fastapi import FastAPI
    test_app = FastAPI()
    
    @test_app.get("/test")
    def test_endpoint():
        return {"status": "test_ok"}
    
    print("✅ FastAPI app creation: OK")
except Exception as e:
    print(f"❌ FastAPI app creation: {e}")

print("=" * 30)
print("🎯 Starting main application...")

# Import and run main app
if __name__ == "__main__":
    import main
