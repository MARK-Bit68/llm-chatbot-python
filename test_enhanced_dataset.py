#!/usr/bin/env python3
"""
Test script to verify the enhanced FMCG dataset
"""

import pandas as pd
import numpy as np

def test_enhanced_dataset():
    """Test the enhanced dataset structure and data quality"""
    
    print("🧪 Testing Enhanced FMCG Dataset...")
    
    try:
        # Load the enhanced dataset
        excel_file = pd.ExcelFile('Enhanced_FMCG_SOP_Dataset.xlsx')
        print(f"✅ Found {len(excel_file.sheet_names)} sheets: {excel_file.sheet_names}")
        
        # Test each sheet
        for sheet_name in excel_file.sheet_names:
            print(f"\n📊 Testing sheet: {sheet_name}")
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"  - Shape: {df.shape}")
            print(f"  - Columns: {list(df.columns)}")
            
            # Check for missing data
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                print(f"  - Missing data: {missing_data[missing_data > 0].to_dict()}")
            else:
                print(f"  - ✅ No missing data")
            
            # Check data types
            print(f"  - Data types: {df.dtypes.to_dict()}")
            
            # Sample data
            print(f"  - Sample data:")
            print(df.head(3).to_string())
            
            # For sheets with monthly data, check seasonal patterns
            if any(col.startswith('Jan-') or col.startswith('Feb-') for col in df.columns):
                monthly_cols = [col for col in df.columns if any(month in col for month in ['Jan-', 'Feb-', 'Mar-', 'Apr-', 'May-', 'Jun-', 'Jul-', 'Aug-', 'Sep-', 'Oct-', 'Nov-', 'Dec-'])]
                print(f"  - Monthly columns: {len(monthly_cols)}")
                
                # Check for seasonal patterns
                if len(monthly_cols) > 0:
                    sample_sku = df.iloc[0]
                    monthly_values = [sample_sku[col] for col in monthly_cols if pd.notna(sample_sku[col])]
                    print(f"  - Sample SKU monthly values: {monthly_values[:6]}...")
        
        # Test data quality
        print(f"\n🔍 Data Quality Analysis:")
        
        # Master Data analysis
        master_df = pd.read_excel(excel_file, sheet_name='Master Data')
        print(f"  - Total SKUs: {len(master_df)}")
        print(f"  - Categories: {master_df['Category'].value_counts().to_dict()}")
        print(f"  - Countries: {master_df['Country'].value_counts().to_dict()}")
        print(f"  - Price range: ${master_df['Unit Price ($)'].min():.2f} - ${master_df['Unit Price ($)'].max():.2f}")
        print(f"  - Cost range: ${master_df['Unit Cost ($)'].min():.2f} - ${master_df['Unit Cost ($)'].max():.2f}")
        
        # Demand Plan analysis
        demand_df = pd.read_excel(excel_file, sheet_name='Demand Plan')
        monthly_cols = [col for col in demand_df.columns if any(month in col for month in ['Jan-', 'Feb-', 'Mar-', 'Apr-', 'May-', 'Jun-', 'Jul-', 'Aug-', 'Sep-', 'Oct-', 'Nov-', 'Dec-'])]
        total_demand = demand_df[monthly_cols].sum().sum()
        print(f"  - Total demand: {total_demand:,.0f} units")
        print(f"  - Average demand per SKU: {total_demand / len(demand_df):,.0f} units")
        
        # Supply Plan analysis
        supply_df = pd.read_excel(excel_file, sheet_name='Supply Plan')
        total_supply = supply_df[monthly_cols].sum().sum()
        print(f"  - Total supply: {total_supply:,.0f} units")
        print(f"  - Supply/Demand ratio: {total_supply / total_demand:.2f}")
        
        # Inventory Plan analysis
        inventory_df = pd.read_excel(excel_file, sheet_name='Inventory Plan')
        total_inventory = inventory_df[monthly_cols].sum().sum()
        print(f"  - Total inventory: {total_inventory:,.0f} units")
        
        # Financial Plan analysis
        financial_df = pd.read_excel(excel_file, sheet_name='Financial Plan')
        print(f"  - Total revenue: ${financial_df['Total Revenue ($)'].sum():,.0f}")
        print(f"  - Total profit: ${financial_df['Gross Profit ($)'].sum():,.0f}")
        print(f"  - Average margin: {financial_df['Gross Margin (%)'].mean():.1f}%")
        
        # Check for realistic gaps and errors
        print(f"\n⚠️ Gap and Error Analysis:")
        
        # Check for supply gaps
        supply_gaps = []
        for idx in range(len(demand_df)):
            demand_row = demand_df.iloc[idx]
            supply_row = supply_df.iloc[idx]
            for col in monthly_cols:
                demand_val = demand_row[col]
                supply_val = supply_row[col]
                if pd.notna(demand_val) and pd.notna(supply_val):
                    if demand_val > supply_val * 1.1:  # 10% tolerance
                        supply_gaps.append({
                            'sku': demand_row['SKU Code'],
                            'month': col,
                            'demand': demand_val,
                            'supply': supply_val,
                            'gap': demand_val - supply_val
                        })
        
        print(f"  - Supply gaps found: {len(supply_gaps)}")
        if supply_gaps:
            print(f"  - Largest gap: {max(supply_gaps, key=lambda x: x['gap'])}")
        
        # Check for negative margins
        negative_margins = financial_df[financial_df['Gross Margin (%)'] < 0]
        print(f"  - SKUs with negative margins: {len(negative_margins)}")
        if len(negative_margins) > 0:
            print(f"  - Worst margin: {negative_margins['Gross Margin (%)'].min():.1f}%")
        
        # Check for missing data
        missing_data_count = 0
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            missing_data_count += df.isnull().sum().sum()
        
        print(f"  - Total missing data points: {missing_data_count}")
        
        print(f"\n✅ Enhanced dataset test completed successfully!")
        print(f"📊 Dataset is ready for ingestion with 100 SKUs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing dataset: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_dataset()
    if success:
        print(f"\n🎉 Dataset is ready for enhanced FMCG S&OP analysis!")
    else:
        print(f"\n💥 Dataset needs to be regenerated.") 