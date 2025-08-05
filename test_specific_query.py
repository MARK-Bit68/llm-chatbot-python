#!/usr/bin/env python3
"""
Test the specific query that's failing in Streamlit
"""

import os
import toml

def setup_test_environment():
    """Setup the test environment similar to Streamlit"""
    print("🔧 Setting up test environment...")
    
    # Try to read secrets from .streamlit/secrets.toml
    try:
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if os.path.exists(secrets_path):
            with open(secrets_path, "r") as f:
                content = f.read()
                # Parse the key=value format manually
                for line in content.split('\n'):
                    if line.strip() and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
                        print(f"✅ {key} found in secrets.toml")
        else:
            print("⚠️ secrets.toml not found")
    except Exception as e:
        print(f"❌ Error reading secrets: {e}")

def test_specific_query():
    """Test the specific query that's failing in Streamlit"""
    print("\n🧪 Testing specific query: 'what skus are in the master data'")
    print("=" * 60)
    
    try:
        from solutions.agent import generate_response, reset_agent
        
        # Reset agent to ensure fresh state
        reset_agent()
        print("✅ Agent reset successfully")
        
        # Test the specific query
        query = "what skus are in the master data"
        print(f"🔍 Testing query: '{query}'")
        
        response = generate_response(query)
        print(f"✅ Response received: {response[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    setup_test_environment()
    success = test_specific_query()
    
    if success:
        print("\n🎉 SUCCESS: Query works correctly!")
    else:
        print("\n❌ FAILURE: Query failed!") 