#!/usr/bin/env python3
"""
Standardized Ingestion Script using Unified Data Model

This script provides a standardized way to ingest FMCG data using the unified data model,
ensuring dashboard compatibility and schema consistency.

USAGE:
    # Ingest new data from Excel file
    python standardized_ingestion.py --file your_data.xlsx
    
    # Validate current database schema
    python standardized_ingestion.py --validate
    
    # Migrate existing SKU nodes to Product nodes
    python standardized_ingestion.py --migrate
    
    # Show help
    python standardized_ingestion.py --help

EXAMPLES:
    # Ingest the 2000 SKU dataset
    python standardized_ingestion.py --file AI_Enhanced_SOP_Dataset_2000SKUs.xlsx
    
    # Check if database is ready for dashboard
    python standardized_ingestion.py --validate
    
    # Migrate any old SKU data to new format
    python standardized_ingestion.py --migrate

FEATURES:
- Automatic column mapping and data type detection
- Excel file processing with auto-sheet detection
- Schema validation after ingestion
- Dashboard compatibility guarantee
- Backward compatibility with existing data

REQUIREMENTS:
- Neo4j database connection (configured in .streamlit/secrets.toml)
- Excel file with product data
- Python 3.7+
- pandas, langchain_neo4j packages

TROUBLESHOOTING:
- If connection fails, check .streamlit/secrets.toml credentials
- If validation fails, run migration to fix schema issues
- If ingestion fails, check Excel file format and column names
"""

import os
import sys
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the current directory to the path to import the unified model
sys.path.append('.')
from unified_data_model import UnifiedDataModel, ProductSchema, get_unified_model, validate_dashboard_compatibility

logger = logging.getLogger(__name__)

class StandardizedIngester:
    """
    Standardized ingester that uses the unified data model to ensure
    dashboard compatibility and schema consistency.
    """
    
    def __init__(self):
        self.model = get_unified_model()
        if not self.model:
            raise Exception("Cannot connect to Neo4j database")
        
        # Create indexes for optimal performance
        self.model.create_indexes()
    
    def ingest_excel_file(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingest data from an Excel file using the standardized schema.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Optional sheet name (if None, will auto-detect)
        
        Returns:
            Dictionary with ingestion statistics
        """
        try:
            logger.info(f"Starting standardized ingestion of {file_path}")
            
            # Read Excel file
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                # Try to auto-detect the main data sheet
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names
                
                # Look for sheets that might contain product data
                data_sheets = [name for name in sheet_names if any(keyword in name.lower() 
                                for keyword in ['product', 'sku', 'master', 'data', 'main'])]
                
                if data_sheets:
                    sheet_name = data_sheets[0]
                    logger.info(f"Auto-detected sheet: {sheet_name}")
                else:
                    sheet_name = sheet_names[0]
                    logger.info(f"Using first sheet: {sheet_name}")
                
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Analyze the data structure
            analysis = self._analyze_dataframe(df)
            logger.info(f"Data analysis: {analysis}")
            
            # Ingest the data
            stats = self._ingest_dataframe(df, analysis)
            
            # Validate the result
            validation = self.model.validate_schema()
            if not validation.is_valid:
                logger.warning(f"Schema validation failed: {validation.errors}")
            
            return {
                'file_path': file_path,
                'sheet_name': sheet_name,
                'rows_processed': len(df),
                'products_created': stats['products_created'],
                'relationships_created': stats['relationships_created'],
                'schema_valid': validation.is_valid,
                'validation_errors': validation.errors,
                'validation_warnings': validation.warnings
            }
            
        except Exception as e:
            logger.error(f"Error ingesting {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'success': False
            }
    
    def _analyze_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the structure of the dataframe to determine column mappings"""
        analysis = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'column_mappings': {},
            'data_types': {},
            'missing_values': {}
        }
        
        # Standard column mappings
        column_mappings = {
            'sku_code': ['sku_code', 'sku', 'code', 'product_code', 'id', 'sku code'],
            'name': ['name', 'product_name', 'description', 'title', 'product name'],
            'category': ['category', 'product_category', 'cat', 'group'],
            'unit_price': ['unit_price', 'price', 'unit price', 'unit_price_$', 'price_$'],
            'unit_cost': ['unit_cost', 'cost', 'unit cost', 'unit_cost_$', 'cost_$'],
            'annual_revenue': ['annual_revenue', 'revenue', 'total_revenue', 'annual_revenue_$'],
            'annual_profit': ['annual_profit', 'profit', 'total_profit', 'annual_profit_$'],
            'gross_margin_pct': ['gross_margin_pct', 'gross_margin', 'margin', 'gross_margin_%'],
            'uom': ['uom', 'unit_of_measure', 'unit', 'measure'],
            'lead_time_days': ['lead_time_days', 'lead_time', 'leadtime', 'lead time'],
            'safety_stock': ['safety_stock', 'safety_stock_level', 'min_stock'],
            'country': ['country', 'location', 'region'],
            'brand': ['brand', 'brand_name', 'manufacturer']
        }
        
        # Find column mappings
        for standard_name, possible_names in column_mappings.items():
            for col in df.columns:
                if any(name.lower() in col.lower() for name in possible_names):
                    analysis['column_mappings'][standard_name] = col
                    break
        
        # Analyze data types
        for col in df.columns:
            analysis['data_types'][col] = str(df[col].dtype)
            analysis['missing_values'][col] = df[col].isnull().sum()
        
        return analysis
    
    def _ingest_dataframe(self, df: pd.DataFrame, analysis: Dict[str, Any]) -> Dict[str, int]:
        """Ingest the dataframe using the unified model"""
        stats = {
            'products_created': 0,
            'relationships_created': 0
        }
        
        column_mappings = analysis['column_mappings']
        
        for idx, row in df.iterrows():
            try:
                # Create ProductSchema from row
                product = ProductSchema(
                    sku_code=str(row.get(column_mappings.get('sku_code', 'sku_code'), f"PROD_{idx}")),
                    name=str(row.get(column_mappings.get('name', 'name'), f"Product {idx}")),
                    category=row.get(column_mappings.get('category', 'category')),
                    unit_price=self._safe_float(row.get(column_mappings.get('unit_price', 'unit_price'))),
                    unit_cost=self._safe_float(row.get(column_mappings.get('unit_cost', 'unit_cost'))),
                    annual_revenue=self._safe_float(row.get(column_mappings.get('annual_revenue', 'annual_revenue'))),
                    annual_profit=self._safe_float(row.get(column_mappings.get('annual_profit', 'annual_profit'))),
                    gross_margin_pct=self._safe_float(row.get(column_mappings.get('gross_margin_pct', 'gross_margin_pct'))),
                    uom=row.get(column_mappings.get('uom', 'uom')),
                    lead_time_days=self._safe_int(row.get(column_mappings.get('lead_time_days', 'lead_time_days'))),
                    safety_stock=self._safe_float(row.get(column_mappings.get('safety_stock', 'safety_stock'))),
                    country=row.get(column_mappings.get('country', 'country')),
                    brand=row.get(column_mappings.get('brand', 'brand')),
                    data_source='standardized_ingestion'
                )
                
                # Create the product node
                if self.model.create_product_node(product):
                    stats['products_created'] += 1
                
            except Exception as e:
                logger.warning(f"Error processing row {idx}: {e}")
                continue
        
        return stats
    
    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if pd.isna(value) or value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if pd.isna(value) or value is None:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None
    
    def migrate_existing_data(self) -> Dict[str, Any]:
        """Migrate existing SKU nodes to Product nodes for backward compatibility"""
        logger.info("Starting migration of existing SKU nodes to Product nodes")
        
        migration_stats = self.model.migrate_sku_to_product()
        
        # Validate after migration
        validation = self.model.validate_schema()
        
        return {
            'migration_stats': migration_stats,
            'schema_valid': validation.is_valid,
            'validation_errors': validation.errors,
            'validation_warnings': validation.warnings
        }
    
    def validate_current_schema(self) -> Dict[str, Any]:
        """Validate the current database schema"""
        validation = self.model.validate_schema()
        
        return {
            'is_valid': validation.is_valid,
            'node_count': validation.node_count,
            'relationship_count': validation.relationship_count,
            'errors': validation.errors,
            'warnings': validation.warnings
        }

def main():
    """
    Main function for command-line usage.
    
    This script provides a standardized way to ingest FMCG data and ensure
    dashboard compatibility. It automatically handles column mapping, data
    validation, and schema consistency.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Standardized FMCG Data Ingestion - Ensures dashboard compatibility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Ingest new data
  python standardized_ingestion.py --file AI_Enhanced_SOP_Dataset_2000SKUs.xlsx
  
  # Validate current database
  python standardized_ingestion.py --validate
  
  # Migrate old SKU data
  python standardized_ingestion.py --migrate
  
  # Ingest with specific sheet
  python standardized_ingestion.py --file data.xlsx --sheet "Products"
        """
    )
    parser.add_argument('--file', '-f', help='Excel file to ingest (required for ingestion)')
    parser.add_argument('--sheet', '-s', help='Sheet name (auto-detected if not specified)')
    parser.add_argument('--migrate', '-m', action='store_true', help='Migrate existing SKU nodes to Product nodes')
    parser.add_argument('--validate', '-v', action='store_true', help='Validate current database schema')
    
    args = parser.parse_args()
    
    print("🚀 Standardized FMCG Data Ingestion")
    print("=" * 50)
    
    try:
        ingester = StandardizedIngester()
        
        if args.validate:
            print("🔍 Validating current database schema...")
            result = ingester.validate_current_schema()
            print(f"Schema validation: {'✅ Valid' if result['is_valid'] else '❌ Invalid'}")
            print(f"Products: {result['node_count']}")
            print(f"Relationships: {result['relationship_count']}")
            
            if result['errors']:
                print(f"\n❌ Errors found:")
                for error in result['errors']:
                    print(f"  - {error}")
            
            if result['warnings']:
                print(f"\n⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
            
            if result['is_valid'] and result['node_count'] > 0:
                print(f"\n✅ Database is ready for dashboard use!")
            else:
                print(f"\n❌ Database needs attention before dashboard can work properly.")
        
        elif args.migrate:
            print("🔄 Migrating existing SKU nodes to Product nodes...")
            result = ingester.migrate_existing_data()
            print(f"Migration completed: {result['migration_stats']}")
            print(f"Schema valid: {result['schema_valid']}")
            
            if result['validation_errors']:
                print(f"Validation errors: {result['validation_errors']}")
        
        elif args.file:
            print(f"📥 Ingesting data from: {args.file}")
            if args.sheet:
                print(f"📋 Using sheet: {args.sheet}")
            else:
                print("🔍 Auto-detecting sheet...")
            
            result = ingester.ingest_excel_file(args.file, args.sheet)
            
            if 'error' in result:
                print(f"❌ Ingestion failed: {result['error']}")
                print("\nTROUBLESHOOTING:")
                print("1. Check that the Excel file exists and is readable")
                print("2. Verify the file contains product data")
                print("3. Check column names match expected format")
                print("4. Ensure database connection is working")
            else:
                print(f"✅ Ingestion completed successfully!")
                print(f"  📊 Rows processed: {result['rows_processed']}")
                print(f"  📦 Products created: {result['products_created']}")
                print(f"  🔗 Relationships created: {result.get('relationships_created', 0)}")
                print(f"  ✅ Schema valid: {result['schema_valid']}")
                
                if result['validation_errors']:
                    print(f"  ⚠️  Validation errors: {result['validation_errors']}")
                if result['validation_warnings']:
                    print(f"  ⚠️  Validation warnings: {result['validation_warnings']}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        print("\nTROUBLESHOOTING:")
        print("1. Check that .streamlit/secrets.toml exists with correct credentials")
        print("2. Verify Neo4j database is running and accessible")
        print("3. Ensure all required packages are installed")
        print("4. Check the file path and permissions")

if __name__ == "__main__":
    main()
