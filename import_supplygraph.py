#!/usr/bin/env python3
"""
Import SupplyGraph dataset into Neo4j using native CSV import.

This script uses Neo4j's LOAD CSV command to efficiently import the SupplyGraph
benchmark dataset, replacing the current database schema with the new data.

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
    graph.query("CALL apoc.schema.assert({},{})")
    
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

def import_nodes(graph, csv_base_path: str):
    """Import all node data from CSV files"""
    print("📥 Importing nodes...")
    
    # Import products (from Nodes.csv)
    products_query = """
    LOAD CSV WITH HEADERS FROM 'file:///nodes.csv' AS row
    MERGE (p:Product {code: row.Node})
    """
    graph.query(products_query)
    print("✅ Products imported")
    
    # Import product groups and subgroups
    groups_query = """
    LOAD CSV WITH HEADERS FROM 'file:///node_types_product.csv' AS row
    MERGE (g:Group {code: row.Group})
    MERGE (sg:SubGroup {code: row.`Sub-Group`})
    MERGE (p:Product {code: row.Node})
    MERGE (p)-[:IN_GROUP]->(g)
    MERGE (p)-[:IN_SUBGROUP]->(sg)
    """
    graph.query(groups_query)
    print("✅ Product groups and subgroups imported")
    
    # Import plant and storage locations
    plant_storage_query = """
    LOAD CSV WITH HEADERS FROM 'file:///node_types_plant_storage.csv' AS row
    MERGE (pl:Plant {id: row.Plant})
    MERGE (sl:StorageLocation {id: toFloat(row.`Storage Location`)})
    MERGE (p:Product {code: row.Node})
    MERGE (p)-[:PRODUCED_AT]->(pl)
    MERGE (p)-[:STORED_AT]->(sl)
    """
    graph.query(plant_storage_query)
    print("✅ Plant and storage locations imported")

def import_edges(graph, csv_base_path: str):
    """Import all edge data from CSV files"""
    print("🔗 Importing edges...")
    
    # Import product group edges
    group_edges_query = """
    LOAD CSV WITH HEADERS FROM 'file:///edges_product_group.csv' AS row
    MATCH (p1:Product {code: row.node1})
    MATCH (p2:Product {code: row.node2})
    MERGE (p1)-[:SAME_GROUP {group_code: row.GroupCode}]->(p2)
    """
    graph.query(group_edges_query)
    print("✅ Product group edges imported")
    
    # Import product subgroup edges
    subgroup_edges_query = """
    LOAD CSV WITH HEADERS FROM 'file:///edges_product_subgroup.csv' AS row
    MATCH (p1:Product {code: row.node1})
    MATCH (p2:Product {code: row.node2})
    MERGE (p1)-[:SAME_SUBGROUP {subgroup_code: row.SubGroupCode}]->(p2)
    """
    graph.query(subgroup_edges_query)
    print("✅ Product subgroup edges imported")
    
    # Import plant edges
    plant_edges_query = """
    LOAD CSV WITH HEADERS FROM 'file:///edges_plant.csv' AS row
    MATCH (p1:Product {code: row.node1})
    MATCH (p2:Product {code: row.node2})
    MERGE (p1)-[:CO_PRODUCED_AT {plant_id: row.PlantCode}]->(p2)
    """
    graph.query(plant_edges_query)
    print("✅ Plant edges imported")
    
    # Import storage location edges
    storage_edges_query = """
    LOAD CSV WITH HEADERS FROM 'file:///edges_storage.csv' AS row
    MATCH (p1:Product {code: row.node1})
    MATCH (p2:Product {code: row.node2})
    MERGE (p1)-[:CO_STORED_AT {storage_id: toFloat(row.StorageCode)}]->(p2)
    """
    graph.query(storage_edges_query)
    print("✅ Storage location edges imported")

def import_temporal_data(graph, csv_base_path: str):
    """Import temporal data (time series) from CSV files"""
    print("📈 Importing temporal data...")
    
    # Define temporal data types and their files
    temporal_types = [
        ("Production", "production_unit.csv", "Unit"),
        ("Production", "production_weight.csv", "Weight"),
        ("SalesOrder", "sales_order_unit.csv", "Unit"),
        ("SalesOrder", "sales_order_weight.csv", "Weight"),
        ("FactoryIssue", "factory_issue_unit.csv", "Unit"),
        ("FactoryIssue", "factory_issue_weight.csv", "Weight"),
        ("DeliveryToDistributor", "delivery_unit.csv", "Unit"),
        ("DeliveryToDistributor", "delivery_weight.csv", "Weight")
    ]
    
    for data_type, filename, measurement_type in temporal_types:
        print(f"  Importing {data_type} ({measurement_type})...")
        
        # Create time series nodes for each product
        query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
        WITH row, keys(row) as columns
        UNWIND columns as col
        WITH row, col
        WHERE col <> 'Date' AND row[col] IS NOT NULL AND row[col] <> ''
        MATCH (p:Product {{code: col}})
        MERGE (ts:TimeSeries {{
            id: p.code + '_' + '{data_type}' + '_' + '{measurement_type}',
            type: '{data_type}',
            measurement_type: '{measurement_type}',
            product_code: p.code
        }})
        MERGE (p)-[:HAS_TIME_SERIES]->(ts)
        """
        graph.query(query)
        
        # Import time series data points
        data_query = f"""
        LOAD CSV WITH HEADERS FROM 'file:///{filename}' AS row
        WITH row, keys(row) as columns
        UNWIND columns as col
        WITH row, col, row[col] as value
        WHERE col <> 'Date' AND value IS NOT NULL AND value <> ''
        MATCH (p:Product {{code: col}})
        MATCH (ts:TimeSeries {{product_code: p.code, type: '{data_type}', measurement_type: '{measurement_type}'}})
        SET ts += {{
            date: row.Date,
            value: toFloat(value)
        }}
        """
        graph.query(data_query)
    
    print("✅ Temporal data imported")

def copy_csv_files_to_neo4j_import():
    """Copy CSV files to Neo4j's import directory for LOAD CSV"""
    print("📋 Copying CSV files to Neo4j import directory...")
    
    # Neo4j import directory (adjust path as needed)
    neo4j_import_dir = "/var/lib/neo4j/import"  # Default Linux path
    if not os.path.exists(neo4j_import_dir):
        # Try alternative paths
        neo4j_import_dir = "/usr/local/neo4j/import"  # macOS Homebrew
        if not os.path.exists(neo4j_import_dir):
            neo4j_import_dir = "./import"  # Local directory
    
    # Create import directory if it doesn't exist
    os.makedirs(neo4j_import_dir, exist_ok=True)
    
    # Source CSV files
    csv_files = {
        "nodes.csv": "external/RawDataSetSupplyGraph/Nodes/Nodes.csv",
        "node_types_product.csv": "external/RawDataSetSupplyGraph/Nodes/Node Types (Product Group and Subgroup).csv",
        "node_types_plant_storage.csv": "external/RawDataSetSupplyGraph/Nodes/Nodes Type (Plant & Storage).csv",
        "edges_product_group.csv": "external/RawDataSetSupplyGraph/Edges/Edges (Product Group).csv",
        "edges_product_subgroup.csv": "external/RawDataSetSupplyGraph/Edges/Edges (Product Sub-Group).csv",
        "edges_plant.csv": "external/RawDataSetSupplyGraph/Edges/Edges (Plant).csv",
        "edges_storage.csv": "external/RawDataSetSupplyGraph/Edges/Edges (Storage Location).csv",
        "production_unit.csv": "external/RawDataSetSupplyGraph/Temporal Data/Unit/Production .csv",
        "production_weight.csv": "external/RawDataSetSupplyGraph/Temporal Data/Weight/Production .csv",
        "sales_order_unit.csv": "external/RawDataSetSupplyGraph/Temporal Data/Unit/Sales Order.csv",
        "sales_order_weight.csv": "external/RawDataSetSupplyGraph/Temporal Data/Weight/Sales Order .csv",
        "factory_issue_unit.csv": "external/RawDataSetSupplyGraph/Temporal Data/Unit/Factory Issue.csv",
        "factory_issue_weight.csv": "external/RawDataSetSupplyGraph/Temporal Data/Weight/Factory Issue.csv",
        "delivery_unit.csv": "external/RawDataSetSupplyGraph/Temporal Data/Unit/Delivery To distributor.csv",
        "delivery_weight.csv": "external/RawDataSetSupplyGraph/Temporal Data/Weight/Delivery to Distributor.csv"
    }
    
    for dest_name, source_path in csv_files.items():
        if os.path.exists(source_path):
            import shutil
            shutil.copy2(source_path, os.path.join(neo4j_import_dir, dest_name))
            print(f"  ✅ Copied {dest_name}")
        else:
            print(f"  ❌ Source file not found: {source_path}")
    
    print(f"✅ CSV files copied to {neo4j_import_dir}")

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
        
        # Copy CSV files to Neo4j import directory
        copy_csv_files_to_neo4j_import()
        
        # Clear existing database
        clear_database(graph)
        
        # Create schema
        create_supplygraph_schema(graph)
        
        # Import data
        import_nodes(graph, "external/RawDataSetSupplyGraph")
        import_edges(graph, "external/RawDataSetSupplyGraph")
        import_temporal_data(graph, "external/RawDataSetSupplyGraph")
        
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
