#!/usr/bin/env python3
"""
Enhanced Excel Ingestion for FMCG S&OP Data
Processes 100 SKUs with proper supply/inventory data handling
"""

import pandas as pd
import streamlit as st
from llm import get_embeddings
import json
import re
import time

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

def get_graph_connection():
    """Get Neo4j connection with error handling"""
    try:
        from langchain_neo4j import Neo4jGraph
        import os
        
        def get_neo4j_config(key, default=""):
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
        
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        return None

def create_enhanced_graph_schema(sku_data, graph):
    """Create enhanced graph schema with proper supply/inventory data"""
    for sku_id, data in sku_data.items():
        try:
            # Create SKU node
            sku_query = """
            MERGE (sku:SKU {sku_id: $sku_id, name: $name})
            """
            graph.query(sku_query, {
                'sku_id': sku_id,
                'name': data['all_properties'].get('product_name', f'Product {sku_id}')
            })

            # Create Category node and relationship
            category = data['all_properties'].get('category', 'Unknown')
            category_query = """
            MERGE (cat:Category {name: $category})
            MERGE (sku)-[:BELONGS_TO_CATEGORY]->(cat)
            """
            graph.query(category_query, {
                'category': category,
                'sku_id': sku_id
            })

            # Create Demand Plan node with monthly data
            monthly_demand = {}
            for key, value in data['all_properties'].items():
                if key.startswith('demand_plan_jan-') or key.startswith('demand_plan_feb-') or key.startswith('demand_plan_mar-') or key.startswith('demand_plan_apr-') or key.startswith('demand_plan_may-') or key.startswith('demand_plan_jun-') or key.startswith('demand_plan_jul-') or key.startswith('demand_plan_aug-') or key.startswith('demand_plan_sep-') or key.startswith('demand_plan_oct-') or key.startswith('demand_plan_nov-') or key.startswith('demand_plan_dec-'):
                    # Extract month name from key
                    month_key = key.replace('demand_plan_', '')
                    monthly_demand[month_key] = value
            
            demand_plan_data = json.dumps(monthly_demand) if monthly_demand else "Unknown"
            demand_query = """
            MERGE (dp:DemandPlan {sku_id: $sku_id, monthly_data: $demand_plan})
            MERGE (sku)-[:HAS_DEMAND_PLAN]->(dp)
            """
            graph.query(demand_query, {
                'demand_plan': demand_plan_data,
                'sku_id': sku_id
            })

            # Create Supply Plan node with monthly data
            monthly_supply = {}
            for key, value in data['all_properties'].items():
                if key.startswith('supply_plan_jan-') or key.startswith('supply_plan_feb-') or key.startswith('supply_plan_mar-') or key.startswith('supply_plan_apr-') or key.startswith('supply_plan_may-') or key.startswith('supply_plan_jun-') or key.startswith('supply_plan_jul-') or key.startswith('supply_plan_aug-') or key.startswith('supply_plan_sep-') or key.startswith('supply_plan_oct-') or key.startswith('supply_plan_nov-') or key.startswith('supply_plan_dec-'):
                    # Extract month name from key
                    month_key = key.replace('supply_plan_', '')
                    monthly_supply[month_key] = value
            
            supply_plan_data = json.dumps(monthly_supply) if monthly_supply else "Unknown"
            supply_query = """
            MERGE (sp:SupplyPlan {sku_id: $sku_id, monthly_data: $supply_plan})
            MERGE (sku)-[:HAS_SUPPLY_PLAN]->(sp)
            """
            graph.query(supply_query, {
                'supply_plan': supply_plan_data,
                'sku_id': sku_id
            })

            # Create Inventory node with monthly data
            monthly_inventory = {}
            for key, value in data['all_properties'].items():
                if key.startswith('inventory_plan_jan-') or key.startswith('inventory_plan_feb-') or key.startswith('inventory_plan_mar-') or key.startswith('inventory_plan_apr-') or key.startswith('inventory_plan_may-') or key.startswith('inventory_plan_jun-') or key.startswith('inventory_plan_jul-') or key.startswith('inventory_plan_aug-') or key.startswith('inventory_plan_sep-') or key.startswith('inventory_plan_oct-') or key.startswith('inventory_plan_nov-') or key.startswith('inventory_plan_dec-'):
                    # Extract month name from key
                    month_key = key.replace('inventory_plan_', '')
                    monthly_inventory[month_key] = value
            
            inventory_data = json.dumps(monthly_inventory) if monthly_inventory else "Unknown"
            inventory_query = """
            MERGE (inv:Inventory {sku_id: $sku_id, monthly_data: $inventory})
            MERGE (sku)-[:HAS_INVENTORY]->(inv)
            """
            graph.query(inventory_query, {
                'inventory': inventory_data,
                'sku_id': sku_id
            })

        except Exception as e:
            print(f"Error creating graph schema for SKU {sku_id}: {e}")
            continue

def extract_enhanced_fmcg_data(excel_file_path, max_skus=100):
    """
    Extract FMCG S&OP data and transform into enhanced graph schema
    """
    print(f"🚀 Enhanced FMCG S&OP data extraction from {excel_file_path}")
    print(f"📊 Processing up to {max_skus} SKUs...")
    
    # Read all sheets
    excel_file = pd.ExcelFile(excel_file_path)
    print(f"Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
    
    # Connect to Neo4j
    graph = get_graph_connection()
    if graph is None:
        return {
            'total_rows': 0,
            'unique_skus': 0,
            'nodes_created': 0,
            'error': 'Neo4j not available'
        }
    
    # Use embeddings from llm module
    try:
        embeddings_instance = get_embeddings()
        if not embeddings_instance:
            print("Warning: Embeddings not available, skipping embedding creation")
            pass
    except Exception as e:
        print(f"Error with embeddings: {e}")
        return {
            'total_rows': 0,
            'unique_skus': 0,
            'nodes_created': 0,
            'error': f'Embeddings error: {e}'
        }
    
    # Track all SKUs and their data
    sku_data = {}
    total_rows_processed = 0
    
    # Process each sheet
    for sheet_name in excel_file.sheet_names:
        print(f"\nProcessing sheet: {sheet_name}")
        
        try:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"  - Shape: {df.shape}")
            print(f"  - Columns: {list(df.columns)}")
            
            # Find SKU column (first column or contains 'sku')
            sku_column = None
            for col in df.columns:
                if 'sku' in str(col).lower():
                    sku_column = col
                    break
            
            if sku_column is None:
                sku_column = df.columns[0]
                print(f"  - Using first column as SKU: {sku_column}")
            else:
                print(f"  - Found SKU column: {sku_column}")
            
            # Clean column names
            original_columns = df.columns.copy()
            df.columns = [clean_column_name(col) for col in df.columns]
            column_mapping = dict(zip(original_columns, df.columns))
            
            # Process only first max_skus rows
            for index, row in df.head(max_skus).iterrows():
                sku_id = str(row.iloc[0]).strip()  # First column
                
                # Skip empty or invalid SKUs
                if not sku_id or sku_id.lower() in ['nan', 'none', '', 'sku', 'sku code']:
                    continue
                
                if sku_id not in sku_data:
                    sku_data[sku_id] = {
                        'sku_id': sku_id,
                        'sheets': {},
                        'all_properties': {},
                        'sheet_count': 0
                    }
                
                # Store sheet-specific data
                row_dict = {}
                for i, (orig_col, clean_col) in enumerate(column_mapping.items()):
                    value = row.iloc[i]
                    if pd.notna(value) and str(value).strip():
                        row_dict[clean_col] = str(value).strip()
                        row_dict[f"{clean_col}_original_name"] = orig_col
                
                sku_data[sku_id]['sheets'][sheet_name.lower().replace(' ', '_')] = row_dict
                sku_data[sku_id]['sheet_count'] += 1
                
                # Merge properties with sheet-specific prefixes for monthly data
                for col, value in row_dict.items():
                    if not col.endswith('_original_name'):
                        # For monthly data, store with sheet prefix
                        if any(month in col for month in ['jan-', 'feb-', 'mar-', 'apr-', 'may-', 'jun-', 'jul-', 'aug-', 'sep-', 'oct-', 'nov-', 'dec-']):
                            sheet_prefix = sheet_name.lower().replace(' ', '_')
                            prefixed_col = f"{sheet_prefix}_{col}"
                            sku_data[sku_id]['all_properties'][prefixed_col] = value
                        else:
                            # For non-monthly data, merge as before
                            if col not in sku_data[sku_id]['all_properties']:
                                sku_data[sku_id]['all_properties'][col] = value
                            else:
                                existing = sku_data[sku_id]['all_properties'][col]
                                sku_data[sku_id]['all_properties'][col] = f"{existing} | {sheet_name}: {value}"
                
                total_rows_processed += 1
                
        except Exception as e:
            print(f"  - Error processing sheet {sheet_name}: {e}")
            continue
    
    print(f"\nTotal rows processed: {total_rows_processed}")
    print(f"Unique SKUs found: {len(sku_data)}")
    
    # Create enhanced graph schema
    create_enhanced_graph_schema(sku_data, graph)
    
    # Create embeddings for each SKU
    nodes_created = 0
    for sku_id, data in sku_data.items():
        try:
            # Extract monthly data for this SKU
            monthly_demand = {}
            monthly_supply = {}
            monthly_inventory = {}
            
            for key, value in data['all_properties'].items():
                if key.startswith('demand_plan_jan-') or key.startswith('demand_plan_feb-') or key.startswith('demand_plan_mar-') or key.startswith('demand_plan_apr-') or key.startswith('demand_plan_may-') or key.startswith('demand_plan_jun-') or key.startswith('demand_plan_jul-') or key.startswith('demand_plan_aug-') or key.startswith('demand_plan_sep-') or key.startswith('demand_plan_oct-') or key.startswith('demand_plan_nov-') or key.startswith('demand_plan_dec-'):
                    month_key = key.replace('demand_plan_', '')
                    monthly_demand[month_key] = value
            
            for key, value in data['all_properties'].items():
                if key.startswith('supply_plan_jan-') or key.startswith('supply_plan_feb-') or key.startswith('supply_plan_mar-') or key.startswith('supply_plan_apr-') or key.startswith('supply_plan_may-') or key.startswith('supply_plan_jun-') or key.startswith('supply_plan_jul-') or key.startswith('supply_plan_aug-') or key.startswith('supply_plan_sep-') or key.startswith('supply_plan_oct-') or key.startswith('supply_plan_nov-') or key.startswith('supply_plan_dec-'):
                    month_key = key.replace('supply_plan_', '')
                    monthly_supply[month_key] = value
            
            for key, value in data['all_properties'].items():
                if key.startswith('inventory_plan_jan-') or key.startswith('inventory_plan_feb-') or key.startswith('inventory_plan_mar-') or key.startswith('inventory_plan_apr-') or key.startswith('inventory_plan_may-') or key.startswith('inventory_plan_jun-') or key.startswith('inventory_plan_jul-') or key.startswith('inventory_plan_aug-') or key.startswith('inventory_plan_sep-') or key.startswith('inventory_plan_oct-') or key.startswith('inventory_plan_nov-') or key.startswith('inventory_plan_dec-'):
                    month_key = key.replace('inventory_plan_', '')
                    monthly_inventory[month_key] = value
            
            # Create text representation for embeddings
            plot_parts = []
            for key, value in data['all_properties'].items():
                if key.lower() not in ['sku_code', 'sku', 'sku_id']:
                    plot_parts.append(f"{key}: {value}")
            
            # Add monthly data summary to plot
            if monthly_demand:
                demand_summary = f"demand_data: {json.dumps(monthly_demand)}"
                plot_parts.append(demand_summary)
            
            if monthly_supply:
                supply_summary = f"supply_data: {json.dumps(monthly_supply)}"
                plot_parts.append(supply_summary)
            
            if monthly_inventory:
                inventory_summary = f"inventory_data: {json.dumps(monthly_inventory)}"
                plot_parts.append(inventory_summary)
            
            plot = " | ".join(plot_parts) if plot_parts else f"FMCG product information for {sku_id}"
            
            # Generate embedding
            print(f"Generating embedding for {sku_id}...")
            text_for_embedding = f"FMCG Product {sku_id} {plot}"
            
            start_time = time.time()
            if embeddings_instance:
                embedding = embeddings_instance.embed_query(text_for_embedding)
                embedding_time = time.time() - start_time
                print(f"✅ Embedding generated for {sku_id} in {embedding_time:.2f}s")
            else:
                embedding = None
                print(f"⚠️ No embedding for {sku_id} (embeddings not available)")
            
            # Store embedding in SKU node
            embedding_query = """
            MATCH (sku:SKU {sku_id: $sku_id})
            SET sku.plotEmbedding = $embedding,
                sku.plot = $plot,
                sku.data_type = 'fmcg_sop'
            """
            
            graph.query(embedding_query, {
                'sku_id': sku_id,
                'embedding': embedding,
                'plot': plot
            })
            
            nodes_created += 1
            print(f"✅ Created enhanced FMCG graph nodes for {sku_id}")
            
        except Exception as e:
            print(f"Error creating enhanced graph nodes for SKU {sku_id}: {e}")
            continue
    
    print(f"\nSuccessfully created {nodes_created} enhanced FMCG graph nodes")
    
    return {
        'total_rows': total_rows_processed,
        'unique_skus': len(sku_data),
        'nodes_created': nodes_created
    }

# Streamlit integration
def upload_enhanced_fmcg_excel():
    """Streamlit function to upload and process enhanced FMCG Excel file"""
    uploaded_file = st.file_uploader("Choose Enhanced FMCG S&OP Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        if st.button("Process Enhanced FMCG Data (100 SKUs)"):
            with st.spinner("Processing Enhanced FMCG S&OP data..."):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    results = extract_enhanced_fmcg_data(tmp_file_path, max_skus=100)
                    
                    if 'error' in results:
                        st.error(f"Processing failed: {results['error']}")
                    else:
                        st.success(f"""
                        ✅ Enhanced FMCG S&OP data processing complete!
                        
                        - **Total rows processed**: {results['total_rows']}
                        - **Unique SKUs found**: {results['unique_skus']}
                        - **SKU nodes created**: {results['nodes_created']}
                        
                        Your enhanced FMCG data has been transformed and is ready for chat!
                        """)
                    
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                finally:
                    import os
                    os.unlink(tmp_file_path)

if __name__ == "__main__":
    # Test with the enhanced Excel file
    results = extract_enhanced_fmcg_data("Enhanced_FMCG_SOP_Dataset.xlsx", max_skus=100)
    print(f"Enhanced extraction results: {results}") 