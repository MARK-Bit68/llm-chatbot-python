#!/usr/bin/env python3
"""
Test deployment configuration for FMCG RAG Chatbot
This script helps verify that all components are ready for deployment
"""

import os
import sys
from pathlib import Path

def test_requirements():
    """Test that all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    required_packages = [
        'streamlit',
        'langchain',
        'openai',
        'neo4j',
        'langchain_neo4j',
        'pandas',
        'openpyxl'
    ]
    
    failed_imports = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError as e:
            print(f"  ❌ {package}: {e}")
            failed_imports.append(package)
    
    if failed_imports:
        print(f"\n❌ Failed imports: {failed_imports}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    else:
        print("✅ All packages imported successfully")
        return True

def test_config_files():
    """Test that required config files exist"""
    print("\n🔍 Testing configuration files...")
    
    required_files = [
        'railway.toml',
        'Procfile',
        '.streamlit/config.toml',
        'requirements.txt'
    ]
    
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        return False
    else:
        print("✅ All config files present")
        return True

def test_environment_variables():
    """Test that required environment variables are set"""
    print("\n🔍 Testing environment variables...")
    
    required_vars = [
        'OPENAI_API_KEY',
        'OPENAI_MODEL',
        'NEO4J_URI',
        'NEO4J_USERNAME',
        'NEO4J_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var}")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {missing_vars}")
        print("💡 Set these in Railway environment variables")
        return False
    else:
        print("✅ All environment variables set")
        return True

def test_neo4j_connection():
    """Test Neo4j connection"""
    print("\n🔍 Testing Neo4j connection...")
    
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=os.getenv('NEO4J_URI'),
            username=os.getenv('NEO4J_USERNAME'),
            password=os.getenv('NEO4J_PASSWORD')
        )
        
        result = graph.query('RETURN 1 as test')
        print("  ✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"  ❌ Neo4j connection failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    print("\n🔍 Testing OpenAI connection...")
    
    try:
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Test with a simple completion
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        print("  ✅ OpenAI connection successful")
        return True
    except Exception as e:
        print(f"  ❌ OpenAI connection failed: {e}")
        return False

def main():
    """Run all deployment tests"""
    print("🚀 FMCG RAG Chatbot - Deployment Configuration Test")
    print("=" * 60)
    
    tests = [
        test_requirements,
        test_config_files,
        test_environment_variables,
        test_neo4j_connection,
        test_openai_connection
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your app is ready for deployment.")
        print("\n📋 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Connect your repository to Railway")
        print("3. Deploy and test your app")
    else:
        print("❌ Some tests failed. Please fix the issues above before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main() 