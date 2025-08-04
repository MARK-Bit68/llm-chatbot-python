#!/usr/bin/env python3
"""
Debug Neo4j database and embeddings
"""
import streamlit as st
import os
from solutions.graph import get_graph
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
    graph = get_graph()
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

# --- SKU ID Uniqueness and Index/Constraint Check ---
from neo4j import GraphDatabase

def check_sku_id_uniqueness_and_index():
    print("\n🔍 DEBUG: Checking SKU ID uniqueness and index/constraint...")
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    pwd = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    with driver.session(database=database) as session:
        # Create uniqueness constraint if not exists
        print("🔍 DEBUG: Ensuring uniqueness constraint on :SKU(sku_id)...")
        try:
            session.run("CREATE CONSTRAINT sku_id_unique IF NOT EXISTS FOR (sku:SKU) REQUIRE sku.sku_id IS UNIQUE")
            print("✅ Uniqueness constraint created or already exists.")
        except Exception as e:
            print(f"❌ Error creating uniqueness constraint: {e}")
        # Get all SKU IDs
        result = session.run("MATCH (sku:SKU) RETURN sku.sku_id AS sku_id")
        sku_ids = [record["sku_id"] for record in result]
        print(f"Found {len(sku_ids)} SKU IDs.")
        # Check for duplicates
        duplicates = set([x for x in sku_ids if sku_ids.count(x) > 1])
        if duplicates:
            print(f"❌ Duplicate SKU IDs found: {duplicates}")
        else:
            print("✅ All SKU IDs are unique.")
        # Check for index/constraint (use SHOW INDEXES for Aura/modern Neo4j)
        idx_result = session.run("SHOW INDEXES YIELD name, entityType, labelsOrTypes, properties, type RETURN name, entityType, labelsOrTypes, properties, type")
        found_index = False
        for record in idx_result:
            labels = record.get("labelsOrTypes")
            props = record.get("properties")
            if labels and props and "SKU" in labels and "sku_id" in props:
                print(f"✅ Index/constraint found: {record}")
                found_index = True
        if not found_index:
            print("❌ No index/constraint found on :SKU(sku_id)")
    driver.close()

if __name__ == "__main__":
    check_sku_id_uniqueness_and_index()

print("✅ All database tests passed!") 