#!/usr/bin/env python3
"""
Test script to verify chatbot fixes are working
"""

import requests
import json
import time

# Test the chatbot API directly
def test_chatbot_api():
    base_url = "https://llm-chatbot-python-production.up.railway.app"
    
    print("🔍 Testing chatbot API fixes...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Services: {list(data.get('services', {}).keys())}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Chat endpoint
    print("\n2. Testing chat endpoint...")
    try:
        chat_data = {
            "message": "How many products are there?",
            "session_id": "test_session_123"
        }
        response = requests.post(f"{base_url}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', '')[:200]}...")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Intermediate steps: {data.get('intermediate_steps', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 3: Advanced analytics
    print("\n3. Testing advanced analytics...")
    try:
        chat_data = {
            "message": "Show me profitability patterns across all categories",
            "session_id": "test_session_456"
        }
        response = requests.post(f"{base_url}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', '')[:200]}...")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Intermediate steps: {data.get('intermediate_steps', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4: Risk analysis
    print("\n4. Testing risk analysis...")
    try:
        chat_data = {
            "message": "Analyze inventory risks and provide recommendations",
            "session_id": "test_session_789"
        }
        response = requests.post(f"{base_url}/api/chat", json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data.get('response', '')[:200]}...")
            print(f"   Status: {data.get('status', 'unknown')}")
            print(f"   Intermediate steps: {data.get('intermediate_steps', 0)}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_chatbot_api()
