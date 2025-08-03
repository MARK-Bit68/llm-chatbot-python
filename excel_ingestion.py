import pandas as pd
import streamlit as st
from llm import get_embeddings
import json
import re

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
            """Get Neo4j config from secrets or environment variables"""
            try:
                return st.secrets[key]
            except:
                return os.getenv(key, default)
        
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        st.error(f"❌ Neo4j connection failed: {str(e)}")
        st.info("💡 Please install and start Neo4j to process Excel data.")
        return None

def create_graph_schema(sku_data, graph):
    """Create proper graph schema instead of flat SKU nodes"""
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

            # Create Demand Plan node and relationship
            demand_plan = data['all_properties'].get('demand_plan', 'Unknown')
            demand_query = """
            MERGE (dp:DemandPlan {value: $demand_plan})
            MERGE (sku)-[:HAS_DEMAND_PLAN]->(dp)
            """
            graph.query(demand_query, {
                'demand_plan': demand_plan,
                'sku_id': sku_id
            })

            # Create Supply Plan node and relationship
            supply_plan = data['all_properties'].get('supply_plan', 'Unknown')
            supply_query = """
            MERGE (sp:SupplyPlan {value: $supply_plan})
            MERGE (sku)-[:HAS_SUPPLY_PLAN]->(sp)
            """
            graph.query(supply_query, {
                'supply_plan': supply_plan,
                'sku_id': sku_id
            })

            # Create Inventory node and relationship
            inventory = data['all_properties'].get('inventory', 'Unknown')
            inventory_query = """
            MERGE (inv:Inventory {value: $inventory})
            MERGE (sku)-[:HAS_INVENTORY]->(inv)
            """
            graph.query(inventory_query, {
                'inventory': inventory,
                'sku_id': sku_id
            })

        except Exception as e:
            print(f"Error creating graph schema for SKU {sku_id}: {e}")
            continue

# Update the extract_fmcg_data function to use the new graph schema

def extract_fmcg_data(excel_file_path):
    """
    Extract FMCG S&OP data and transform into a graph schema
    """
    print(f"Starting FMCG S&OP data extraction from {excel_file_path}")
    
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
    
    # Use embeddings from llm module (already imported)
    try:
        embeddings_instance = get_embeddings()
        if not embeddings_instance:
            print("Warning: Embeddings not available, skipping embedding creation")
            # Continue without embeddings for now
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
            
            # Process each row
            for index, row in df.iterrows():
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
                
                sku_data[sku_id]['sheets'][sheet_name] = row_dict
                sku_data[sku_id]['sheet_count'] += 1
                
                # Merge properties
                for col, value in row_dict.items():
                    if not col.endswith('_original_name'):
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
    
    # Create graph schema
    create_graph_schema(sku_data, graph)
    
    return {
        'total_rows': total_rows_processed,
        'unique_skus': len(sku_data),
        'nodes_created': len(sku_data)
    }

# Streamlit integration
def upload_fmcg_excel():
    """Streamlit function to upload and process FMCG Excel file"""
    uploaded_file = st.file_uploader("Choose FMCG S&OP Excel file", type=['xlsx', 'xls'])
    
    if uploaded_file is not None:
        if st.button("Process FMCG Data"):
            with st.spinner("Processing FMCG S&OP data..."):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                try:
                    results = extract_fmcg_data(tmp_file_path)
                    
                    if 'error' in results:
                        st.error(f"Processing failed: {results['error']}")
                    else:
                        st.success(f"""
                        ✅ FMCG S&OP data processing complete!
                        
                        - **Total rows processed**: {results['total_rows']}
                        - **Unique SKUs found**: {results['unique_skus']}
                        - **SKU nodes created**: {results['nodes_created']}
                        
                        Your FMCG data has been transformed and is ready for chat!
                        """)
                    
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                finally:
                    import os
                    os.unlink(tmp_file_path)

if __name__ == "__main__":
    # Test with the Excel file
    results = extract_fmcg_data("FMCG S&OP Working Excel.xlsx")
    print(f"Extraction results: {results}") 