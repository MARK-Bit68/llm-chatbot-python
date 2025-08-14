#!/usr/bin/env python3
"""
Test all imports to see what's failing
"""

import sys
import os

def test_import(module_name, description):
    try:
        exec(f"import {module_name}")
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def main():
    print("🔍 Testing all imports for main.py")
    print("=" * 50)
    
    # Test basic imports
    test_import("fastapi", "FastAPI")
    test_import("uvicorn", "Uvicorn")
    
    print("\n🔍 Testing core services")
    print("=" * 30)
    
    # Test core services
    test_import("core.graph_analytics_engine", "Graph Analytics Engine")
    test_import("core.ai_agent_service", "AI Agent Service")
    
    print("\n🔍 Testing advanced API server")
    print("=" * 35)
    
    # Test advanced API
    try:
        from advanced_api_server import app as advanced_api_app
        print("✅ Advanced API server imports successfully")
    except Exception as e:
        print(f"❌ Advanced API server: {e}")
        
        # Try to debug the specific error
        print("\n🔍 Debugging advanced API import...")
        try:
            import advanced_api_server
        except Exception as debug_e:
            print(f"Detailed error: {debug_e}")
    
    print(f"\n📁 Current directory: {os.getcwd()}")
    print(f"📁 Files in current directory:")
    for item in os.listdir("."):
        if not item.startswith("."):
            print(f"   {item}")

if __name__ == "__main__":
    main()