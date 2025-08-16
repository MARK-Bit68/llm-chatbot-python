#!/usr/bin/env python3
"""
Temporary script to analyze graph structure and identify isolated nodes.
This script will be deleted after analysis is complete.
"""

import pandas as pd
import os
from solutions.graph import get_graph

def analyze_node_connections():
    """Analyze which nodes have connections and which are isolated"""
    print("🔍 Analyzing graph structure...")
    
    # Read the node files
    nodes_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes.csv")
    node_types_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Node Types (Product Group and Subgroup).csv")
    plant_storage_df = pd.read_csv("external/RawDataSetSupplyGraph/Nodes/Nodes Type (Plant & Storage).csv")
    
    # Read edge files
    group_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Group).csv")
    subgroup_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Product Sub-Group).csv")
    plant_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Plant).csv")
    storage_edges_df = pd.read_csv("external/RawDataSetSupplyGraph/Edges/Edges (Storage Location).csv")
    
    print(f"📊 Dataset Summary:")
    print(f"  - Total Products: {len(nodes_df)}")
    print(f"  - Products with Group/Subgroup: {len(node_types_df)}")
    print(f"  - Products with Plant/Storage: {len(plant_storage_df)}")
    print(f"  - Group Edges: {len(group_edges_df)}")
    print(f"  - Subgroup Edges: {len(subgroup_edges_df)}")
    print(f"  - Plant Edges: {len(plant_edges_df)}")
    print(f"  - Storage Edges: {len(storage_edges_df)}")
    
    # Find products that appear in different files
    all_products = set(nodes_df['Node'].tolist())
    products_with_groups = set(node_types_df['Node'].tolist())
    products_with_plants = set(plant_storage_df['Node'].tolist())
    
    # Products in group edges
    group_edge_products = set(group_edges_df['node1'].tolist() + group_edges_df['node2'].tolist())
    subgroup_edge_products = set(subgroup_edges_df['node1'].tolist() + subgroup_edges_df['node2'].tolist())
    plant_edge_products = set(plant_edges_df['node1'].tolist() + plant_edges_df['node2'].tolist())
    storage_edge_products = set(storage_edges_df['node1'].tolist() + storage_edges_df['node2'].tolist())
    
    print(f"\n🔗 Product Coverage Analysis:")
    print(f"  - Products with Group/Subgroup classification: {len(products_with_groups)}")
    print(f"  - Products with Plant/Storage classification: {len(products_with_plants)}")
    print(f"  - Products in Group edges: {len(group_edge_products)}")
    print(f"  - Products in Subgroup edges: {len(subgroup_edge_products)}")
    print(f"  - Products in Plant edges: {len(plant_edge_products)}")
    print(f"  - Products in Storage edges: {len(storage_edge_products)}")
    
    # Find isolated products
    products_with_any_edges = group_edge_products | subgroup_edge_products | plant_edge_products | storage_edge_products
    isolated_products = all_products - products_with_any_edges
    
    print(f"\n🚨 ISOLATED PRODUCTS ({len(isolated_products)}):")
    for product in sorted(isolated_products):
        print(f"  - {product}")
    
    # Find products that have classification but no edges
    products_with_classification = products_with_groups | products_with_plants
    products_with_classification_but_no_edges = products_with_classification - products_with_any_edges
    
    print(f"\n⚠️  PRODUCTS WITH CLASSIFICATION BUT NO EDGES ({len(products_with_classification_but_no_edges)}):")
    for product in sorted(products_with_classification_but_no_edges):
        print(f"  - {product}")
    
    # Analyze plant and storage nodes
    unique_plants = set(plant_storage_df['Plant'].dropna().tolist())
    unique_storage = set(plant_storage_df['Storage Location'].dropna().tolist())
    
    print(f"\n🏭 Plant and Storage Analysis:")
    print(f"  - Unique Plants: {len(unique_plants)}")
    print(f"  - Unique Storage Locations: {len(unique_storage)}")
    print(f"  - Plants in edges: {len(set(plant_edges_df['node1'].tolist() + plant_edges_df['node2'].tolist()))}")
    print(f"  - Storage in edges: {len(set(storage_edges_df['node1'].tolist() + storage_edges_df['node2'].tolist()))}")
    
    # Check which plants/storage appear in edges
    plants_in_edges = set(plant_edges_df['node1'].tolist() + plant_edges_df['node2'].tolist())
    storage_in_edges = set(storage_edges_df['node1'].tolist() + storage_edges_df['node2'].tolist())
    
    isolated_plants = unique_plants - plants_in_edges
    isolated_storage = unique_storage - storage_in_edges
    
    print(f"\n🏭 ISOLATED PLANTS ({len(isolated_plants)}):")
    for plant in sorted(isolated_plants):
        print(f"  - {plant}")
    
    print(f"\n📦 ISOLATED STORAGE LOCATIONS ({len(isolated_storage)}):")
    for storage in sorted(isolated_storage):
        print(f"  - {storage}")
    
    return {
        'isolated_products': isolated_products,
        'isolated_plants': isolated_plants,
        'isolated_storage': isolated_storage,
        'products_with_classification_but_no_edges': products_with_classification_but_no_edges
    }

def analyze_neo4j_graph():
    """Analyze the actual Neo4j graph to see what's in the database"""
    print("\n🗄️  Analyzing Neo4j Graph...")
    
    try:
        graph = get_graph()
        
        # Get node counts by type
        node_counts = graph.query("""
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
        """)
        
        print("📊 Node counts by type:")
        for record in node_counts:
            print(f"  - {record['node_type']}: {record['count']}")
        
        # Get relationship counts by type
        rel_counts = graph.query("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        print("\n🔗 Relationship counts by type:")
        for record in rel_counts:
            print(f"  - {record['rel_type']}: {record['count']}")
        
        # Find isolated nodes (nodes with no relationships)
        isolated_nodes = graph.query("""
            MATCH (n)
            WHERE NOT (n)--()
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
        """)
        
        print("\n🚨 Isolated nodes by type:")
        for record in isolated_nodes:
            print(f"  - {record['node_type']}: {record['count']}")
        
        # Get sample isolated nodes
        sample_isolated = graph.query("""
            MATCH (n)
            WHERE NOT (n)--()
            RETURN labels(n)[0] as node_type, n.code as code, n.id as id
            LIMIT 10
        """)
        
        print("\n🔍 Sample isolated nodes:")
        for record in sample_isolated:
            identifier = record['code'] or record['id']
            print(f"  - {record['node_type']}: {identifier}")
        
        # Check connectivity of different node types
        connectivity = graph.query("""
            MATCH (n)
            WITH labels(n)[0] as node_type, n
            OPTIONAL MATCH (n)-[r]-()
            RETURN node_type, 
                   count(DISTINCT n) as total_nodes,
                   count(DISTINCT CASE WHEN r IS NOT NULL THEN n END) as connected_nodes,
                   count(DISTINCT CASE WHEN r IS NULL THEN n END) as isolated_nodes
            ORDER BY isolated_nodes DESC
        """)
        
        print("\n📈 Connectivity analysis:")
        for record in connectivity:
            isolation_rate = (record['isolated_nodes'] / record['total_nodes']) * 100
            print(f"  - {record['node_type']}: {record['isolated_nodes']}/{record['total_nodes']} isolated ({isolation_rate:.1f}%)")
        
    except Exception as e:
        print(f"❌ Error analyzing Neo4j graph: {e}")

if __name__ == "__main__":
    analyze_node_connections()
    analyze_neo4j_graph()
