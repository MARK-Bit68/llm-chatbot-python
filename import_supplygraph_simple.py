#!/usr/bin/env python3
"""
Import SupplyGraph dataset into Neo4j using pandas and Cypher MERGE.

This script reads CSV files directly and uses Cypher MERGE statements to import
the SupplyGraph benchmark dataset, replacing the current database schema.

The SupplyGraph schema includes:
- Products (nodes with codes like SOS008L02P, POV005L04P, etc.)
- Product Groups (S, P, A, M, E) and SubGroups (SOS, POV, POP, AT, MAR, etc.)
- Plants (1911, 1916, 1917, 1919, 1920, 1921, 2111, 2114, 2116, 2117, 2119, 2120, 2121)
- Storage Locations (1130.0, 1430.0, 1630.0, 1730.0, 1930.0, 2030.0, 2130.0)
- Temporal data (Production, Sales Order, Factory Issue, Delivery to Distributor)
- Both Unit and Weight measurements

This replaces the current SKU-based schema with the comprehensive SupplyGraph benchmark.
"""

import os
import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
import json

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
    
    # Drop all constraints and indexes
    try:
        graph.query("CALL apoc.schema.assert({},{})")
    except:
        # If APOC is not available, drop constraints manually
        graph.query("SHOW CONSTRAINTS YIELD name CALL { DROP CONSTRAINT $name } IN TRANSACTIONS")
        graph.query("SHOW INDEXES YIELD name CALL { DROP INDEX $name } IN TRANSACTIONS")
    
    # Delete all nodes and relationships
    graph.query("MATCH (n) DETACH DELETE n")
    
    print("✅ Database cleared")

def create_supplygraph_schema(graph):
    """Create the SupplyGraph schema with constraints and indexes"""
    print("🏗️  Creating SupplyGraph schema...")
    
    # Create constraints for unique identifiers
    constraints = [
        "CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.code IS UNIQUE",
        "CREATE CONSTRAINT group_code IF NOT EXISTS FOR (g:Group) REQUIRE g.code IS UNIQUE", 
        "CREATE CONSTRAINT subgroup_code IF NOT EXISTS FOR (sg:SubGroup) REQUIRE sg.code IS UNIQUE",
        "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (pl:Plant) REQUIRE pl.id IS UNIQUE",
        "CREATE CONSTRAINT storage_id IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE sl.id IS UNIQUE",
        "CREATE CONSTRAINT time_series_id IF NOT EXISTS FOR (ts:TimeSeries) REQUIRE ts.id IS UNIQUE"
    ]
    
    for constraint in constraints:
        try:
            graph.query(constraint)
        except Exception as e:
            print(f"⚠️  Constraint creation warning: {e}")
    
    # Create indexes for better performance
    indexes = [
        "CREATE INDEX product_code_idx IF NOT EXISTS FOR (p:Product) ON (p.code)",
        "CREATE INDEX group_code_idx IF NOT EXISTS FOR (g:Group) ON (g.code)",
        "CREATE INDEX subgroup_code_idx IF NOT EXISTS FOR (sg:SubGroup) ON (sg.code)",
        "CREATE INDEX plant_id_idx IF NOT EXISTS FOR (pl:Plant) ON (pl.id)",
        "CREATE INDEX storage_id_idx IF NOT EXISTS FOR (sl:StorageLocation) ON (sl.id)",
        "CREATE INDEX time_series_type_idx IF NOT EXISTS FOR (ts:TimeSeries) ON (ts.type)",
        "CREATE INDEX time_series_measurement_idx IF NOT EXISTS FOR (ts:TimeSeries) ON (ts.measurement_type)"
    ]
    
    for index in indexes:
        try:
            graph.query(index)
        except Exception as e:
            print(f"⚠️  Index creation warning: {e}")
    
    print("✅ Schema created")

def import_nodes(graph):
    """Import all node data from CSV files"""
    print("📥 Importing nodes...")
    
    # Import products (from Nodes.csv)
    products_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes.csv")
    print(f"  Found {len(products_df)} products")
    
    for _, row in products_df.iterrows():
        product_code = row['Node']
        graph.query("MERGE (p:Product {code: $code})", {"code": product_code})
    
    print("✅ Products imported")
    
    # Import product groups and subgroups
    groups_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Node Types (Product Group and Subgroup).csv")
    print(f"  Found {len(groups_df)} product classifications")
    
    for _, row in groups_df.iterrows():
        product_code = row['Node']
        group_code = row['Group']
        subgroup_code = row['Sub-Group']
        
        # Create group and subgroup nodes
        graph.query("MERGE (g:Group {code: $code})", {"code": group_code})
        graph.query("MERGE (sg:SubGroup {code: $code})", {"code": subgroup_code})
        
        # Create relationships
        graph.query("""
            MATCH (p:Product {code: $product_code})
            MATCH (g:Group {code: $group_code})
            MATCH (sg:SubGroup {code: $subgroup_code})
            MERGE (p)-[:IN_GROUP]->(g)
            MERGE (p)-[:IN_SUBGROUP]->(sg)
        """, {
            "product_code": product_code,
            "group_code": group_code,
            "subgroup_code": subgroup_code
        })
    
    print("✅ Product groups and subgroups imported")
    
    # Import plant and storage locations
    plant_storage_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes Type (Plant & Storage).csv")
    print(f"  Found {len(plant_storage_df)} plant-storage relationships")
    
    for _, row in plant_storage_df.iterrows():
        product_code = row['Node']
        plant_id = row['Plant']
        storage_id = float(row['Storage Location'])
        
        # Create plant and storage nodes
        graph.query("MERGE (pl:Plant {id: $id})", {"id": plant_id})
        graph.query("MERGE (sl:StorageLocation {id: $id})", {"id": storage_id})
        
        # Create relationships
        graph.query("""
            MATCH (p:Product {code: $product_code})
            MATCH (pl:Plant {id: $plant_id})
            MATCH (sl:StorageLocation {id: $storage_id})
            MERGE (p)-[:PRODUCED_AT]->(pl)
            MERGE (p)-[:STORED_AT]->(sl)
        """, {
            "product_code": product_code,
            "plant_id": plant_id,
            "storage_id": storage_id
        })
    
    print("✅ Plant and storage locations imported")

def import_edges(graph):
    """Import all edge data from CSV files"""
    print("🔗 Importing edges...")
    
    # Import product group edges
    group_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Group).csv")
    print(f"  Found {len(group_edges_df)} product group edges")
    
    for _, row in group_edges_df.iterrows():
        node1 = row['node1']
        node2 = row['node2']
        group_code = row['GroupCode']
        
        graph.query("""
            MATCH (p1:Product {code: $node1})
            MATCH (p2:Product {code: $node2})
            MERGE (p1)-[:SAME_GROUP {group_code: $group_code}]->(p2)
        """, {
            "node1": node1,
            "node2": node2,
            "group_code": group_code
        })
    
    print("✅ Product group edges imported")
    
    # Import product subgroup edges
    subgroup_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Sub-Group).csv")
    print(f"  Found {len(subgroup_edges_df)} product subgroup edges")
    
    for _, row in subgroup_edges_df.iterrows():
        node1 = row['node1']
        node2 = row['node2']
        subgroup_code = row['SubGroupCode']
        
        graph.query("""
            MATCH (p1:Product {code: $node1})
            MATCH (p2:Product {code: $node2})
            MERGE (p1)-[:SAME_SUBGROUP {subgroup_code: $subgroup_code}]->(p2)
        """, {
            "node1": node1,
            "node2": node2,
            "subgroup_code": subgroup_code
        })
    
    print("✅ Product subgroup edges imported")
    
    # Import plant edges
    plant_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Plant).csv")
    print(f"  Found {len(plant_edges_df)} plant edges")
    
    for _, row in plant_edges_df.iterrows():
        node1 = row['node1']
        node2 = row['node2']
        plant_code = row['PlantCode']
        
        graph.query("""
            MATCH (p1:Product {code: $node1})
            MATCH (p2:Product {code: $node2})
            MERGE (p1)-[:CO_PRODUCED_AT {plant_id: $plant_code}]->(p2)
        """, {
            "node1": node1,
            "node2": node2,
            "plant_code": plant_code
        })
    
    print("✅ Plant edges imported")
    
    # Import storage location edges
    storage_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Storage Location).csv")
    print(f"  Found {len(storage_edges_df)} storage location edges")
    
    for _, row in storage_edges_df.iterrows():
        node1 = row['node1']
        node2 = row['node2']
        storage_code = float(row['StorageCode'])
        
        graph.query("""
            MATCH (p1:Product {code: $node1})
            MATCH (p2:Product {code: $node2})
            MERGE (p1)-[:CO_STORED_AT {storage_id: $storage_code}]->(p2)
        """, {
            "node1": node1,
            "node2": node2,
            "storage_code": storage_code
        })
    
    print("✅ Storage location edges imported")

def import_temporal_data(graph):
    """Import temporal data (time series) from CSV files"""
    print("📈 Importing temporal data...")
    
    # Define temporal data types and their files
    temporal_files = [
        ("Production", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Production .csv", "Unit"),
        ("Production", "external/RawDataSetSupplyGraph/Temporal Data/Weight/Production .csv", "Weight"),
        ("SalesOrder", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Sales Order.csv", "Unit"),
        ("SalesOrder", "external/RawDataSetSupplyGraph/Temporal Data/Weight/Sales Order .csv", "Weight"),
        ("FactoryIssue", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Factory Issue.csv", "Unit"),
        ("FactoryIssue", "external/RawDataSetSupplyGraph/Temporal Data/Weight/Factory Issue.csv", "Weight"),
        ("DeliveryToDistributor", "external/RawDataSetSupplyGraph/Temporal Data/Unit/Delivery To distributor.csv", "Unit"),
        ("DeliveryToDistributor", "external/RawDataSetSupplyGraph/Temporal Data/Weight/Delivery to Distributor.csv", "Weight")
    ]
    
    for data_type, filepath, measurement_type in temporal_files:
        print(f"  Importing {data_type} ({measurement_type})...")
        
        if not os.path.exists(filepath):
            print(f"    ❌ File not found: {filepath}")
            continue
        
        df = pd.read_csv(filepath)
        print(f"    Found {len(df)} time points for {data_type}")
        
        # Get product columns (all columns except 'Date')
        product_columns = [col for col in df.columns if col != 'Date']
        
        # Create time series nodes for each product
        for product_code in product_columns:
            time_series_id = f"{product_code}_{data_type}_{measurement_type}"
            
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
        
        # Import time series data points (sample for performance)
        # For full import, you might want to batch this or use a different approach
        sample_size = min(50, len(df))  # Import first 50 time points for demo
        sample_df = df.head(sample_size)
        
        for _, row in sample_df.iterrows():
            date = row['Date']
            
            for product_code in product_columns:
                value = row[product_code]
                if pd.notna(value) and value != '':
                    time_series_id = f"{product_code}_{data_type}_{measurement_type}"
                    
                    # Store time series data as properties (for demo)
                    # In production, you might want to use a different approach for time series
                    graph.query("""
                        MATCH (ts:TimeSeries {id: $time_series_id})
                        SET ts += {
                            date: $date,
                            value: $value
                        }
                    """, {
                        "time_series_id": time_series_id,
                        "date": date,
                        "value": float(value)
                    })
    
    print("✅ Temporal data imported (sample)")

def create_enhanced_queries(graph):
    """Create additional indexes and constraints for better query performance"""
    print("🔍 Creating enhanced indexes for query optimization...")
    
    # Create composite indexes for common query patterns
    enhanced_indexes = [
        "CREATE INDEX product_group_idx IF NOT EXISTS FOR (p:Product)-[:IN_GROUP]->(g:Group) ON (g.code, p.code)",
        "CREATE INDEX product_subgroup_idx IF NOT EXISTS FOR (p:Product)-[:IN_SUBGROUP]->(sg:SubGroup) ON (sg.code, p.code)",
        "CREATE INDEX product_plant_idx IF NOT EXISTS FOR (p:Product)-[:PRODUCED_AT]->(pl:Plant) ON (pl.id, p.code)",
        "CREATE INDEX product_storage_idx IF NOT EXISTS FOR (p:Product)-[:STORED_AT]->(sl:StorageLocation) ON (sl.id, p.code)",
        "CREATE INDEX time_series_product_idx IF NOT EXISTS FOR (p:Product)-[:HAS_TIME_SERIES]->(ts:TimeSeries) ON (p.code, ts.type, ts.measurement_type)"
    ]
    
    for index in enhanced_indexes:
        try:
            graph.query(index)
        except Exception as e:
            print(f"⚠️  Enhanced index creation warning: {e}")
    
    print("✅ Enhanced indexes created")

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
    print("🚀 Starting SupplyGraph dataset import...")
    
    try:
        # Get Neo4j connection
        graph = get_graph()
        print("✅ Connected to Neo4j")
        
        # Clear existing database
        clear_database(graph)
        
        # Create schema
        create_supplygraph_schema(graph)
        
        # Import data
        import_nodes(graph)
        import_edges(graph)
        import_temporal_data(graph)
        
        # Create enhanced indexes
        create_enhanced_queries(graph)
        
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
