#!/usr/bin/env python3
"""
Ingest the SupplyGraph benchmark dataset into Neo4j.

This script reads the SupplyGraph dataset from external/RawDataSetSupplyGraph/
and creates a comprehensive graph database schema that matches the benchmark
dataset structure for supply chain analytics.

Schema:
- (:Product {code}) - Product nodes with codes like SOS008L02P
- (:Group {code}) - Product groups (S, P, A, M, E)
- (:SubGroup {code}) - Product subgroups (SOS, SOP, POV, POP, etc.)
- (:Plant {id}) - Manufacturing plants
- (:StorageLocation {id}) - Storage locations
- (:TimeSeries {type, unit_type}) - Time series data nodes
- Relationships:
  - (Product)-[:IN_GROUP]->(Group)
  - (Product)-[:IN_SUBGROUP]->(SubGroup)
  - (Product)-[:PRODUCED_AT]->(Plant)
  - (Product)-[:STORED_AT]->(StorageLocation)
  - (Product)-[:HAS_TIME_SERIES]->(TimeSeries)
  - (TimeSeries)-[:HAS_VALUE {date, value}]->(Product)
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import json
from solutions.graph import get_graph

# Configuration
RAW_DATA_PATH = "external/RawDataSetSupplyGraph"
BATCH_SIZE = 1000

def get_neo4j_connection():
    """Get Neo4j connection with proper error handling."""
    try:
        graph = get_graph()
        if graph is None:
            print("❌ ERROR: Cannot connect to Neo4j. Check your environment variables.")
            return None
        return graph
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to Neo4j: {e}")
        return None

def clear_database():
    """Clear all existing data from the database."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("🗑️  Clearing existing database...")
    try:
        # Clear all nodes and relationships
        graph.query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared successfully")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to clear database: {e}")
        return False

def create_constraints():
    """Create database constraints for the new schema."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("🔒 Creating database constraints...")
    try:
        constraints = [
            "CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.code IS UNIQUE",
            "CREATE CONSTRAINT group_code IF NOT EXISTS FOR (g:Group) REQUIRE g.code IS UNIQUE",
            "CREATE CONSTRAINT subgroup_code IF NOT EXISTS FOR (sg:SubGroup) REQUIRE sg.code IS UNIQUE",
            "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (pl:Plant) REQUIRE pl.id IS UNIQUE",
            "CREATE CONSTRAINT storage_id IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE sl.id IS UNIQUE",
            "CREATE CONSTRAINT timeseries_id IF NOT EXISTS FOR (ts:TimeSeries) REQUIRE ts.id IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                graph.query(constraint)
            except Exception as e:
                print(f"⚠️  Constraint creation warning: {e}")
        
        print("✅ Constraints created successfully")
        return True
    except Exception as e:
        print(f"❌ ERROR: Failed to create constraints: {e}")
        return False

def ingest_products_and_groups():
    """Ingest product nodes and their group/subgroup classifications."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("📦 Ingesting products and groups...")
    
    try:
        # Read product classifications
        product_groups_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "Nodes", "Node Types (Product Group and Subgroup).csv"))
        
        # Create groups and subgroups
        groups = product_groups_df['Group'].unique()
        subgroups = product_groups_df['Sub-Group'].unique()
        
        # Create Group nodes
        for group_code in groups:
            graph.query(
                "MERGE (g:Group {code: $code})",
                {"code": group_code}
            )
        
        # Create SubGroup nodes
        for subgroup_code in subgroups:
            graph.query(
                "MERGE (sg:SubGroup {code: $code})",
                {"code": subgroup_code}
            )
        
        # Create Product nodes and relationships
        for _, row in product_groups_df.iterrows():
            product_code = row['Node']
            group_code = row['Group']
            subgroup_code = row['Sub-Group']
            
            # Create product node
            graph.query(
                """
                MERGE (p:Product {code: $product_code})
                MERGE (g:Group {code: $group_code})
                MERGE (sg:SubGroup {code: $subgroup_code})
                MERGE (p)-[:IN_GROUP]->(g)
                MERGE (p)-[:IN_SUBGROUP]->(sg)
                """,
                {
                    "product_code": product_code,
                    "group_code": group_code,
                    "subgroup_code": subgroup_code
                }
            )
        
        print(f"✅ Created {len(product_groups_df)} products with {len(groups)} groups and {len(subgroups)} subgroups")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to ingest products and groups: {e}")
        return False

def ingest_plants_and_storage():
    """Ingest plant and storage location data."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("🏭 Ingesting plants and storage locations...")
    
    try:
        # Read plant and storage data
        plant_storage_df = pd.read_csv(os.path.join(RAW_DATA_PATH, "Nodes", "Nodes Type (Plant & Storage).csv"))
        
        # Get unique plants and storage locations
        plants = plant_storage_df['Plant'].unique()
        storage_locations = plant_storage_df['Storage Location'].dropna().unique()
        
        # Create Plant nodes
        for plant_id in plants:
            graph.query(
                "MERGE (pl:Plant {id: $plant_id})",
                {"plant_id": int(plant_id)}
            )
        
        # Create StorageLocation nodes
        for storage_id in storage_locations:
            graph.query(
                "MERGE (sl:StorageLocation {id: $storage_id})",
                {"storage_id": int(storage_id)}
            )
        
        # Create product-plant and product-storage relationships
        for _, row in plant_storage_df.iterrows():
            product_code = row['Node']
            plant_id = int(row['Plant'])
            storage_id = row['Storage Location']
            
            # Product-Plant relationship
            graph.query(
                """
                MATCH (p:Product {code: $product_code})
                MATCH (pl:Plant {id: $plant_id})
                MERGE (p)-[:PRODUCED_AT]->(pl)
                """,
                {
                    "product_code": product_code,
                    "plant_id": plant_id
                }
            )
            
            # Product-Storage relationship (if storage location exists)
            if pd.notna(storage_id):
                graph.query(
                    """
                    MATCH (p:Product {code: $product_code})
                    MATCH (sl:StorageLocation {id: $storage_id})
                    MERGE (p)-[:STORED_AT]->(sl)
                    """,
                    {
                        "product_code": product_code,
                        "storage_id": int(storage_id)
                    }
                )
        
        print(f"✅ Created {len(plants)} plants and {len(storage_locations)} storage locations")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to ingest plants and storage: {e}")
        return False

def ingest_temporal_data():
    """Ingest time series data for production, sales, delivery, and factory issues."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("📈 Ingesting temporal data...")
    
    try:
        # Define time series types
        time_series_types = {
            "Unit": {
                "Production": "production_units",
                "Sales Order": "sales_units", 
                "Delivery To distributor": "delivery_units",
                "Factory Issue": "factory_issue_units"
            },
            "Weight": {
                "Production": "production_weight",
                "Sales Order": "sales_weight",
                "Delivery to Distributor": "delivery_weight", 
                "Factory Issue": "factory_issue_weight"
            }
        }
        
        total_records = 0
        
        for unit_type, series_dict in time_series_types.items():
            for series_name, property_name in series_dict.items():
                print(f"  📊 Processing {unit_type} - {series_name}...")
                
                # Read the CSV file
                file_path = os.path.join(RAW_DATA_PATH, "Temporal Data", unit_type, f"{series_name}.csv")
                if not os.path.exists(file_path):
                    print(f"⚠️  File not found: {file_path}")
                    continue
                
                df = pd.read_csv(file_path)
                
                # Process each date
                for _, row in df.iterrows():
                    date_str = row['Date']
                    try:
                        date_obj = pd.to_datetime(date_str)
                        date_formatted = date_obj.strftime('%Y-%m-%d')
                    except:
                        continue
                    
                    # Process each product column
                    for column in df.columns[1:]:  # Skip the Date column
                        if column == 'Date':
                            continue
                        
                        value = row[column]
                        if pd.isna(value) or value == 0:
                            continue
                        
                        # Create time series node and relationship
                        graph.query(
                            """
                            MATCH (p:Product {code: $product_code})
                            MERGE (ts:TimeSeries {
                                id: $ts_id,
                                type: $series_type,
                                unit_type: $unit_type,
                                property_name: $property_name
                            })
                            MERGE (p)-[:HAS_TIME_SERIES]->(ts)
                            MERGE (ts)-[:HAS_VALUE {date: $date, value: $value}]->(p)
                            """,
                            {
                                "product_code": column,
                                "ts_id": f"{series_name}_{unit_type}_{property_name}",
                                "series_type": series_name,
                                "unit_type": unit_type,
                                "property_name": property_name,
                                "date": date_formatted,
                                "value": float(value)
                            }
                        )
                        total_records += 1
                        
                        # Batch processing for performance
                        if total_records % BATCH_SIZE == 0:
                            print(f"    Processed {total_records} records...")
        
        print(f"✅ Ingested {total_records} temporal data records")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to ingest temporal data: {e}")
        return False

def create_summary_statistics():
    """Create summary statistics for the ingested data."""
    graph = get_neo4j_connection()
    if not graph:
        return False
    
    print("📊 Creating summary statistics...")
    
    try:
        # Get counts
        counts = {}
        queries = {
            "products": "MATCH (p:Product) RETURN count(p) as count",
            "groups": "MATCH (g:Group) RETURN count(g) as count", 
            "subgroups": "MATCH (sg:SubGroup) RETURN count(sg) as count",
            "plants": "MATCH (pl:Plant) RETURN count(pl) as count",
            "storage_locations": "MATCH (sl:StorageLocation) RETURN count(sl) as count",
            "time_series": "MATCH (ts:TimeSeries) RETURN count(ts) as count",
            "relationships": "MATCH ()-[r]->() RETURN count(r) as count"
        }
        
        for name, query in queries.items():
            result = graph.query(query)
            counts[name] = result[0]['count'] if result else 0
        
        print("📈 Database Summary:")
        print(f"  Products: {counts['products']}")
        print(f"  Groups: {counts['groups']}")
        print(f"  SubGroups: {counts['subgroups']}")
        print(f"  Plants: {counts['plants']}")
        print(f"  Storage Locations: {counts['storage_locations']}")
        print(f"  Time Series: {counts['time_series']}")
        print(f"  Relationships: {counts['relationships']}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Failed to create summary statistics: {e}")
        return False

def main():
    """Main ingestion function."""
    print("🚀 Starting SupplyGraph dataset ingestion...")
    print("=" * 60)
    
    # Check if raw data exists
    if not os.path.exists(RAW_DATA_PATH):
        print(f"❌ ERROR: Raw data path not found: {RAW_DATA_PATH}")
        return False
    
    # Clear existing database
    if not clear_database():
        return False
    
    # Create constraints
    if not create_constraints():
        return False
    
    # Ingest data
    steps = [
        ("Products and Groups", ingest_products_and_groups),
        ("Plants and Storage", ingest_plants_and_storage),
        ("Temporal Data", ingest_temporal_data),
        ("Summary Statistics", create_summary_statistics)
    ]
    
    for step_name, step_func in steps:
        print(f"\n🔄 Step: {step_name}")
        print("-" * 40)
        if not step_func():
            print(f"❌ Failed at step: {step_name}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ SupplyGraph dataset ingestion completed successfully!")
    print("🎯 The database now contains the complete SupplyGraph benchmark dataset.")
    print("📊 You can now run supply chain analytics queries against this data.")
    
    return True

if __name__ == "__main__":
    main()
