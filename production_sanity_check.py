#!/usr/bin/env python3
"""
Comprehensive Production Sanity Check
Verifies Neo4j database setup and code alignment before production deployment
"""

import os
import sys
import pandas as pd
import json

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
        return secrets
    except Exception as e:
        print(f"❌ Error loading secrets: {e}")
        return None

def check_neo4j_database_setup():
    """Verify Neo4j database setup and data integrity"""
    print("🔍 NEO4J DATABASE SANITY CHECK")
    print("=" * 50)
    
    # Load secrets
    secrets = load_secrets()
    if not secrets:
        print("❌ Cannot proceed without secrets")
        return False
    
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=secrets['NEO4J_URI'],
            username=secrets['NEO4J_USERNAME'],
            password=secrets['NEO4J_PASSWORD'],
        )
        
        # Test connection
        result = graph.query("RETURN 1 as test")
        print(f"✅ Neo4j connection: {result}")
        
        # Check node counts
        result = graph.query("MATCH (sku:SKU) RETURN count(sku) as sku_count")
        sku_count = result[0]['sku_count']
        print(f"📊 SKU nodes: {sku_count}")
        
        result = graph.query("MATCH (sp:SupplyPlan) RETURN count(sp) as supply_count")
        supply_count = result[0]['supply_count']
        print(f"📦 Supply Plan nodes: {supply_count}")
        
        result = graph.query("MATCH (inv:Inventory) RETURN count(inv) as inventory_count")
        inventory_count = result[0]['inventory_count']
        print(f"🏪 Inventory nodes: {inventory_count}")
        
        result = graph.query("MATCH (cat:Category) RETURN count(cat) as category_count")
        category_count = result[0]['category_count']
        print(f"🏷️ Category nodes: {category_count}")
        
        # Verify we have 100 SKUs as expected
        if sku_count != 100:
            print(f"❌ Expected 100 SKUs, found {sku_count}")
            return False
        else:
            print(f"✅ Correct SKU count: {sku_count}")
        
        # Check data quality for sample SKUs
        result = graph.query("""
            MATCH (sku:SKU)
            OPTIONAL MATCH (sku)-[:HAS_DEMAND_PLAN]->(dp:DemandPlan)
            OPTIONAL MATCH (sku)-[:HAS_SUPPLY_PLAN]->(sp:SupplyPlan)
            OPTIONAL MATCH (sku)-[:HAS_INVENTORY]->(inv:Inventory)
            OPTIONAL MATCH (sku)-[:BELONGS_TO_CATEGORY]->(cat:Category)
            RETURN sku.sku_id as sku_id,
                   sku.name as name,
                   cat.name as category,
                   dp.monthly_data as demand_data,
                   sp.monthly_data as supply_data,
                   inv.monthly_data as inventory_data
            LIMIT 5
        """)
        
        print(f"\n📋 Sample SKU Data Quality Check:")
        for i, row in enumerate(result):
            print(f"\nSKU {i+1}: {row['sku_id']}")
            print(f"  Name: {row['name']}")
            print(f"  Category: {row['category']}")
            
            # Check plot data for monthly information
            plot_data = str(row.get('demand_data', ''))
            if 'jan_2024' in plot_data or 'jan-2024' in plot_data:
                print(f"  ✅ Monthly data present")
            else:
                print(f"  ❌ No monthly data found")
        
        # Check for supply and inventory data in plot
        result = graph.query("""
            MATCH (sku:SKU)
            WHERE sku.plot CONTAINS 'Supply Plan' AND sku.plot CONTAINS 'Inventory Plan'
            RETURN count(sku) as count
        """)
        supply_inventory_count = result[0]['count']
        print(f"\n📦 SKUs with supply/inventory data: {supply_inventory_count}")
        
        if supply_inventory_count == 100:
            print(f"✅ All SKUs have supply/inventory data")
        else:
            print(f"❌ Only {supply_inventory_count}/100 SKUs have supply/inventory data")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_code_alignment():
    """Verify code alignment with expansion goals"""
    print("\n🔍 CODE ALIGNMENT SANITY CHECK")
    print("=" * 50)
    
    # Check key files for 100 SKU references
    files_to_check = [
        ('quick_ingestion_2_skus.py', 'max_skus=100'),
        ('enhanced_excel_ingestion.py', 'max_skus=100'),
        ('dashboard_component.py', '100 SKU'),
        ('bot.py', '100 SKU')
    ]
    
    alignment_issues = []
    
    for filename, expected_content in files_to_check:
        try:
            with open(filename, 'r') as f:
                content = f.read()
                if expected_content in content:
                    print(f"✅ {filename}: Contains {expected_content}")
                else:
                    print(f"❌ {filename}: Missing {expected_content}")
                    alignment_issues.append(filename)
        except FileNotFoundError:
            print(f"❌ {filename}: File not found")
            alignment_issues.append(filename)
    
    # Check for enhanced dataset file
    if os.path.exists('Enhanced_FMCG_SOP_Dataset.xlsx'):
        print(f"✅ Enhanced dataset file exists")
        
        # Verify dataset structure
        try:
            excel_file = pd.ExcelFile('Enhanced_FMCG_SOP_Dataset.xlsx')
            print(f"✅ Dataset has {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
            
            # Check SKU count
            master_df = pd.read_excel(excel_file, sheet_name='Master Data')
            print(f"✅ Dataset contains {len(master_df)} SKUs")
            
            if len(master_df) >= 500:
                print(f"✅ Dataset meets 500 SKU requirement")
            else:
                print(f"❌ Dataset only has {len(master_df)} SKUs, expected 500")
                alignment_issues.append('Enhanced_FMCG_SOP_Dataset.xlsx')
                
        except Exception as e:
            print(f"❌ Error reading dataset: {e}")
            alignment_issues.append('Enhanced_FMCG_SOP_Dataset.xlsx')
    else:
        print(f"❌ Enhanced dataset file not found")
        alignment_issues.append('Enhanced_FMCG_SOP_Dataset.xlsx')
    
    # Check for supply/inventory data in dashboard
    try:
        with open('dashboard_component.py', 'r') as f:
            content = f.read()
            if 'supply_data' in content and 'inventory_data' in content:
                print(f"✅ Dashboard component handles supply/inventory data")
            else:
                print(f"❌ Dashboard component missing supply/inventory handling")
                alignment_issues.append('dashboard_component.py')
    except:
        print(f"❌ Cannot read dashboard component")
        alignment_issues.append('dashboard_component.py')
    
    return len(alignment_issues) == 0, alignment_issues

def check_data_quality():
    """Verify data quality and completeness"""
    print("\n🔍 DATA QUALITY SANITY CHECK")
    print("=" * 50)
    
    try:
        # Load secrets and connect to database
        secrets = load_secrets()
        if not secrets:
            return False
            
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=secrets['NEO4J_URI'],
            username=secrets['NEO4J_USERNAME'],
            password=secrets['NEO4J_PASSWORD'],
        )
        
        # Test dashboard data extraction
        from dashboard_component import get_dashboard_data
        
        monthly_df, category_summary, financial_summary = get_dashboard_data()
        
        if monthly_df is not None and not monthly_df.empty:
            print(f"✅ Dashboard data extraction: {len(monthly_df)} records")
            print(f"📈 Unique SKUs: {monthly_df['sku_id'].nunique()}")
            print(f"📅 Unique months: {monthly_df['month'].nunique()}")
            
            # Check for non-zero supply and inventory
            total_supply = monthly_df['supply'].sum()
            total_inventory = monthly_df['inventory'].sum()
            
            print(f"📦 Total supply: {total_supply:,.0f}")
            print(f"🏪 Total inventory: {total_inventory:,.0f}")
            
            if total_supply > 0 and total_inventory > 0:
                print(f"✅ Supply and inventory data are non-zero")
            else:
                print(f"❌ Supply or inventory data is zero")
                return False
        else:
            print(f"❌ Dashboard data extraction failed")
            return False
            
        if category_summary is not None and not category_summary.empty:
            print(f"✅ Category summary: {len(category_summary)} categories")
        else:
            print(f"❌ Category summary missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Data quality check failed: {e}")
        return False

def run_comprehensive_sanity_check():
    """Run comprehensive sanity check"""
    print("🧪 COMPREHENSIVE PRODUCTION SANITY CHECK")
    print("=" * 70)
    
    checks_passed = 0
    total_checks = 3
    
    # Check 1: Neo4j Database Setup
    print("\n1️⃣ NEO4J DATABASE SETUP CHECK")
    if check_neo4j_database_setup():
        print("✅ Neo4j database setup: PASSED")
        checks_passed += 1
    else:
        print("❌ Neo4j database setup: FAILED")
    
    # Check 2: Code Alignment
    print("\n2️⃣ CODE ALIGNMENT CHECK")
    alignment_ok, issues = check_code_alignment()
    if alignment_ok:
        print("✅ Code alignment: PASSED")
        checks_passed += 1
    else:
        print(f"❌ Code alignment: FAILED")
        print(f"   Issues found: {issues}")
    
    # Check 3: Data Quality
    print("\n3️⃣ DATA QUALITY CHECK")
    if check_data_quality():
        print("✅ Data quality: PASSED")
        checks_passed += 1
    else:
        print("❌ Data quality: FAILED")
    
    # Final assessment
    print(f"\n🎯 SANITY CHECK RESULTS")
    print("=" * 70)
    print(f"Checks passed: {checks_passed}/{total_checks}")
    
    if checks_passed == total_checks:
        print("🎉 ALL CHECKS PASSED - READY FOR PRODUCTION!")
        print("✅ Neo4j database properly configured")
        print("✅ Code aligned with expansion goals")
        print("✅ Data quality verified")
        print("✅ 100 SKU processing confirmed")
        print("✅ Supply/inventory data working")
        return True
    else:
        print("❌ SOME CHECKS FAILED - NEEDS FIXES BEFORE PRODUCTION")
        print("Please address the issues above before deploying")
        return False

if __name__ == "__main__":
    success = run_comprehensive_sanity_check()
    if success:
        print("\n🚀 PRODUCTION DEPLOYMENT APPROVED!")
    else:
        print("\n💥 PRODUCTION DEPLOYMENT BLOCKED - FIXES REQUIRED!") 