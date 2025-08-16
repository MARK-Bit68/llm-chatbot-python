#!/usr/bin/env python3
"""
Test script to create a sample Excel file and test the upload functionality
"""

import pandas as pd
import requests
import os

def create_test_excel():
    """Create a simple test Excel file"""
    
    # Sample data for products
    products_data = {
        'Product_ID': ['P001', 'P002', 'P003', 'P004', 'P005'],
        'Product_Name': ['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Tool Z'],
        'Category': ['Electronics', 'Electronics', 'Tools', 'Tools', 'Hardware'],
        'Price': [10.99, 15.99, 25.50, 30.00, 12.75],
        'Stock': [100, 50, 75, 25, 200]
    }
    
    # Sample data for relationships
    relationships_data = {
        'Source_Product': ['P001', 'P002', 'P003', 'P004'],
        'Target_Product': ['P002', 'P003', 'P004', 'P005'],
        'Relationship_Type': ['COMPATIBLE_WITH', 'REPLACES', 'REQUIRES', 'BUNDLED_WITH'],
        'Strength': [0.8, 0.9, 0.7, 0.6]
    }
    
    # Sample temporal data
    temporal_data = {
        'Date': ['2024-01', '2024-02', '2024-03', '2024-04', '2024-05'],
        'P001_Sales': [100, 120, 110, 130, 140],
        'P002_Sales': [80, 90, 95, 100, 105],
        'P003_Sales': [60, 70, 75, 85, 90],
        'P004_Sales': [40, 45, 50, 55, 60],
        'P005_Sales': [200, 220, 210, 240, 250]
    }
    
    # Create Excel file with multiple sheets
    filename = 'test_sample_data.xlsx'
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        pd.DataFrame(products_data).to_excel(writer, sheet_name='Products', index=False)
        pd.DataFrame(relationships_data).to_excel(writer, sheet_name='Product_Relationships', index=False)
        pd.DataFrame(temporal_data).to_excel(writer, sheet_name='Monthly_Sales', index=False)
    
    print(f"✅ Created test Excel file: {filename}")
    return filename

def test_local_import():
    """Test the import function locally"""
    
    filename = create_test_excel()
    
    try:
        # Import locally
        from enhanced_graph_import import import_enhanced_fmcg_graph
        
        print("🧪 Testing local import...")
        result = import_enhanced_fmcg_graph(filename)
        
        print("📊 Import Results:")
        print(f"  - Nodes Created: {result.get('nodes_created', {})}")
        print(f"  - Relationships Created: {result.get('relationships_created', {})}")
        print(f"  - Connectivity: {result.get('connectivity', {})}")
        print(f"  - Sheets Processed: {result.get('sheets_processed', 0)}")
        print(f"  - Errors: {result.get('errors', [])}")
        
        if result.get('excel_analysis'):
            print("🔍 Excel Analysis:")
            analysis = result['excel_analysis']
            print(f"  - Total Sheets: {analysis.get('total_sheets', 0)}")
            print(f"  - Sheet Names: {analysis.get('sheet_names', [])}")
            print(f"  - Suggested Mapping: {analysis.get('suggested_mapping', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ Local test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

def test_api_upload():
    """Test the API upload endpoint"""
    
    filename = create_test_excel()
    
    try:
        # Test API upload
        print("🌐 Testing API upload...")
        
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            # Test locally first
            response = requests.post('http://localhost:8000/api/upload/excel', files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ API upload successful!")
                print(f"📊 Results: {result}")
                return True
            else:
                print(f"❌ API upload failed: {response.status_code}")
                print(f"Error: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False
    finally:
        # Clean up
        if os.path.exists(filename):
            os.remove(filename)

if __name__ == "__main__":
    print("🧪 Starting Excel Upload Tests")
    
    # Test local import first
    local_success = test_local_import()
    
    if local_success:
        print("\n" + "="*50)
        # Test API upload
        # api_success = test_api_upload()
        print("✅ Local test completed successfully!")
    else:
        print("❌ Local test failed - skipping API test")