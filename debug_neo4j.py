#!/usr/bin/env python3
"""
Debug Neo4j database and embeddings
"""
import streamlit as st
import os
from graph import get_graph_instance
from llm import get_embeddings

print("🔍 DEBUG: Testing Neo4j connection and data...")

# Check environment variables
print("🔍 DEBUG: Checking environment variables...")
required_vars = ["NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
for var in required_vars:
    value = os.getenv(var)
    if value:
        print(f"✅ {var}: {value[:20]}..." if len(value) > 20 else f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

# Test basic connection
try:
    graph = get_graph_instance()
    if graph is None:
        print("❌ ERROR: Graph instance is None - this means Neo4j connection failed")
        print("💡 This is expected if running locally without Neo4j environment variables")
        print("💡 On Railway, the environment variables should be set")
        exit(1)
    print("✅ Graph connection successful")
except Exception as e:
    print(f"❌ ERROR: Failed to connect to Neo4j: {e}")
    print("💡 This is expected if running locally without Neo4j")
    exit(1)

# Test basic SKU query
try:
    print("🔍 DEBUG: Testing basic SKU query...")
    result = graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
    count = result[0]['count'] if result else 0
    print(f"✅ Found {count} SKU nodes in database")
    
    if count == 0:
        print("❌ ERROR: No SKU nodes found in database!")
        print("💡 This suggests the data hasn't been loaded into the Railway Neo4j instance")
        exit(1)
    
    # Test getting actual SKU data
    print("🔍 DEBUG: Testing SKU data retrieval...")
    result = graph.query("MATCH (sku:SKU) RETURN sku.sku_id, sku.name LIMIT 5")
    print(f"✅ Retrieved {len(result)} SKU records:")
    for record in result:
        print(f"  - {record['sku.sku_id']}: {record['sku.name']}")
        
except Exception as e:
    print(f"❌ ERROR: Failed to query SKU data: {e}")
    exit(1)

# Test the specific query that the agent should use
try:
    print("🔍 DEBUG: Testing 'all SKUs' query that agent should use...")
    result = graph.query("MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 3")
    print(f"✅ Retrieved {len(result)} SKU records with full data:")
    for record in result:
        print(f"  - {record['sku.sku_id']}: {record['sku.name']}")
        print(f"    Plot preview: {record['sku.plot'][:100]}...")
        
except Exception as e:
    print(f"❌ ERROR: Failed to query SKU data with plot: {e}")
    exit(1)

print("✅ All database tests passed!") 