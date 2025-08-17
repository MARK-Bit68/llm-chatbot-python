#!/usr/bin/env python3
"""
Quick Data Ingestion for AI_Enhanced_SOP_Dataset_2000SKUs.xlsx
Optimized for speed with batch operations
"""

import pandas as pd
import numpy as np
from neo4j import GraphDatabase
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QuickDataIngester:
    
    def __init__(self):
        """Initialize with Neo4j connection"""
        
        # Read from secrets file
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            with open(secrets_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('NEO4J_URI='):
                        self.neo4j_uri = line.split('=', 1)[1].strip()
                    elif line.startswith('NEO4J_USERNAME='):
                        self.neo4j_username = line.split('=', 1)[1].strip()
                    elif line.startswith('NEO4J_PASSWORD='):
                        self.neo4j_password = line.split('=', 1)[1].strip()
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )
        logger.info("🔗 Connected to Neo4j database")
    
    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("🔌 Neo4j connection closed")
    
    def clear_existing_data(self):
        """Clear existing products and relationships"""
        logger.info("🧹 Clearing existing product data...")
        
        with self.driver.session() as session:
            # Delete product relationships first
            session.run("MATCH (p:Product)-[r]-() DELETE r")
            # Delete products  
            session.run("MATCH (p:Product) DELETE p")
            # Delete other entities if they exist
            session.run("MATCH (n) WHERE NOT n:Product DELETE n")
            
        logger.info("✅ Existing data cleared")
    
    def load_and_validate_data(self, file_path: str):
        """Load Excel data and validate structure"""
        logger.info(f"📁 Loading Excel file: {file_path}")
        
        df = pd.read_excel(file_path, sheet_name='SOP_Dataset')
        logger.info(f"📊 Loaded {len(df)} products with {len(df.columns)} attributes")
        
        # Basic validation
        required_columns = ['SKU Code', 'Product_Name', 'Category', 'Brand', 'Country']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Clean data
        df = df.fillna('')
        
        return df
    
    def create_entities_batch(self, df: pd.DataFrame):
        """Create all entities using batch operations"""
        logger.info("🏗️ Creating entities in batches...")
        
        with self.driver.session() as session:
            
            # 1. Create Categories
            categories = df['Category'].unique()
            logger.info(f"   📊 Creating {len(categories)} categories...")
            for category in categories:
                if category:
                    session.run("MERGE (c:Category {name: $name})", name=str(category))
            
            # 2. Create Brands  
            brands = df['Brand'].unique()
            logger.info(f"   🏷️ Creating {len(brands)} brands...")
            for brand in brands:
                if brand:
                    session.run("MERGE (b:Brand {name: $name})", name=str(brand))
            
            # 3. Create Countries
            countries = df['Country'].unique()
            logger.info(f"   🌍 Creating {len(countries)} countries...")
            for country in countries:
                if country:
                    session.run("MERGE (ct:Country {name: $name})", name=str(country))
            
            # 4. Create Regions
            regions = df['Region'].unique()
            logger.info(f"   🗺️ Creating {len(regions)} regions...")
            for region in regions:
                if region:
                    session.run("MERGE (r:Region {name: $name})", name=str(region))
                    
        logger.info("✅ Core entities created")
    
    def create_products_batch(self, df: pd.DataFrame):
        """Create products in optimized batches"""
        logger.info("🛍️ Creating products...")
        
        batch_size = 50  # Smaller batches for stability
        total_products = len(df)
        
        with self.driver.session() as session:
            
            for i in range(0, total_products, batch_size):
                batch_df = df.iloc[i:i+batch_size]
                logger.info(f"   📦 Processing products {i+1}-{min(i+batch_size, total_products)} of {total_products}")
                
                # Build batch data
                products_data = []
                for _, row in batch_df.iterrows():
                    product_data = {
                        'sku_code': str(row['SKU Code']),
                        'name': str(row['Product_Name']),
                        'uom': str(row.get('UOM', '')),
                        'unit_price': float(row.get('Unit Price ($)', 0)),
                        'unit_cost': float(row.get('Unit Cost ($)', 0)),
                        'gross_margin': float(row.get('Gross_Margin_Pct', 0)),
                        'annual_revenue': float(row.get('Annual_Revenue_USD', 0)),
                        'annual_profit': float(row.get('Annual_Profit_USD', 0)),
                        'lead_time': float(row.get('Lead Time (days)', 0)),
                        'safety_stock': float(row.get('Safety Stock', 0)),
                        'abc_classification': str(row.get('ABC_Classification', '')),
                        'xyz_classification': str(row.get('XYZ_Classification', '')),
                        'overall_risk_rating': str(row.get('Overall_Risk_Rating', '')),
                        'category': str(row['Category']),
                        'brand': str(row['Brand']),
                        'country': str(row['Country']),
                        'region': str(row['Region'])
                    }
                    products_data.append(product_data)
                
                # Execute batch insert
                session.run("""
                    UNWIND $products as product
                    CREATE (p:Product {
                        sku_code: product.sku_code,
                        name: product.name,
                        uom: product.uom,
                        unit_price: product.unit_price,
                        unit_cost: product.unit_cost,
                        gross_margin_pct: product.gross_margin,
                        annual_revenue: product.annual_revenue,
                        annual_profit: product.annual_profit,
                        lead_time_days: product.lead_time,
                        safety_stock: product.safety_stock,
                        abc_classification: product.abc_classification,
                        xyz_classification: product.xyz_classification,
                        overall_risk_rating: product.overall_risk_rating,
                        created_at: datetime()
                    })
                """, products=products_data)
                
        logger.info(f"✅ Created {total_products} products")
    
    def create_relationships_batch(self, df: pd.DataFrame):
        """Create relationships using batch operations"""
        logger.info("🔗 Creating relationships...")
        
        with self.driver.session() as session:
            
            # 1. Product-Category relationships
            logger.info("   📊 Product-Category relationships...")
            session.run("""
                MATCH (p:Product), (c:Category)
                WHERE p.sku_code IN $sku_codes
                  AND c.name IN $categories
                WITH p, c
                WHERE p.sku_code + '|' + c.name IN $product_category_pairs
                MERGE (p)-[:BELONGS_TO]->(c)
            """, 
            sku_codes=df['SKU Code'].astype(str).tolist(),
            categories=df['Category'].astype(str).tolist(),
            product_category_pairs=[f"{row['SKU Code']}|{row['Category']}" for _, row in df.iterrows()]
            )
            
            # 2. Product-Brand relationships
            logger.info("   🏷️ Product-Brand relationships...")
            session.run("""
                MATCH (p:Product), (b:Brand)
                WHERE p.sku_code IN $sku_codes
                  AND b.name IN $brands
                WITH p, b
                WHERE p.sku_code + '|' + b.name IN $product_brand_pairs
                MERGE (p)-[:BRANDED_AS]->(b)
            """,
            sku_codes=df['SKU Code'].astype(str).tolist(),
            brands=df['Brand'].astype(str).tolist(),
            product_brand_pairs=[f"{row['SKU Code']}|{row['Brand']}" for _, row in df.iterrows()]
            )
            
            # 3. Product-Country relationships
            logger.info("   🌍 Product-Country relationships...")
            session.run("""
                MATCH (p:Product), (ct:Country)
                WHERE p.sku_code IN $sku_codes
                  AND ct.name IN $countries
                WITH p, ct
                WHERE p.sku_code + '|' + ct.name IN $product_country_pairs
                MERGE (p)-[:SOLD_IN]->(ct)
            """,
            sku_codes=df['SKU Code'].astype(str).tolist(),
            countries=df['Country'].astype(str).tolist(),
            product_country_pairs=[f"{row['SKU Code']}|{row['Country']}" for _, row in df.iterrows()]
            )
            
            # 4. Country-Region relationships
            logger.info("   🗺️ Country-Region relationships...")
            country_region_pairs = df[['Country', 'Region']].drop_duplicates()
            session.run("""
                UNWIND $pairs as pair
                MATCH (ct:Country {name: pair.country}), (r:Region {name: pair.region})
                MERGE (ct)-[:PART_OF]->(r)
            """, pairs=[{'country': str(row['Country']), 'region': str(row['Region'])} 
                       for _, row in country_region_pairs.iterrows()])
        
        logger.info("✅ Basic relationships created")
    
    def validate_results(self):
        """Validate ingestion results"""
        logger.info("🔍 Validating results...")
        
        with self.driver.session() as session:
            
            # Count entities
            product_count = session.run("MATCH (p:Product) RETURN count(p) as count").single()['count']
            category_count = session.run("MATCH (c:Category) RETURN count(c) as count").single()['count']
            country_count = session.run("MATCH (ct:Country) RETURN count(ct) as count").single()['count']
            relationship_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            logger.info(f"📊 Validation Results:")
            logger.info(f"   🛍️ Products: {product_count}")
            logger.info(f"   📊 Categories: {category_count}")
            logger.info(f"   🌍 Countries: {country_count}")
            logger.info(f"   🔗 Relationships: {relationship_count}")
            
            # Sample query
            sample_result = session.run("""
                MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                RETURN c.name as category, count(p) as products
                ORDER BY products DESC LIMIT 3
            """)
            
            logger.info("📈 Top Categories:")
            for record in sample_result:
                logger.info(f"   {record['category']}: {record['products']} products")
            
            return {
                'products': product_count,
                'categories': category_count,
                'countries': country_count,
                'relationships': relationship_count
            }

def main():
    """Main ingestion process"""
    
    logger.info("🚀 Starting Quick AI Enhanced Dataset Ingestion...")
    
    file_path = "AI_Enhanced_SOP_Dataset_2000SKUs.xlsx"
    
    if not Path(file_path).exists():
        logger.error(f"❌ File not found: {file_path}")
        return
    
    ingester = QuickDataIngester()
    
    try:
        # Clear existing data
        ingester.clear_existing_data()
        
        # Load and validate data
        df = ingester.load_and_validate_data(file_path)
        
        # Create entities
        ingester.create_entities_batch(df)
        
        # Create products
        ingester.create_products_batch(df)
        
        # Create relationships
        ingester.create_relationships_batch(df)
        
        # Validate results
        results = ingester.validate_results()
        
        logger.info("🎉 Quick ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise
    
    finally:
        ingester.close()

if __name__ == "__main__":
    main()