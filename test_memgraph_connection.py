#!/usr/bin/env python3
"""
Simple test script to verify Memgraph connection and basic functionality
"""

import sys
import subprocess

def test_memgraph_connection():
    """Test if Memgraph is running and accessible"""
    print("🔍 Testing Memgraph Connection...")
    
    try:
        from gqlalchemy import Memgraph
        
        # Try to connect
        memgraph = Memgraph("localhost", 7687)
        result = memgraph.execute("RETURN 1 AS test")
        
        if result and result[0]['test'] == 1:
            print("✅ Memgraph connection successful!")
            return True
        else:
            print("❌ Memgraph connection failed - unexpected response")
            return False
            
    except ImportError:
        print("❌ gqlalchemy not installed")
        print("   Run: pip install gqlalchemy")
        return False
    except Exception as e:
        print(f"❌ Memgraph connection failed: {e}")
        print("💡 Make sure Memgraph is running with:")
        print("   docker run -d --name memgraph-fmcg -p 7687:7687 -p 7444:7444 -p 3000:3000 memgraph/memgraph-platform")
        return False

def test_docker_memgraph():
    """Test if Memgraph Docker container is running"""
    print("🐳 Testing Docker Memgraph container...")
    
    try:
        # Check if container is running
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=memgraph-fmcg", "--format", "{{.Names}}"],
            capture_output=True, text=True
        )
        
        if "memgraph-fmcg" in result.stdout:
            print("✅ Memgraph Docker container is running")
            return True
        else:
            print("❌ Memgraph Docker container not found")
            print("💡 Start it with:")
            print("   docker run -d --name memgraph-fmcg -p 7687:7687 -p 7444:7444 -p 3000:3000 memgraph/memgraph-platform")
            return False
            
    except FileNotFoundError:
        print("❌ Docker not found or not in PATH")
        return False
    except Exception as e:
        print(f"❌ Docker test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Memgraph Connection Test")
    print("=" * 40)
    
    # Test Docker container
    docker_ok = test_docker_memgraph()
    
    if docker_ok:
        # Test connection
        connection_ok = test_memgraph_connection()
        
        if connection_ok:
            print("\n🎉 All tests passed! Memgraph is ready to use.")
            print("💡 You can now run: python memgraph_fmcg_analyzer.py")
        else:
            print("\n⚠️  Docker container is running but connection failed.")
            print("   This might be due to:")
            print("   - Container still starting up (wait 10-30 seconds)")
            print("   - Port conflicts")
            print("   - Network issues")
    else:
        print("\n❌ Docker container not running.")
        print("   Please start Memgraph first.")

if __name__ == "__main__":
    main()
