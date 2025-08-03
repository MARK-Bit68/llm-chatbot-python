#!/usr/bin/env python3
"""
Quick data ingestion for testing - processes only 2 SKUs and generates sample questions
"""

import pandas as pd
import streamlit as st
from langchain_ollama import OllamaEmbeddings
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
        
        graph = Neo4jGraph(
            url=st.secrets["NEO4J_URI"],
            username=st.secrets["NEO4J_USERNAME"], 
            password=st.secrets["NEO4J_PASSWORD"],
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        return None

def generate_sample_questions(sku_data):
    """Generate sample questions based on the ingested SKU data"""
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
            f"What are the logistics details for {sku_id}?"
        ]
        
        questions.extend(sku_questions)
    
    # Add general questions
    general_questions = [
        "What SKUs are in the Master Data?",
        "Show me all SKUs from the Demand Plan",
        "What products are in the Supply Plan?",
        "List all SKUs in the Inventory Plan",
        "What are the financial details for all products?",
        "Show me logistics information for all SKUs",
        "What categories of products do we have?",
        "Which countries are our products from?",
        "What is the price range of our products?",
        "Tell me about our supply chain operations"
    ]
    
    questions.extend(general_questions)
    return questions

def quick_ingestion_2_skus(excel_file_path, max_skus=2):
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
    
    # Create embeddings
    try:
        embeddings = OllamaEmbeddings(
            model="llama3.2-large-context",
            base_url="http://localhost:11434"
        )
    except Exception as e:
        print(f"Error creating embeddings: {e}")
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
    
    # Create movie nodes
    nodes_created = 0
    for sku_id, data in sku_data.items():
        try:
            # Create title from available properties
            title_candidates = []
            for key, value in data['all_properties'].items():
                if any(word in key.lower() for word in ['name', 'title', 'product', 'item', 'description']):
                    title_candidates.append(value)
            
            title = title_candidates[0] if title_candidates else f"FMCG Product {sku_id}"
            
            # Create plot from all properties
            plot_parts = []
            for key, value in data['all_properties'].items():
                if key.lower() not in ['sku_code', 'sku', 'sku_id']:
                    plot_parts.append(f"{key}: {value}")
            
            plot = " | ".join(plot_parts) if plot_parts else f"FMCG product information for {title}"
            
            # Generate embedding (with timeout)
            print(f"Generating embedding for {sku_id}...")
            text_for_embedding = f"{title} {plot}"
            
            # Add timeout for embedding generation
            start_time = time.time()
            embedding = embeddings.embed_query(text_for_embedding)
            embedding_time = time.time() - start_time
            print(f"✅ Embedding generated for {sku_id} in {embedding_time:.2f}s")
            
            # Create movie node
            movie_properties = {
                'title': title,
                'plot': plot,
                'tmdbId': sku_id,
                'plotEmbedding': embedding,
                'sku_id': sku_id,
                'sheet_count': data['sheet_count'],
                'sheets': json.dumps(list(data['sheets'].keys())),
                'data_type': 'fmcg_sop'
            }
            
            # Add all other properties
            for key, value in data['all_properties'].items():
                if key not in ['title', 'plot', 'tmdbId', 'sku_id', 'sheet_count', 'sheets', 'data_type']:
                    movie_properties[key] = value
            
            # Insert into Neo4j
            cypher_query = """
            MERGE (m:Movie {tmdbId: $tmdbId})
            SET m += $properties
            """
            
            graph.query(cypher_query, {
                'tmdbId': sku_id,
                'properties': movie_properties
            })
            
            # Create Category nodes for each sheet
            for sheet_name in data['sheets'].keys():
                category_query = """
                MERGE (c:Category {name: $category_name})
                MERGE (m:Movie {tmdbId: $sku_id})
                MERGE (m)-[:IN_CATEGORY]->(c)
                """
                
                graph.query(category_query, {
                    'category_name': sheet_name,
                    'sku_id': sku_id
                })
            
            nodes_created += 1
            print(f"✅ Created node for {sku_id}")
            
        except Exception as e:
            print(f"Error creating node for SKU {sku_id}: {e}")
            continue
    
    print(f"\nSuccessfully created {nodes_created} movie nodes")
    
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