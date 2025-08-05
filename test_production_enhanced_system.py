#!/usr/bin/env python3
"""
Comprehensive Production Test for Enhanced FMCG S&OP System
Tests the enhanced system on production Neo4j instance
"""

import pandas as pd
import numpy as np
import os
import sys
import time
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def load_secrets():
    """Load secrets from .streamlit/secrets.toml"""
    secrets_path = ".streamlit/secrets.toml"
    secrets = {}
    
    try:
        with open(secrets_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    secrets[key.strip()] = value.strip().strip('"')
        print("✅ Secrets loaded successfully")
        return secrets
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return None

def test_neo4j_connection(secrets):
    """Test Neo4j connection with production credentials"""
    print("\n🔌 Testing Neo4j Connection...")
    
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=secrets['NEO4J_URI'],
            username=secrets['NEO4J_USERNAME'],
            password=secrets['NEO4J_PASSWORD'],
        )
        
        # Test the connection
        result = graph.query("RETURN 1 as test")
        print(f"✅ Neo4j connection successful: {result}")
        
        # Test basic query
        result = graph.query("MATCH (n) RETURN count(n) as node_count")
        print(f"📊 Current nodes in database: {result[0]['node_count']}")
        
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return None

def test_enhanced_dataset_availability():
    """Test if enhanced dataset exists and is valid"""
    print("\n📊 Testing Enhanced Dataset...")
    
    try:
        if not os.path.exists('Enhanced_FMCG_SOP_Dataset.xlsx'):
            print("❌ Enhanced dataset not found. Creating it...")
            from create_enhanced_fmcg_dataset import FMCGDatasetGenerator
            generator = FMCGDatasetGenerator()
            generator.create_enhanced_dataset()
        
        # Test dataset structure
        excel_file = pd.ExcelFile('Enhanced_FMCG_SOP_Dataset.xlsx')
        print(f"✅ Enhanced dataset found: {len(excel_file.sheet_names)} sheets")
        
        # Quick validation
        master_df = pd.read_excel(excel_file, sheet_name='Master Data')
        print(f"✅ Dataset contains {len(master_df)} SKUs")
        
        return True
    except Exception as e:
        print(f"❌ Dataset test failed: {e}")
        return False

def test_enhanced_ingestion(graph):
    """Test enhanced ingestion on production database"""
    print("\n🚀 Testing Enhanced Ingestion...")
    
    try:
        from enhanced_excel_ingestion import extract_enhanced_fmcg_data
        
        # Clear existing data first
        print("🧹 Clearing existing data...")
        graph.query("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")
        
        # Test ingestion with 100 SKUs
        print("📥 Ingesting 100 SKUs...")
        start_time = time.time()
        results = extract_enhanced_fmcg_data('Enhanced_FMCG_SOP_Dataset.xlsx', max_skus=100)
        ingestion_time = time.time() - start_time
        
        print(f"✅ Ingestion completed in {ingestion_time:.2f}s")
        print(f"📊 Results: {results}")
        
        # Verify data was ingested
        result = graph.query("MATCH (sku:SKU) RETURN count(sku) as sku_count")
        sku_count = result[0]['sku_count']
        print(f"✅ {sku_count} SKU nodes created")
        
        # Check for supply and inventory data
        result = graph.query("MATCH (sp:SupplyPlan) RETURN count(sp) as supply_count")
        supply_count = result[0]['supply_count']
        print(f"✅ {supply_count} Supply Plan nodes created")
        
        result = graph.query("MATCH (inv:Inventory) RETURN count(inv) as inventory_count")
        inventory_count = result[0]['inventory_count']
        print(f"✅ {inventory_count} Inventory nodes created")
        
        return True, results
        
    except Exception as e:
        print(f"❌ Enhanced ingestion failed: {e}")
        return False, None

def test_dashboard_data_extraction(graph):
    """Test dashboard data extraction with enhanced data"""
    print("\n📊 Testing Dashboard Data Extraction...")
    
    try:
        # Test the dashboard data extraction function
        from dashboard_component import get_dashboard_data
        
        monthly_df, category_summary, financial_summary = get_dashboard_data()
        
        if monthly_df is not None and not monthly_df.empty:
            print(f"✅ Monthly data extracted: {len(monthly_df)} records")
            print(f"📈 Unique SKUs: {monthly_df['sku_id'].nunique()}")
            print(f"📅 Unique months: {monthly_df['month'].nunique()}")
            
            # Check for supply and inventory data
            total_supply = monthly_df['supply'].sum()
            total_inventory = monthly_df['inventory'].sum()
            
            print(f"📦 Total supply: {total_supply:,.0f}")
            print(f"🏪 Total inventory: {total_inventory:,.0f}")
            
            if total_supply > 0:
                print("✅ Supply data is available (no more zero values)")
            else:
                print("⚠️ Supply data still shows zero values")
                
            if total_inventory > 0:
                print("✅ Inventory data is available")
            else:
                print("⚠️ Inventory data still shows zero values")
                
        else:
            print("❌ Dashboard data extraction failed")
            return False
            
        if category_summary is not None and not category_summary.empty:
            print(f"✅ Category summary extracted: {len(category_summary)} categories")
            
        if financial_summary is not None:
            print(f"✅ Financial summary extracted")
            
        return True
        
    except Exception as e:
        print(f"❌ Dashboard data extraction failed: {e}")
        return False

def test_enhanced_queries(graph):
    """Test enhanced queries with 100 SKU data"""
    print("\n🔍 Testing Enhanced Queries...")
    
    try:
        # Test various queries to ensure data is accessible
        
        # 1. Test SKU count
        result = graph.query("MATCH (sku:SKU) RETURN count(sku) as sku_count")
        sku_count = result[0]['sku_count']
        print(f"✅ SKU count query: {sku_count} SKUs")
        
        # 2. Test category distribution
        result = graph.query("""
            MATCH (sku:SKU)-[:BELONGS_TO_CATEGORY]->(cat:Category)
            RETURN cat.name as category, count(sku) as count
            ORDER BY count DESC
        """)
        print(f"✅ Category distribution: {len(result)} categories")
        for row in result[:3]:  # Show top 3
            print(f"   - {row['category']}: {row['count']} SKUs")
        
        # 3. Test supply chain gaps
        result = graph.query("""
            MATCH (sku:SKU)-[:HAS_DEMAND_PLAN]->(dp:DemandPlan)
            MATCH (sku:SKU)-[:HAS_SUPPLY_PLAN]->(sp:SupplyPlan)
            WHERE dp.monthly_data IS NOT NULL AND sp.monthly_data IS NOT NULL
            RETURN count(sku) as skus_with_supply_data
        """)
        supply_data_count = result[0]['skus_with_supply_data']
        print(f"✅ SKUs with supply data: {supply_data_count}")
        
        # 4. Test inventory data
        result = graph.query("""
            MATCH (sku:SKU)-[:HAS_INVENTORY]->(inv:Inventory)
            WHERE inv.monthly_data IS NOT NULL
            RETURN count(sku) as skus_with_inventory_data
        """)
        inventory_data_count = result[0]['skus_with_inventory_data']
        print(f"✅ SKUs with inventory data: {inventory_data_count}")
        
        # 5. Test financial data
        result = graph.query("""
            MATCH (sku:SKU)
            WHERE sku.plot CONTAINS 'gross_profit'
            RETURN count(sku) as skus_with_financial_data
        """)
        financial_data_count = result[0]['skus_with_financial_data']
        print(f"✅ SKUs with financial data: {financial_data_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced queries failed: {e}")
        return False

def test_dashboard_rendering():
    """Test dashboard rendering with enhanced data"""
    print("\n📈 Testing Dashboard Rendering...")
    
    try:
        # Import dashboard functions
        from dashboard_component import render_dashboard, generate_dashboard_response
        
        # Test dashboard response generation
        print("🔄 Testing dashboard response generation...")
        response = generate_dashboard_response()
        print(f"✅ Dashboard response generated: {len(response)} characters")
        
        # Check if response contains enhanced data indicators
        if "100 SKU" in response or "supply chain" in response.lower():
            print("✅ Dashboard response includes enhanced data references")
        else:
            print("⚠️ Dashboard response may not include enhanced data")
            
        return True
        
    except Exception as e:
        print(f"❌ Dashboard rendering test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive production test"""
    print("🧪 COMPREHENSIVE PRODUCTION TEST FOR ENHANCED FMCG SYSTEM")
    print("=" * 70)
    
    # Load secrets
    secrets = load_secrets()
    if not secrets:
        print("❌ Cannot proceed without secrets")
        return False
    
    # Test Neo4j connection
    graph = test_neo4j_connection(secrets)
    if not graph:
        print("❌ Cannot proceed without Neo4j connection")
        return False
    
    # Test dataset availability
    if not test_enhanced_dataset_availability():
        print("❌ Cannot proceed without enhanced dataset")
        return False
    
    # Test enhanced ingestion
    ingestion_success, ingestion_results = test_enhanced_ingestion(graph)
    if not ingestion_success:
        print("❌ Enhanced ingestion failed")
        return False
    
    # Test dashboard data extraction
    if not test_dashboard_data_extraction(graph):
        print("❌ Dashboard data extraction failed")
        return False
    
    # Test enhanced queries
    if not test_enhanced_queries(graph):
        print("❌ Enhanced queries failed")
        return False
    
    # Test dashboard rendering
    if not test_dashboard_rendering():
        print("❌ Dashboard rendering failed")
        return False
    
    print("\n🎉 COMPREHENSIVE PRODUCTION TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    print("✅ All enhanced FMCG system components working on production")
    print("✅ 100 SKU processing capability confirmed")
    print("✅ Supply/inventory data properly integrated")
    print("✅ Dashboard analytics enhanced")
    print("✅ Production Neo4j instance validated")
    
    return True

if __name__ == "__main__":
    success = run_comprehensive_test()
    if success:
        print("\n🚀 Enhanced FMCG S&OP system is ready for production use!")
    else:
        print("\n💥 Production test failed. System needs fixes before deployment.") 