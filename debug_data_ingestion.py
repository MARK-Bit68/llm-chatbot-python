#!/usr/bin/env python3
"""
Debug Data Ingestion
Check what's happening with the data ingestion process
"""

import pandas as pd
import numpy as np
import json
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

def debug_excel_data():
    """Debug the Excel data to see what's actually there"""
    
    print("🔍 Debugging Excel Data...")
    
    # Read the Excel file
    excel_data = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name=None)
    
    print(f"📊 Found {len(excel_data)} sheets")
    
    for sheet_name, df in excel_data.items():
        print(f"\n📋 Sheet: {sheet_name}")
        print(f"  - Shape: {df.shape}")
        print(f"  - Columns: {df.columns.tolist()}")
        
        if len(df) > 0:
            print(f"  - First row data:")
            first_row = df.iloc[0]
            for col in df.columns:
                print(f"    {col}: {first_row[col]} (type: {type(first_row[col])})")

def debug_sku_processing():
    """Debug SKU processing specifically"""
    
    print("\n🔍 Debugging SKU Processing...")
    
    # Read Master Data
    master_df = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name='Master Data')
    
    print(f"📊 Master Data shape: {master_df.shape}")
    print(f"📋 Columns: {master_df.columns.tolist()}")
    
    # Check first few rows
    for idx in range(min(3, len(master_df))):
        row = master_df.iloc[idx]
        print(f"\n📦 SKU {idx + 1}:")
        print(f"  SKU Code: '{row.get('SKU Code', 'MISSING')}'")
        print(f"  Category: '{row.get('Category', 'MISSING')}'")
        print(f"  Region: '{row.get('Region', 'MISSING')}'")
        print(f"  Manufacturing Plant: '{row.get('Manufacturing Plant', 'MISSING')}'")
        print(f"  Manufacturing Capacity: {row.get('Manufacturing Capacity', 'MISSING')}")
        print(f"  Capacity Utilization: {row.get('Capacity Utilization', 'MISSING')}")
        print(f"  Lead Time: {row.get('Lead Time (days)', 'MISSING')}")
        print(f"  Safety Stock: {row.get('Safety Stock', 'MISSING')}")
        print(f"  Reorder Point: {row.get('Reorder Point', 'MISSING')}")

def debug_customer_processing():
    """Debug customer processing specifically"""
    
    print("\n🔍 Debugging Customer Processing...")
    
    # Read Customer Data
    customer_df = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name='Customer Data')
    
    print(f"📊 Customer Data shape: {customer_df.shape}")
    print(f"📋 Columns: {customer_df.columns.tolist()}")
    
    # Check first few rows
    for idx in range(min(3, len(customer_df))):
        row = customer_df.iloc[idx]
        print(f"\n👥 Customer {idx + 1}:")
        print(f"  Customer ID: '{row.get('customer_id', 'MISSING')}'")
        print(f"  Name: '{row.get('name', 'MISSING')}'")
        print(f"  Priority Level: '{row.get('priority_level', 'MISSING')}'")
        print(f"  Service Level: {row.get('service_level', 'MISSING')}")
        print(f"  Priority Score: {row.get('priority_score', 'MISSING')}")
        print(f"  Relationship Impact: '{row.get('relationship_impact', 'MISSING')}'")
        print(f"  Region: '{row.get('region', 'MISSING')}'")
        print(f"  Total Revenue: {row.get('total_revenue', 'MISSING')}")

def debug_manufacturing_processing():
    """Debug manufacturing processing specifically"""
    
    print("\n🔍 Debugging Manufacturing Processing...")
    
    # Read Manufacturing Data
    manufacturing_df = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name='Manufacturing Capacity')
    
    print(f"📊 Manufacturing Data shape: {manufacturing_df.shape}")
    print(f"📋 Columns: {manufacturing_df.columns.tolist()}")
    
    # Check first few rows
    for idx in range(min(3, len(manufacturing_df))):
        row = manufacturing_df.iloc[idx]
        print(f"\n🏭 Manufacturing {idx + 1}:")
        print(f"  Plant: '{row.get('Plant', 'MISSING')}'")
        print(f"  Category: '{row.get('Category', 'MISSING')}'")
        print(f"  Location: '{row.get('Location', 'MISSING')}'")
        print(f"  Total Capacity: {row.get('Total Capacity', 'MISSING')}")
        print(f"  Category Capacity: {row.get('Category Capacity', 'MISSING')}")
        print(f"  Utilization Rate: {row.get('Utilization Rate', 'MISSING')}")
        print(f"  Available Capacity: {row.get('Available Capacity', 'MISSING')}")

def debug_promotional_processing():
    """Debug promotional processing specifically"""
    
    print("\n🔍 Debugging Promotional Processing...")
    
    # Read Promotional Data
    promotional_df = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name='Promotional Campaigns')
    
    print(f"📊 Promotional Data shape: {promotional_df.shape}")
    print(f"📋 Columns: {promotional_df.columns.tolist()}")
    
    # Check first few rows
    for idx in range(min(3, len(promotional_df))):
        row = promotional_df.iloc[idx]
        print(f"\n📢 Promotional {idx + 1}:")
        print(f"  Campaign Name: '{row.get('Campaign Name', 'MISSING')}'")
        print(f"  Start Date: '{row.get('Start Date', 'MISSING')}'")
        print(f"  End Date: '{row.get('End Date', 'MISSING')}'")
        print(f"  Categories: '{row.get('Categories', 'MISSING')}'")
        print(f"  Demand Uplift: {row.get('Demand Uplift', 'MISSING')}")
        print(f"  Budget: {row.get('Budget', 'MISSING')}")
        print(f"  Regions: '{row.get('Regions', 'MISSING')}'")
        print(f"  Status: '{row.get('Status', 'MISSING')}'")

def debug_regional_processing():
    """Debug regional processing specifically"""
    
    print("\n🔍 Debugging Regional Processing...")
    
    # Read Regional Data
    regional_df = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name='Regional Data')
    
    print(f"📊 Regional Data shape: {regional_df.shape}")
    print(f"📋 Columns: {regional_df.columns.tolist()}")
    
    # Check first few rows
    for idx in range(min(3, len(regional_df))):
        row = regional_df.iloc[idx]
        print(f"\n🌍 Region {idx + 1}:")
        print(f"  Region: '{row.get('Region', 'MISSING')}'")
        print(f"  Countries: '{row.get('Countries', 'MISSING')}'")
        print(f"  Demand Multiplier: {row.get('Demand Multiplier', 'MISSING')}")
        print(f"  Service Level: {row.get('Service Level', 'MISSING')}")
        print(f"  Market Size: {row.get('Market Size', 'MISSING')}")
        print(f"  Growth Rate: {row.get('Growth Rate', 'MISSING')}")
        print(f"  Competition Level: '{row.get('Competition Level', 'MISSING')}'")
        print(f"  Distribution Channels: {row.get('Distribution Channels', 'MISSING')}")

def main():
    """Main debug function"""
    
    try:
        debug_excel_data()
        debug_sku_processing()
        debug_customer_processing()
        debug_manufacturing_processing()
        debug_promotional_processing()
        debug_regional_processing()
        
        print("\n🎉 Debug completed!")
        
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        raise

if __name__ == "__main__":
    main() 