#!/usr/bin/env python3
"""
Quick data ingestion for testing - processes only 2 SKUs and generates sample questions
"""

import pandas as pd
import streamlit as st
from langchain_openai import OpenAIEmbeddings
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
            """Get Neo4j config from environment variables only"""
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
        print(f"❌ Neo4j connection failed: {str(e)}")
        return None

def generate_sample_questions(sku_data):
    """Generate comprehensive sample questions based on the ingested SKU data"""
    questions = []
    
    for sku_id, data in sku_data.items():
        # Extract key information for questions
        category = data['all_properties'].get('category', 'Unknown')
        country = data['all_properties'].get('country', 'Unknown')
        unit_price = data['all_properties'].get('unit_price', 'Unknown')
        unit_cost = data['all_properties'].get('unit_cost', 'Unknown')
        
        # Generate specific questions for this SKU
        sku_questions = [
            f"What is the category of {sku_id}?",
            f"What country is {sku_id} from?",
            f"What is the unit price of {sku_id}?",
            f"What is the unit cost of {sku_id}?",
            f"Tell me about {sku_id}",
            f"What are the supply chain details for {sku_id}?",
            f"Show me the demand plan for {sku_id}",
            f"What is the inventory plan for {sku_id}?",
            f"Give me the financial details for {sku_id}",
            f"What are the logistics details for {sku_id}?",
            f"What is the profit margin for {sku_id}?",
            f"Show me all details for {sku_id}"
        ]
        
        questions.extend(sku_questions)
    
    # Add comprehensive general questions
    general_questions = [
        # Basic Information
        "What SKUs are in the Master Data?",
        "Show me all SKUs from the Demand Plan",
        "What products are in the Supply Plan?",
        "List all SKUs in the Inventory Plan",
        "What are the financial details for all products?",
        "Show me logistics information for all SKUs",
        "What categories of products do we have?",
        "Which countries are our products from?",
        "What is the price range of our products?",
        "Tell me about our supply chain operations",
        
        # Financial Analysis
        "Show me products with highest profit margins",
        "Which products have the lowest unit costs?",
        "What is the average profit margin across all products?",
        "Show me products with profit margins above 50%",
        "Which products have the best cost-to-price ratio?",
        "What is the total value of our inventory?",
        "Which products have the highest revenue potential?",
        
        # Supply Chain Analysis
        "Which products have the longest lead times?",
        "What is the average lead time across all products?",
        "Show me products with lead times over 20 days",
        "What is the supply chain plan for SKU002?",
        
        # Category and Market Analysis
        "How many products are in each category?",
        "Which category has the highest average price?",
        "Show me products by country",
        "What is the price distribution by category?",
        
        # Comparative Analysis
        "Show me the top 5 most profitable products",
        "Which products have similar pricing strategies?",
        "What is the price difference between highest and lowest priced products?",
        "Which products have the highest and lowest profit margins?",
        
        # Advanced Analytics
        "Compare SKU001 and SKU003",
        "What are the financial metrics for SKU005?",
        "Show me all details for SKU004",
        "Which products have the highest profit margins?",
        "What is the average unit cost by category?",
        "Show me products with unit prices above $10",
        "Which products have the lowest profit margins?",
        "What is the price range by country?",
        "Show me products with lead times under 15 days",
        "Which category has the most products?"
    ]
    
    questions.extend(general_questions)
    return questions

def quick_ingestion_2_skus(excel_file_path, max_skus=10):
    """
    Quick ingestion of first 2 SKUs for testing
    """
    print(f"🚀 Quick ingestion of first {max_skus} SKUs from {excel_file_path}")
    
    # Read all sheets
    excel_file = pd.ExcelFile(excel_file_path)
    print(f"Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
    
    # Connect to Neo4j
    graph = get_graph_connection()
    if graph is None:
        return {'total_rows': 0, 'unique_skus': 0, 'nodes_created': 0, 'error': 'Neo4j not available'}
    
    # Create embeddings - CRITICAL for RAG system
    try:
        from llm import get_embeddings
        embeddings = get_embeddings()
        if not embeddings:
            print("❌ CRITICAL ERROR: Embeddings not available")
            print("   The RAG system requires embeddings to function properly")
            print("   Please set OPENAI_API_KEY in Railway environment variables")
            return {
                'total_rows': 0,
                'unique_skus': 0,
                'nodes_created': 0,
                'error': 'CRITICAL: OpenAI API key not set. Please configure OPENAI_API_KEY in Railway environment variables.'
            }
    except Exception as e:
        print(f"❌ CRITICAL ERROR creating embeddings: {e}")
        return {
            'total_rows': 0,
            'unique_skus': 0,
            'nodes_created': 0,
            'error': f'CRITICAL: Embeddings error: {e}'
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
            
            # Find SKU column (first column or contains 'sku')
            sku_column = None
            for col in df.columns:
                if 'sku' in str(col).lower():
                    sku_column = col
                    break
            
            if sku_column is None:
                sku_column = df.columns[0]
            
            print(f"  - Found SKU column: {sku_column}")
            
            # Keep original column names for now
            original_columns = df.columns.copy()
            column_mapping = {col: col for col in df.columns}
            
            # Process only first few rows
            for index, row in df.head(max_skus).iterrows():
                # Get the original column name for SKU
                original_sku_col = None
                for orig_col, clean_col in column_mapping.items():
                    if clean_col == sku_column:
                        original_sku_col = orig_col
                        break
                
                if original_sku_col is None:
                    original_sku_col = sku_column
                
                sku_id = str(row[original_sku_col]).strip()
                
                if pd.isna(sku_id) or sku_id == '':
                    continue
                
                # Initialize SKU data if not exists
                if sku_id not in sku_data:
                    sku_data[sku_id] = {
                        'sheets': {},
                        'sheet_count': 0,
                        'all_properties': {}
                    }
                
                # Track sheet
                if sheet_name not in sku_data[sku_id]['sheets']:
                    sku_data[sku_id]['sheets'][sheet_name] = {}
                    sku_data[sku_id]['sheet_count'] += 1
                
                # Store all properties
                for col in df.columns:
                    if col != sku_column:
                        value = row[col]
                        if pd.notna(value):
                            # Clean column name for Neo4j
                            clean_col = clean_column_name(col)
                            
                            # Store in sheet-specific data
                            sku_data[sku_id]['sheets'][sheet_name][clean_col] = value
                            
                            # Store in all properties (with sheet prefix if duplicate)
                            if clean_col not in sku_data[sku_id]['all_properties']:
                                sku_data[sku_id]['all_properties'][clean_col] = value
                            else:
                                existing = sku_data[sku_id]['all_properties'][clean_col]
                                sku_data[sku_id]['all_properties'][clean_col] = f"{existing} | {sheet_name}: {value}"
                
                total_rows_processed += 1
                
        except Exception as e:
            print(f"  - Error processing sheet {sheet_name}: {e}")
            continue
    
    print(f"\nTotal rows processed: {total_rows_processed}")
    print(f"Unique SKUs found: {len(sku_data)}")
    
    # Create FMCG graph schema nodes
    nodes_created = 0
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
            MERGE (sku:SKU {sku_id: $sku_id})
            MERGE (sku)-[:BELONGS_TO_CATEGORY]->(cat)
            """
            graph.query(category_query, {
                'category': category,
                'sku_id': sku_id
            })

            # Create Demand Plan node and relationship
            # Extract monthly demand data
            monthly_demand = {}
            for key, value in data['all_properties'].items():
                if key.startswith('jan_') or key.startswith('feb_') or key.startswith('mar_') or key.startswith('apr_') or key.startswith('may_') or key.startswith('jun_') or key.startswith('jul_') or key.startswith('aug_') or key.startswith('sep_') or key.startswith('oct_') or key.startswith('nov_') or key.startswith('dec_'):
                    # Extract demand part from the combined data
                    if '|' in str(value):
                        demand_value = str(value).split('|')[0].strip()
                        monthly_demand[key] = demand_value
                    else:
                        monthly_demand[key] = value
            
            # Create DemandPlan node with monthly data
            demand_plan_data = json.dumps(monthly_demand) if monthly_demand else "Unknown"
            demand_query = """
            MERGE (dp:DemandPlan {sku_id: $sku_id, monthly_data: $demand_plan})
            MERGE (sku:SKU {sku_id: $sku_id})
            MERGE (sku)-[:HAS_DEMAND_PLAN]->(dp)
            """
            graph.query(demand_query, {
                'demand_plan': demand_plan_data,
                'sku_id': sku_id
            })

            # Create Supply Plan node and relationship
            supply_plan = data['all_properties'].get('supply_plan', 'Unknown')
            supply_query = """
            MERGE (sp:SupplyPlan {value: $supply_plan})
            MERGE (sku:SKU {sku_id: $sku_id})
            MERGE (sku)-[:HAS_SUPPLY_PLAN]->(sp)
            """
            graph.query(supply_query, {
                'supply_plan': supply_plan,
                'sku_id': sku_id
            })

            # Create Inventory node and relationship
            # Extract monthly inventory data
            monthly_inventory = {}
            for key, value in data['all_properties'].items():
                if key.startswith('jan_') or key.startswith('feb_') or key.startswith('mar_') or key.startswith('apr_') or key.startswith('may_') or key.startswith('jun_') or key.startswith('jul_') or key.startswith('aug_') or key.startswith('sep_') or key.startswith('oct_') or key.startswith('nov_') or key.startswith('dec_'):
                    # Extract inventory part from the combined data
                    if 'Inventory Plan:' in str(value):
                        inventory_value = str(value).split('Inventory Plan:')[1].split('|')[0].strip()
                        monthly_inventory[key] = inventory_value
            
            # Create Inventory node with monthly data
            inventory_data = json.dumps(monthly_inventory) if monthly_inventory else "Unknown"
            inventory_query = """
            MERGE (inv:Inventory {sku_id: $sku_id, monthly_data: $inventory})
            MERGE (sku:SKU {sku_id: $sku_id})
            MERGE (sku)-[:HAS_INVENTORY]->(inv)
            """
            graph.query(inventory_query, {
                'inventory': inventory_data,
                'sku_id': sku_id
            })

            # Create text representation for embeddings
            plot_parts = []
            for key, value in data['all_properties'].items():
                if key.lower() not in ['sku_code', 'sku', 'sku_id']:
                    plot_parts.append(f"{key}: {value}")
            
            plot = " | ".join(plot_parts) if plot_parts else f"FMCG product information for {sku_id}"
            
            # Generate embedding
            print(f"Generating embedding for {sku_id}...")
            text_for_embedding = f"FMCG Product {sku_id} {plot}"
            
            start_time = time.time()
            embedding = embeddings.embed_query(text_for_embedding)
            embedding_time = time.time() - start_time
            print(f"✅ Embedding generated for {sku_id} in {embedding_time:.2f}s")
            
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
            print(f"✅ Created FMCG graph nodes for {sku_id}")
            
        except Exception as e:
            print(f"Error creating FMCG graph nodes for SKU {sku_id}: {e}")
            continue
    
    print(f"\nSuccessfully created {nodes_created} FMCG graph nodes")
    
    # Generate sample questions
    sample_questions = generate_sample_questions(sku_data)
    
    return {
        'total_rows': total_rows_processed,
        'unique_skus': len(sku_data),
        'nodes_created': nodes_created,
        'sample_questions': sample_questions,
        'sku_data': sku_data
    }

if __name__ == "__main__":
    # Test with just 2 SKUs
    results = quick_ingestion_2_skus("FMCG S&OP Working Excel.xlsx", max_skus=2)
    print(f"\nQuick ingestion results: {results}")
    
    if 'sample_questions' in results:
        print(f"\n📝 Sample Questions to Test RAG:")
        print("=" * 50)
        for i, question in enumerate(results['sample_questions'][:10], 1):
            print(f"{i}. {question}")
        
        print(f"\n💡 Try these questions in the chatbot at http://localhost:8501")
        print(f"📊 Processed {results['nodes_created']} SKUs with full embeddings") 