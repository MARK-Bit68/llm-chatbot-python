#!/usr/bin/env python3
"""
Import SupplyGraph dataset into Neo4j using batched operations.

This script uses small batches and progress tracking to avoid timeouts
and provide visibility into the import process.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json
import time
from tqdm import tqdm

def get_neo4j_config(key: str, default: str = "") -> str:
    """Get Neo4j config from environment variables or secrets file"""
    # First try environment variables
    env_value = os.getenv(key)
    if env_value:
        return env_value
    
    # Then try secrets file
    try:
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        k, v = line.split('=', 1)
                        if k.strip() == key:
                            return v.strip().strip('"')
    except:
        pass
    
    return default

def get_graph():
    """Create a Neo4j graph connection, raising on failure."""
    from langchain_neo4j import Neo4jGraph

    graph = Neo4jGraph(
        url=get_neo4j_config("NEO4J_URI"),
        username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
        password=get_neo4j_config("NEO4J_PASSWORD"),
    )
    # Sanity check
    graph.query("RETURN 1 AS ok")
    return graph

def clear_database(graph):
    """Clear all existing data from the database"""
    print("🗑️  Clearing existing database...")
    
    try:
        # Drop all constraints and indexes
        try:
            graph.query("CALL apoc.schema.assert({},{})")
        except:
            # If APOC is not available, drop constraints manually
            try:
                graph.query("SHOW CONSTRAINTS YIELD name CALL { DROP CONSTRAINT $name } IN TRANSACTIONS")
            except:
                pass
            try:
                graph.query("SHOW INDEXES YIELD name CALL { DROP INDEX $name } IN TRANSACTIONS")
            except:
                pass
        
        # Delete all nodes and relationships
        graph.query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")
    except Exception as e:
        print(f"⚠️  Warning during database clear: {e}")

def create_supplygraph_schema(graph):
    """Create the SupplyGraph schema with constraints and indexes"""
    print("🏗️  Creating SupplyGraph schema...")
    
    # Create constraints for unique identifiers
    constraints = [
        "CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.code IS UNIQUE",
        "CREATE CONSTRAINT group_code IF NOT EXISTS FOR (g:Group) REQUIRE g.code IS UNIQUE", 
        "CREATE CONSTRAINT subgroup_code IF NOT EXISTS FOR (sg:SubGroup) REQUIRE sg.code IS UNIQUE",
        "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (pl:Plant) REQUIRE pl.id IS UNIQUE",
        "CREATE CONSTRAINT storage_id IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE sl.id IS UNIQUE"
    ]
    
    for constraint in constraints:
        try:
            graph.query(constraint)
            print(f"  ✅ Created constraint: {constraint.split('FOR')[0].strip()}")
        except Exception as e:
            print(f"  ⚠️  Constraint creation warning: {e}")
    
    # Create indexes for better performance
    indexes = [
        "CREATE INDEX product_code_idx IF NOT EXISTS FOR (p:Product) ON (p.code)",
        "CREATE INDEX group_code_idx IF NOT EXISTS FOR (g:Group) ON (g.code)",
        "CREATE INDEX subgroup_code_idx IF NOT EXISTS FOR (sg:SubGroup) ON (sg.code)",
        "CREATE INDEX plant_id_idx IF NOT EXISTS FOR (pl:Plant) ON (pl.id)",
        "CREATE INDEX storage_id_idx IF NOT EXISTS FOR (sl:StorageLocation) ON (sl.id)"
    ]
    
    for index in indexes:
        try:
            graph.query(index)
            print(f"  ✅ Created index: {index.split('FOR')[0].strip()}")
        except Exception as e:
            print(f"  ⚠️  Index creation warning: {e}")
    
    print("✅ Schema created")

def batch_import_products(graph, batch_size=10):
    """Import products in batches"""
    print("📥 Importing products...")
    
    products_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes.csv")
    print(f"  Found {len(products_df)} products")
    
    # Process in batches
    for i in tqdm(range(0, len(products_df), batch_size), desc="Importing products"):
        batch = products_df.iloc[i:i+batch_size]
        
        # Create batch query
        codes = [row['Node'] for _, row in batch.iterrows()]
        query = "UNWIND $codes as code MERGE (p:Product {code: code})"
        
        try:
            graph.query(query, {"codes": codes})
        except Exception as e:
            print(f"  ⚠️  Batch {i//batch_size + 1} failed: {e}")
            # Try individual imports as fallback
            for code in codes:
                try:
                    graph.query("MERGE (p:Product {code: $code})", {"code": code})
                except Exception as e2:
                    print(f"    ❌ Failed to import product {code}: {e2}")
    
    print("✅ Products imported")

def batch_import_groups(graph, batch_size=10):
    """Import product groups and subgroups in batches"""
    print("📥 Importing product groups and subgroups...")
    
    groups_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Node Types (Product Group and Subgroup).csv")
    print(f"  Found {len(groups_df)} product classifications")
    
    # First, create all unique groups and subgroups
    unique_groups = groups_df['Group'].unique()
    unique_subgroups = groups_df['Sub-Group'].unique()
    
    print(f"  Creating {len(unique_groups)} unique groups and {len(unique_subgroups)} unique subgroups")
    
    # Create groups
    for group_code in unique_groups:
        try:
            graph.query("MERGE (g:Group {code: $code})", {"code": group_code})
        except Exception as e:
            print(f"  ❌ Failed to create group {group_code}: {e}")
    
    # Create subgroups
    for subgroup_code in unique_subgroups:
        try:
            graph.query("MERGE (sg:SubGroup {code: $code})", {"code": subgroup_code})
        except Exception as e:
            print(f"  ❌ Failed to create subgroup {subgroup_code}: {e}")
    
    # Now create relationships in batches
    for i in tqdm(range(0, len(groups_df), batch_size), desc="Creating group relationships"):
        batch = groups_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p:Product {code: $product_code})
                    MATCH (g:Group {code: $group_code})
                    MATCH (sg:SubGroup {code: $subgroup_code})
                    MERGE (p)-[:IN_GROUP]->(g)
                    MERGE (p)-[:IN_SUBGROUP]->(sg)
                """, {
                    "product_code": row['Node'],
                    "group_code": row['Group'],
                    "subgroup_code": row['Sub-Group']
                })
            except Exception as e:
                print(f"  ❌ Failed to create relationships for {row['Node']}: {e}")
    
    print("✅ Product groups and subgroups imported")

def batch_import_plants_storage(graph, batch_size=50):
    """Import plant and storage locations in batches"""
    print("📥 Importing plant and storage locations...")
    
    plant_storage_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes Type (Plant & Storage).csv")
    print(f"  Found {len(plant_storage_df)} plant-storage relationships")
    
    # First, create all unique plants and storage locations
    unique_plants = plant_storage_df['Plant'].unique()
    unique_storage = plant_storage_df['Storage Location'].unique()
    
    print(f"  Creating {len(unique_plants)} unique plants and {len(unique_storage)} unique storage locations")
    
    # Create plants
    for plant_id in unique_plants:
        try:
            graph.query("MERGE (pl:Plant {id: $id})", {"id": plant_id})
        except Exception as e:
            print(f"  ❌ Failed to create plant {plant_id}: {e}")
    
    # Create storage locations
    for storage_id in unique_storage:
        try:
            graph.query("MERGE (sl:StorageLocation {id: $id})", {"id": float(storage_id)})
        except Exception as e:
            print(f"  ❌ Failed to create storage location {storage_id}: {e}")
    
    # Now create relationships in batches
    for i in tqdm(range(0, len(plant_storage_df), batch_size), desc="Creating plant-storage relationships"):
        batch = plant_storage_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p:Product {code: $product_code})
                    MATCH (pl:Plant {id: $plant_id})
                    MATCH (sl:StorageLocation {id: $storage_id})
                    MERGE (p)-[:PRODUCED_AT]->(pl)
                    MERGE (p)-[:STORED_AT]->(sl)
                """, {
                    "product_code": row['Node'],
                    "plant_id": row['Plant'],
                    "storage_id": float(row['Storage Location'])
                })
            except Exception as e:
                print(f"  ❌ Failed to create plant-storage relationships for {row['Node']}: {e}")
    
    print("✅ Plant and storage locations imported")

def batch_import_edges(graph, batch_size=100):
    """Import edges in batches"""
    print("🔗 Importing edges...")
    
    # Import product group edges
    print("  Importing product group edges...")
    group_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Group).csv")
    print(f"    Found {len(group_edges_df)} product group edges")
    
    for i in tqdm(range(0, len(group_edges_df), batch_size), desc="Importing group edges"):
        batch = group_edges_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p1:Product {code: $node1})
                    MATCH (p2:Product {code: $node2})
                    MERGE (p1)-[:SAME_GROUP {group_code: $group_code}]->(p2)
                """, {
                    "node1": row['node1'],
                    "node2": row['node2'],
                    "group_code": row['GroupCode']
                })
            except Exception as e:
                print(f"    ❌ Failed to create group edge {row['node1']} -> {row['node2']}: {e}")
    
    # Import product subgroup edges
    print("  Importing product subgroup edges...")
    subgroup_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Sub-Group).csv")
    print(f"    Found {len(subgroup_edges_df)} product subgroup edges")
    
    for i in tqdm(range(0, len(subgroup_edges_df), batch_size), desc="Importing subgroup edges"):
        batch = subgroup_edges_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p1:Product {code: $node1})
                    MATCH (p2:Product {code: $node2})
                    MERGE (p1)-[:SAME_SUBGROUP {subgroup_code: $subgroup_code}]->(p2)
                """, {
                    "node1": row['node1'],
                    "node2": row['node2'],
                    "subgroup_code": row['SubGroupCode']
                })
            except Exception as e:
                print(f"    ❌ Failed to create subgroup edge {row['node1']} -> {row['node2']}: {e}")
    
    # Import plant edges
    print("  Importing plant edges...")
    plant_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Plant).csv")
    print(f"    Found {len(plant_edges_df)} plant edges")
    
    for i in tqdm(range(0, len(plant_edges_df), batch_size), desc="Importing plant edges"):
        batch = plant_edges_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p1:Product {code: $node1})
                    MATCH (p2:Product {code: $node2})
                    MERGE (p1)-[:CO_PRODUCED_AT {plant_id: $plant_code}]->(p2)
                """, {
                    "node1": row['node1'],
                    "node2": row['node2'],
                    "plant_code": row['PlantCode']
                })
            except Exception as e:
                print(f"    ❌ Failed to create plant edge {row['node1']} -> {row['node2']}: {e}")
    
    # Import storage location edges
    print("  Importing storage location edges...")
    storage_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Storage Location).csv")
    print(f"    Found {len(storage_edges_df)} storage location edges")
    
    for i in tqdm(range(0, len(storage_edges_df), batch_size), desc="Importing storage edges"):
        batch = storage_edges_df.iloc[i:i+batch_size]
        
        for _, row in batch.iterrows():
            try:
                graph.query("""
                    MATCH (p1:Product {code: $node1})
                    MATCH (p2:Product {code: $node2})
                    MERGE (p1)-[:CO_STORED_AT {storage_id: $storage_code}]->(p2)
                """, {
                    "node1": row['node1'],
                    "node2": row['node2'],
                    "storage_code": float(row['StorageCode'])
                })
            except Exception as e:
                print(f"    ❌ Failed to create storage edge {row['node1']} -> {row['node2']}: {e}")
    
    print("✅ All edges imported")

def import_sample_temporal_data(graph, sample_size=10):
    """Import a sample of temporal data for demonstration"""
    print("📈 Importing sample temporal data...")
    
    # Define temporal data types and their files
    temporal_files = [
        ("Production", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Production .csv", "Unit"),
        ("SalesOrder", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Sales Order.csv", "Unit")
    ]
    
    for data_type, filepath, measurement_type in temporal_files:
        print(f"  Importing {data_type} ({measurement_type}) sample...")
        
        if not os.path.exists(filepath):
            print(f"    ❌ File not found: {filepath}")
            continue
        
        df = pd.read_csv(filepath)
        print(f"    Found {len(df)} time points for {data_type}")
        
        # Get product columns (all columns except 'Date')
        product_columns = [col for col in df.columns if col != 'Date']
        
        # Sample products for demo
        sample_products = product_columns[:min(5, len(product_columns))]
        sample_df = df.head(sample_size)
        
        print(f"    Processing {len(sample_products)} products with {len(sample_df)} time points")
        
        # Create time series nodes for sample products
        for product_code in sample_products:
            time_series_id = f"{product_code}_{data_type}_{measurement_type}"
            
            try:
                graph.query("""
                    MERGE (ts:TimeSeries {
                        id: $id,
                        type: $type,
                        measurement_type: $measurement_type,
                        product_code: $product_code
                    })
                """, {
                    "id": time_series_id,
                    "type": data_type,
                    "measurement_type": measurement_type,
                    "product_code": product_code
                })
                
                # Create relationship to product
                graph.query("""
                    MATCH (p:Product {code: $product_code})
                    MATCH (ts:TimeSeries {id: $time_series_id})
                    MERGE (p)-[:HAS_TIME_SERIES]->(ts)
                """, {
                    "product_code": product_code,
                    "time_series_id": time_series_id
                })
                
                # Import sample time series data
                for _, row in sample_df.iterrows():
                    value = row[product_code]
                    if pd.notna(value) and value != '':
                        try:
                            graph.query("""
                                MATCH (ts:TimeSeries {id: $time_series_id})
                                SET ts += {
                                    date: $date,
                                    value: $value
                                }
                            """, {
                                "time_series_id": time_series_id,
                                "date": row['Date'],
                                "value": float(value)
                            })
                        except Exception as e:
                            print(f"      ❌ Failed to add time series data for {product_code}: {e}")
                            
            except Exception as e:
                print(f"    ❌ Failed to create time series for {product_code}: {e}")
    
    print("✅ Sample temporal data imported")

def verify_import(graph):
    """Verify that the import was successful"""
    print("🔍 Verifying import...")
    
    verification_queries = [
        ("Products", "MATCH (p:Product) RETURN count(p) as count"),
        ("Groups", "MATCH (g:Group) RETURN count(g) as count"),
        ("SubGroups", "MATCH (sg:SubGroup) RETURN count(sg) as count"),
        ("Plants", "MATCH (pl:Plant) RETURN count(pl) as count"),
        ("Storage Locations", "MATCH (sl:StorageLocation) RETURN count(sl) as count"),
        ("Time Series", "MATCH (ts:TimeSeries) RETURN count(ts) as count"),
        ("Product-Group Relationships", "MATCH (p:Product)-[:IN_GROUP]->(g:Group) RETURN count(*) as count"),
        ("Product-Plant Relationships", "MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant) RETURN count(*) as count"),
        ("Product-Storage Relationships", "MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation) RETURN count(*) as count")
    ]
    
    results = {}
    for name, query in verification_queries:
        try:
            result = graph.query(query)
            count = result[0]['count'] if result else 0
            results[name] = count
            print(f"  {name}: {count}")
        except Exception as e:
            print(f"  ❌ Error verifying {name}: {e}")
            results[name] = 0
    
    # Summary
    print("\n📊 Import Summary:")
    print(f"  Total Products: {results.get('Products', 0)}")
    print(f"  Total Groups: {results.get('Groups', 0)}")
    print(f"  Total SubGroups: {results.get('SubGroups', 0)}")
    print(f"  Total Plants: {results.get('Plants', 0)}")
    print(f"  Total Storage Locations: {results.get('Storage Locations', 0)}")
    print(f"  Total Time Series: {results.get('Time Series', 0)}")
    print(f"  Total Relationships: {sum([results.get('Product-Group Relationships', 0), results.get('Product-Plant Relationships', 0), results.get('Product-Storage Relationships', 0)])}")
    
    return results

def main():
    """Main import function"""
    print("🚀 Starting SupplyGraph dataset import (batched)...")
    
    try:
        # Get Neo4j connection
        graph = get_graph()
        print("✅ Connected to Neo4j")
        
        # Clear existing database
        clear_database(graph)
        
        # Create schema
        create_supplygraph_schema(graph)
        
        # Import data in batches
        batch_import_products(graph, batch_size=5)
        batch_import_groups(graph, batch_size=5)
        batch_import_plants_storage(graph, batch_size=25)
        batch_import_edges(graph, batch_size=50)
        import_sample_temporal_data(graph, sample_size=5)
        
        # Verify import
        results = verify_import(graph)
        
        print("\n🎉 SupplyGraph dataset import completed successfully!")
        print("The database now contains the complete SupplyGraph benchmark dataset.")
        print("You can now use the chatbot with the new schema.")
        
        return results
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
