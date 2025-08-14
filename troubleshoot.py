#!/usr/bin/env python3
"""
Troubleshoot Railway deployment
"""

import os
import sys

print("🔍 Railway Deployment Troubleshooting")
print("====================================")

print(f"📁 Current working directory: {os.getcwd()}")
print(f"🐍 Python executable: {sys.executable}")
print(f"🌍 Environment variables:")
for key in ['PORT', 'RAILWAY_ENVIRONMENT', 'RAILWAY_SERVICE_NAME', 'NODE_ENV']:
    value = os.environ.get(key, 'NOT SET')
    print(f"   {key}: {value}")

print(f"\n📁 Directory contents:")
for item in sorted(os.listdir('.')):
    if os.path.isfile(item):
        size = os.path.getsize(item)
        print(f"   📄 {item} ({size} bytes)")
    else:
        print(f"   📁 {item}/")

print(f"\n📄 Railway configuration files:")
railway_files = ['railway.toml', 'railway-advanced.toml', 'railway-multi.toml', 'railway-frontend.toml']
for file in railway_files:
    if os.path.exists(file):
        print(f"   ✅ {file} exists")
        with open(file, 'r') as f:
            content = f.read()
            print(f"      Content preview: {content[:200]}...")
    else:
        print(f"   ❌ {file} missing")

print(f"\n📦 React build status:")
dist_exists = os.path.exists('dist')
print(f"   dist/ folder exists: {dist_exists}")
if dist_exists:
    dist_files = os.listdir('dist')
    print(f"   dist/ contents: {', '.join(dist_files)}")

print(f"\n🗂️ Python files:")
python_files = ['main.py', 'bot.py', 'bot_supplygraph.py', 'advanced_api_server.py']
for file in python_files:
    if os.path.exists(file):
        print(f"   ✅ {file} exists")
    else:
        print(f"   ❌ {file} missing")

print(f"\n🚀 What should be running:")
print(f"   Expected start command: python main.py")
print(f"   Health check path: /health")
print(f"   Expected port: 8000 (or $PORT)")

if __name__ == "__main__":
    print(f"\n🧪 Testing imports:")
    try:
        import fastapi
        print(f"   ✅ FastAPI available: {fastapi.__version__}")
    except ImportError as e:
        print(f"   ❌ FastAPI import error: {e}")
    
    try:
        import uvicorn
        print(f"   ✅ Uvicorn available")
    except ImportError as e:
        print(f"   ❌ Uvicorn import error: {e}")
    
    print(f"\n🎯 Next steps:")
    print(f"   1. Check Railway dashboard for actual start command")
    print(f"   2. Verify railway.toml is being used")
    print(f"   3. Check build logs for errors")
    print(f"   4. Ensure main.py is the entry point")