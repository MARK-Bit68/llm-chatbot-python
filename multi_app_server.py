#!/usr/bin/env python3
"""
Multi-App Server - Serves both Streamlit and FastAPI from one deployment
"""

import os
import asyncio
import subprocess
import threading
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

# Import the advanced API server
from advanced_api_server import app as fastapi_app

def run_streamlit():
    """Run Streamlit in a separate thread"""
    import streamlit.web.bootstrap as bootstrap
    import streamlit.web.cli as cli
    
    # Set up Streamlit configuration
    os.environ['STREAMLIT_CONFIG'] = '.streamlit/config.toml'
    
    # Run Streamlit on port 8501
    try:
        cli.main(['run', 'bot_supplygraph.py', '--server.port=8501', '--server.address=0.0.0.0'])
    except SystemExit:
        pass

def build_react_app():
    """Build the React application"""
    try:
        print("📦 Building React application...")
        subprocess.run(['npm', 'install'], check=True, cwd='.')
        subprocess.run(['npm', 'run', 'build'], check=True, cwd='.')
        print("✅ React build completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ React build failed: {e}")
        return False

# Create the main FastAPI app
app = FastAPI(
    title="Multi-App FMCG Platform",
    description="Serves both Modern UI and Advanced API",
    version="1.0.0"
)

# Mount the advanced API
app.mount("/api", fastapi_app)

# Health check for Railway
@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["react", "api", "streamlit"]}

# Main route - serve React app
@app.get("/")
async def serve_react():
    return FileResponse("dist/index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print("🚀 Starting Multi-App FMCG Platform")
    
    # Build React app
    build_success = build_react_app()
    
    if build_success:
        # Serve React static files
        if os.path.exists("dist"):
            app.mount("/", StaticFiles(directory="dist", html=True), name="react")
            print("✅ React app mounted at /")
        else:
            print("⚠️ React dist folder not found, serving API only")
    
    # Start Streamlit in background thread  
    streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
    streamlit_thread.start()
    print("✅ Streamlit started on port 8501")
    
    print(f"🌐 Services available:")
    print(f"   • Modern React UI: http://localhost:{port}/")
    print(f"   • Advanced API: http://localhost:{port}/api/")
    print(f"   • Streamlit UI: http://localhost:{port}/streamlit (proxy needed)")
    
    # Run FastAPI + React on main port
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )