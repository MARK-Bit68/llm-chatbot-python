#!/usr/bin/env python3
"""
Enhanced Graph Import for Excel Files
Intelligently processes Excel files and creates graph structures from any Excel format
"""

import pandas as pd
import os
import json
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime


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


def get_graph_connection():
    """Get Neo4j connection with error handling"""
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        print("✅ Neo4j connection established")
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        return None


def clean_column_name(col_name):
    """Clean column names for Neo4j property names"""
    if pd.isna(col_name):
        return "unknown_column"
    
    clean_name = str(col_name).strip()
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', clean_name)
    clean_name = re.sub(r'_+', '_', clean_name)
    clean_name = clean_name.strip('_')
    
    if clean_name and not clean_name[0].isalpha():
        clean_name = 'col_' + clean_name
    
    return clean_name.lower()


def clear_graph_database(graph):
    """Clear all existing data from the graph database"""
    try:
        print("🧹 Clearing existing graph data...")
        graph.query("MATCH (n) DETACH DELETE n")
        print("✅ Cleared existing graph data")
    except Exception as e:
        print(f"❌ Error clearing graph: {e}")


def analyze_excel_structure(excel_file_path: str) -> Dict[str, Any]:
    """Analyze Excel file structure to understand the data format"""
    try:
        excel_file = pd.ExcelFile(excel_file_path)
        analysis = {
            "sheet_names": excel_file.sheet_names,
            "sheet_analysis": {},
            "total_sheets": len(excel_file.sheet_names),
            "suggested_mapping": {}
        }
        
        print(f"📊 Analyzing Excel structure: {len(excel_file.sheet_names)} sheets")
        
        for sheet_name in excel_file.sheet_names:
            try:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                
                sheet_info = {
                    "rows": len(df),
                    "columns": len(df.columns),
                    "column_names": list(df.columns),
                    "has_data": len(df) > 0,
                    "sample_data": {}
                }
                
                # Get sample data from first few rows
                if len(df) > 0:
                    for col in df.columns[:5]:  # First 5 columns
                        sample_vals = df[col].dropna().head(3).tolist()
                        sheet_info["sample_data"][col] = [str(v) for v in sample_vals]
                
                analysis["sheet_analysis"][sheet_name] = sheet_info
                
                # Suggest mapping based on sheet name and content
                sheet_lower = sheet_name.lower()
                if "relationship" in sheet_lower or "edge" in sheet_lower or "connect" in sheet_lower or "_rel" in sheet_lower:
                    analysis["suggested_mapping"][sheet_name] = "relationships"
                elif "node" in sheet_lower or "product" in sheet_lower and "relationship" not in sheet_lower:
                    analysis["suggested_mapping"][sheet_name] = "nodes"
                elif "group" in sheet_lower or "category" in sheet_lower:
                    analysis["suggested_mapping"][sheet_name] = "categories"
                elif any(month in sheet_lower for month in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]):
                    analysis["suggested_mapping"][sheet_name] = "temporal_data"
                else:
                    # Look at column names to determine if it's relationships
                    if len(df.columns) >= 2:
                        col_names = [str(col).lower() for col in df.columns[:4]]
                        if any(src in name for name in col_names for src in ["source", "from", "node1"]) and \
                           any(tgt in name for name in col_names for tgt in ["target", "to", "node2"]):
                            analysis["suggested_mapping"][sheet_name] = "relationships"
                        else:
                            analysis["suggested_mapping"][sheet_name] = "general_data"
                    else:
                        analysis["suggested_mapping"][sheet_name] = "general_data"
                    
            except Exception as e:
                print(f"  - Error analyzing sheet {sheet_name}: {e}")
                analysis["sheet_analysis"][sheet_name] = {"error": str(e)}
        
        return analysis
        
    except Exception as e:
        print(f"❌ Error analyzing Excel structure: {e}")
        return {"error": str(e)}


def create_intelligent_graph_schema(data_analysis: Dict[str, Any], excel_file_path: str, graph) -> Dict[str, Any]:
    """Create intelligent graph schema based on Excel analysis"""
    
    results = {
        "nodes_created": {},
        "relationships_created": {},
        "sheets_processed": 0,
        "total_rows_processed": 0,
        "errors": []
    }
    
    excel_file = pd.ExcelFile(excel_file_path)
    
    # Process each sheet based on suggested mapping
    for sheet_name, mapping_type in data_analysis.get("suggested_mapping", {}).items():
        try:
            print(f"\n📋 Processing sheet: {sheet_name} (type: {mapping_type})")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            if len(df) == 0:
                print(f"  - Skipping empty sheet: {sheet_name}")
                continue
                
            # Clean column names
            original_columns = df.columns.copy()
            df.columns = [clean_column_name(col) for col in df.columns]
            
            if mapping_type == "nodes":
                processed = process_nodes_sheet(df, sheet_name, graph)
                results["nodes_created"].update(processed)
                
            elif mapping_type == "relationships":
                processed = process_relationships_sheet(df, sheet_name, graph)
                results["relationships_created"].update(processed)
                
            elif mapping_type == "categories":
                processed = process_categories_sheet(df, sheet_name, graph)
                results["nodes_created"].update(processed)
                
            elif mapping_type == "temporal_data":
                processed = process_temporal_sheet(df, sheet_name, graph)
                results["nodes_created"].update(processed)
                
            else:  # general_data
                processed = process_general_sheet(df, sheet_name, graph)
                results["nodes_created"].update(processed)
            
            results["sheets_processed"] += 1
            results["total_rows_processed"] += len(df)
            
        except Exception as e:
            error_msg = f"Error processing sheet {sheet_name}: {e}"
            print(f"  - ❌ {error_msg}")
            results["errors"].append(error_msg)
    
    return results


def process_nodes_sheet(df: pd.DataFrame, sheet_name: str, graph) -> Dict[str, int]:
    """Process a sheet that contains node data"""
    created = {}
    
    # Find ID column (first column or one containing 'id', 'code', 'sku')
    id_column = df.columns[0]
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['id', 'code', 'sku', 'node']):
            id_column = col
            break
    
    print(f"  - Using ID column: {id_column}")
    
    # Determine node type from sheet name
    node_type = "Product"
    if "group" in sheet_name.lower():
        node_type = "Group"
    elif "category" in sheet_name.lower():
        node_type = "Category"
    elif "plant" in sheet_name.lower():
        node_type = "Plant"
    elif "storage" in sheet_name.lower():
        node_type = "StorageLocation"
    
    # Create nodes
    for _, row in df.iterrows():
        node_id = str(row[id_column]).strip()
        if not node_id or node_id.lower() in ['nan', 'none', '']:
            continue
            
        # Build properties dict
        properties = {}
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                properties[col] = str(value).strip()
        
        # Create node
        query = f"""
        MERGE (n:{node_type} {{id: $node_id}})
        SET n += $properties
        """
        
        try:
            graph.query(query, {
                "node_id": node_id,
                "properties": properties
            })
            
            if node_type not in created:
                created[node_type] = 0
            created[node_type] += 1
            
        except Exception as e:
            print(f"    - Error creating node {node_id}: {e}")
    
    print(f"  - Created {sum(created.values())} {node_type} nodes")
    return created


def process_relationships_sheet(df: pd.DataFrame, sheet_name: str, graph) -> Dict[str, int]:
    """Process a sheet that contains relationship data"""
    created = {}
    
    # Find source and target columns
    source_col = None
    target_col = None
    
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in ['node1', 'source', 'from']) and source_col is None:
            source_col = col
        elif any(keyword in col_lower for keyword in ['node2', 'target', 'to']) and target_col is None:
            target_col = col
    
    # Fallback to first two columns
    if source_col is None or target_col is None:
        if len(df.columns) >= 2:
            source_col = df.columns[0]
            target_col = df.columns[1]
        else:
            print(f"  - Cannot find source/target columns in {sheet_name}")
            return created
    
    print(f"  - Using source: {source_col}, target: {target_col}")
    
    # Determine relationship type from sheet name or column values
    rel_type = "RELATED_TO"
    if "group" in sheet_name.lower():
        rel_type = "SAME_GROUP"
    elif "plant" in sheet_name.lower():
        rel_type = "CO_PRODUCED_AT"
    elif "storage" in sheet_name.lower():
        rel_type = "CO_STORED_AT"
    elif "supply" in sheet_name.lower():
        rel_type = "SUPPLIES"
    else:
        # Look for relationship type column
        for col in df.columns:
            if "type" in col.lower() or "relationship" in col.lower():
                # Use the most common value as relationship type
                type_values = df[col].dropna().value_counts()
                if len(type_values) > 0:
                    most_common = type_values.index[0]
                    rel_type = str(most_common).upper().replace(' ', '_')
                break
    
    # Create relationships
    for _, row in df.iterrows():
        source_id = str(row[source_col]).strip()
        target_id = str(row[target_col]).strip()
        
        if not source_id or not target_id or source_id == target_id:
            continue
        
        # Build properties dict and look for specific relationship type
        properties = {}
        specific_rel_type = rel_type
        
        for col in df.columns:
            if col not in [source_col, target_col]:
                value = row[col]
                if pd.notna(value) and str(value).strip():
                    # Check if this is a relationship type column
                    if "type" in col.lower() or "relationship" in col.lower():
                        specific_rel_type = str(value).upper().replace(' ', '_')
                    else:
                        properties[col] = str(value).strip()
        
        # Create relationship - try multiple ways to match nodes
        query = f"""
        MATCH (a)
        WHERE a.id = $source_id OR a.product_id = $source_id OR a.code = $source_id
        MATCH (b)
        WHERE b.id = $target_id OR b.product_id = $target_id OR b.code = $target_id
        MERGE (a)-[r:{specific_rel_type}]->(b)
        SET r += $properties
        """
        
        try:
            graph.query(query, {
                "source_id": source_id,
                "target_id": target_id,
                "properties": properties
            })
            
            if specific_rel_type not in created:
                created[specific_rel_type] = 0
            created[specific_rel_type] += 1
            
        except Exception as e:
            print(f"    - Error creating relationship {source_id}->{target_id}: {e}")
    
    print(f"  - Created {sum(created.values())} relationships")
    return created


def process_categories_sheet(df: pd.DataFrame, sheet_name: str, graph) -> Dict[str, int]:
    """Process a sheet that contains category/classification data"""
    created = {}
    
    # This is similar to nodes but with specific category handling
    id_column = df.columns[0]
    
    # Look for category columns
    category_columns = []
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['group', 'category', 'class', 'type']):
            category_columns.append(col)
    
    # Create category nodes and relationships
    for _, row in df.iterrows():
        item_id = str(row[id_column]).strip()
        if not item_id:
            continue
        
        # Create relationships to categories
        for cat_col in category_columns:
            cat_value = str(row[cat_col]).strip()
            if not cat_value or cat_value.lower() in ['nan', 'none', '']:
                continue
            
            # Determine category type
            cat_type = "Category"
            if "group" in cat_col.lower():
                cat_type = "Group"
            elif "subgroup" in cat_col.lower():
                cat_type = "SubGroup"
            
            # Create category node and relationship
            query = f"""
            MERGE (item {{id: $item_id}})
            MERGE (cat:{cat_type} {{name: $cat_name}})
            MERGE (item)-[:BELONGS_TO_{cat_type.upper()}]->(cat)
            """
            
            try:
                graph.query(query, {
                    "item_id": item_id,
                    "cat_name": cat_value
                })
                
                if cat_type not in created:
                    created[cat_type] = 0
                created[cat_type] += 1
                
            except Exception as e:
                print(f"    - Error creating category relationship {item_id}->{cat_value}: {e}")
    
    return created


def process_temporal_sheet(df: pd.DataFrame, sheet_name: str, graph) -> Dict[str, int]:
    """Process a sheet that contains temporal/time series data"""
    created = {}
    
    # Find date column
    date_column = None
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['date', 'time', 'month', 'year']):
            date_column = col
            break
    
    if date_column is None:
        print(f"  - No date column found in temporal sheet {sheet_name}")
        return created
    
    # Process temporal data
    data_columns = [col for col in df.columns if col != date_column]
    
    for col in data_columns:
        # Create time series for each data column (treating it as an entity)
        ts_data = {}
        for _, row in df.iterrows():
            date_val = row[date_column]
            data_val = row[col]
            
            if pd.notna(date_val) and pd.notna(data_val):
                ts_data[str(date_val)] = str(data_val)
        
        if ts_data:
            query = """
            MERGE (ts:TimeSeries {entity: $entity, sheet: $sheet})
            SET ts.data = $data, ts.last_updated = $timestamp
            """
            
            try:
                graph.query(query, {
                    "entity": col,
                    "sheet": sheet_name,
                    "data": json.dumps(ts_data),
                    "timestamp": datetime.now().isoformat()
                })
                
                if "TimeSeries" not in created:
                    created["TimeSeries"] = 0
                created["TimeSeries"] += 1
                
            except Exception as e:
                print(f"    - Error creating time series for {col}: {e}")
    
    return created


def process_general_sheet(df: pd.DataFrame, sheet_name: str, graph) -> Dict[str, int]:
    """Process a general data sheet"""
    created = {}
    
    # Treat as generic entities
    id_column = df.columns[0]
    
    for _, row in df.iterrows():
        entity_id = str(row[id_column]).strip()
        if not entity_id:
            continue
        
        # Build properties dict
        properties = {}
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                properties[col] = str(value).strip()
        
        # Create generic entity
        query = """
        MERGE (e:Entity {id: $entity_id, source_sheet: $sheet})
        SET e += $properties
        """
        
        try:
            graph.query(query, {
                "entity_id": entity_id,
                "sheet": sheet_name,
                "properties": properties
            })
            
            if "Entity" not in created:
                created["Entity"] = 0
            created["Entity"] += 1
            
        except Exception as e:
            print(f"    - Error creating entity {entity_id}: {e}")
    
    return created


def validate_connectivity(graph) -> Dict[str, Any]:
    """Validate graph connectivity and return statistics"""
    try:
        # Count total nodes
        total_nodes_result = graph.query("MATCH (n) RETURN count(n) as total")
        total_nodes = total_nodes_result[0]["total"] if total_nodes_result else 0
        
        # Count total relationships
        total_rels_result = graph.query("MATCH ()-[r]->() RETURN count(r) as total")
        total_relationships = total_rels_result[0]["total"] if total_rels_result else 0
        
        # Count connected nodes (nodes with at least one relationship)
        connected_nodes_result = graph.query("""
            MATCH (n)
            WHERE (n)--()
            RETURN count(n) as connected
        """)
        connected_nodes = connected_nodes_result[0]["connected"] if connected_nodes_result else 0
        
        # Calculate isolated nodes
        isolated_nodes = total_nodes - connected_nodes
        
        # Calculate connectivity percentage
        connectivity_percentage = (connected_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        return {
            "total_nodes": total_nodes,
            "connected_nodes": connected_nodes,
            "isolated_nodes": isolated_nodes,
            "total_relationships": total_relationships,
            "connectivity_percentage": connectivity_percentage
        }
        
    except Exception as e:
        print(f"❌ Error validating connectivity: {e}")
        return {
            "total_nodes": 0,
            "connected_nodes": 0,
            "isolated_nodes": 0,
            "total_relationships": 0,
            "connectivity_percentage": 0
        }


def import_enhanced_fmcg_graph(excel_file_path: str) -> Dict[str, Any]:
    """
    Main function to import Excel file and create enhanced graph structure
    """
    print(f"📁 Importing enhanced graph from: {excel_file_path}")
    
    # Connect to Neo4j
    graph = get_graph_connection()
    if graph is None:
        return {"error": "Neo4j connection failed"}
    
    # Clear existing data
    clear_graph_database(graph)
    
    try:
        # Analyze Excel structure
        print("🔍 Analyzing Excel file structure...")
        analysis = analyze_excel_structure(excel_file_path)
        
        if "error" in analysis:
            return {"error": f"Excel analysis failed: {analysis['error']}"}
        
        print(f"📊 Found {analysis['total_sheets']} sheets to process")
        
        # Create intelligent graph schema
        print("🏗️ Creating intelligent graph schema...")
        results = create_intelligent_graph_schema(analysis, excel_file_path, graph)
        
        # Validate connectivity
        print("🔗 Validating graph connectivity...")
        connectivity = validate_connectivity(graph)
        
        # Compile final results
        final_results = {
            "nodes_created": results["nodes_created"],
            "relationships_created": results["relationships_created"],
            "connectivity": connectivity,
            "sheets_processed": results["sheets_processed"],
            "total_rows_processed": results["total_rows_processed"],
            "excel_analysis": analysis,
            "errors": results["errors"]
        }
        
        print(f"✅ Import complete: {connectivity['total_nodes']} nodes, {connectivity['total_relationships']} relationships")
        print(f"✅ Connectivity: {connectivity['connectivity_percentage']:.1f}% ({connectivity['connected_nodes']}/{connectivity['total_nodes']} nodes connected)")
        
        return final_results
        
    except Exception as e:
        error_msg = f"Import failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}


if __name__ == "__main__":
    # Test import
    result = import_enhanced_fmcg_graph("Enhanced_FMCG_SOP_Dataset.xlsx")
    print("Import result:", json.dumps(result, indent=2))