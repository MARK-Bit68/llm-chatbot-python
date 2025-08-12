#!/usr/bin/env python3
"""Debug script to check data structure and fix queries"""

import os

# Load secrets
with open(".streamlit/secrets.toml", 'r') as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            os.environ[key] = value

from solutions.graph import get_graph

def check_data_structure():
    """Check the actual data structure in Neo4j"""
    print("🔍 Checking data structure...")
    
    try:
        graph = get_graph()
        if graph is None:
            print("❌ No database connection")
            return
        
        # Check sample SKU data
        result = graph.query("MATCH (sku:SKU) RETURN sku.sku_id, sku.plot LIMIT 3")
        print(f"✅ Found {len(result)} sample SKUs")
        
        for row in result:
            sku_id = row['sku.sku_id']
            plot = row['sku.plot']
            print(f"\n📦 {sku_id}:")
            print(f"   Plot: {plot}")
            
            # Parse the plot string to understand structure
            if 'gross_profit:' in plot:
                parts = plot.split(' | ')
                for part in parts:
                    if 'gross_profit:' in part:
                        gross_profit = part.split('gross_profit: ')[1]
                        print(f"   Gross Profit: {gross_profit}")
                        try:
                            gp_value = float(gross_profit)
                            print(f"   As float: {gp_value}")
                            if gp_value < 0:
                                print(f"   ⚠️ NEGATIVE GROSS PROFIT FOUND!")
                        except:
                            print(f"   ❌ Could not parse as float")
        
        # Check for negative gross profit
        print("\n🔍 Checking for negative gross profit...")
        result = graph.query("""
            MATCH (sku:SKU)
            WITH sku, toFloat(split(split(sku.plot, 'gross_profit: ')[1], ' | ')[0]) as gross_profit
            WHERE gross_profit < 0
            RETURN sku.sku_id, gross_profit
            LIMIT 5
        """)
        
        if result:
            print(f"✅ Found {len(result)} SKUs with negative gross profit:")
            for row in result:
                print(f"   {row['sku.sku_id']}: {row['gross_profit']}")
        else:
            print("❌ No SKUs with negative gross profit found")
            
            # Check all gross profit values
            print("\n🔍 Checking all gross profit values...")
            result = graph.query("""
                MATCH (sku:SKU)
                WITH sku, split(split(sku.plot, 'gross_profit: ')[1], ' | ')[0] as gross_profit_str
                WHERE gross_profit_str IS NOT NULL
                RETURN sku.sku_id, gross_profit_str
                LIMIT 10
            """)
            
            for row in result:
                print(f"   {row['sku.sku_id']}: '{row['gross_profit_str']}'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_data_structure()
