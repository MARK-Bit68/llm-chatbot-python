#!/usr/bin/env python3
"""
Simple deployment test - check if the React app is deployed
"""

import requests
import time

def test_deployment():
    url = "https://llm-chatbot-python-production-d789.up.railway.app"
    
    print("🔍 Testing deployment status...")
    print(f"URL: {url}")
    
    try:
        # Test main page
        response = requests.get(url, timeout=10)
        print(f"Main page status: {response.status_code}")
        
        if response.status_code == 502:
            print("❌ 502 Bad Gateway - Application is not running")
            return False
        
        # Test health endpoint
        health_response = requests.get(f"{url}/health", timeout=10)
        print(f"Health endpoint status: {health_response.status_code}")
        
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"Health data: {health_data}")
            
            if "services" in health_data and "status" in health_data:
                print("✅ FastAPI backend is running!")
                print("✅ React UI should be accessible")
                return True
        
        # Check content to see if it's Streamlit or React
        content = response.text.lower()
        
        if "streamlit" in content or "ui theme" in content:
            print("❌ Still showing Streamlit app")
            return False
        elif "react" in content or "supplygraph" in content or "root" in content:
            print("✅ React app detected")
            return True
        else:
            print(f"❓ Unknown content type. First 200 chars: {content[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_deployment()
    if success:
        print("\n🎉 Deployment successful!")
    else:
        print("\n❌ Deployment not ready yet")