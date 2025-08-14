#!/usr/bin/env python3
"""
Enhanced FMCG SOP Dataset - Memgraph Graph Database Loader and Visualizer

This standalone application loads the Enhanced FMCG SOP dataset into Memgraph
and provides visualization capabilities through Memgraph Lab.

Requirements:
- Memgraph running locally (docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph-platform)
- Python packages: pandas, openpyxl, gqlalchemy
"""

import os
import sys
import pandas as pd
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import webbrowser
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from gqlalchemy import Memgraph
    from gqlalchemy.query_builders.memgraph_query_builder import (
        Create, Match, Where, Return, With, Unwind, Optional, Merge
    )
except ImportError:
    print("❌ gqlalchemy not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "gqlalchemy"])
    from gqlalchemy import Memgraph
    from gqlalchemy.query_builders.memgraph_query_builder import (
        Create, Match, Where, Return, With, Unwind, Optional, Merge
    )

class FMCGGraphLoader:
    """Loads Enhanced FMCG SOP dataset into Memgraph graph database"""
    
    def __init__(self, excel_file: str = "Enhanced_FMCG_SOP_Dataset.xlsx"):
        self.excel_file = excel_file
        self.memgraph = None
        self.data_cache = {}
        
    def connect_to_memgraph(self) -> bool:
        """Connect to Memgraph database"""
        try:
            self.memgraph = Memgraph("localhost", 7687)
            # Test connection
            result = self.memgraph.execute("RETURN 1 AS test")
            print("✅ Connected to Memgraph successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Memgraph: {e}")
            print("💡 Make sure Memgraph is running with:")
            print("   docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph-platform")
            return False
    
    def clear_database(self):
        """Clear all existing data from the database"""
        print("🗑️  Clearing existing database...")
        try:
            self.memgraph.execute("MATCH (n) DETACH DELETE n")
            print("✅ Database cleared")
        except Exception as e:
            print(f"⚠️  Warning during database clear: {e}")
    
    def load_excel_data(self):
        """Load data from Excel file into memory"""
        print(f"📊 Loading data from {self.excel_file}...")
        
        try:
            excel_file = pd.ExcelFile(self.excel_file)
            print(f"   Found {len(excel_file.sheet_names)} sheets")
            
            for sheet_name in excel_file.sheet_names:
                print(f"   Loading sheet: {sheet_name}")
                self.data_cache[sheet_name] = pd.read_excel(self.excel_file, sheet_name=sheet_name)
            
            print("✅ Excel data loaded successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load Excel file: {e}")
            return False
    
    def create_schema(self):
        """Create database schema with constraints and indexes"""
        print("🏗️  Creating database schema...")
        
        # Create constraints for unique identifiers
        constraints = [
            "CREATE CONSTRAINT product_code IF NOT EXISTS FOR (p:Product) REQUIRE p.code IS UNIQUE",
            "CREATE CONSTRAINT category_name IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT country_name IF NOT EXISTS FOR (co:Country) REQUIRE co.name IS UNIQUE",
            "CREATE CONSTRAINT plant_id IF NOT EXISTS FOR (pl:Plant) REQUIRE pl.id IS UNIQUE",
            "CREATE CONSTRAINT storage_id IF NOT EXISTS FOR (sl:StorageLocation) REQUIRE sl.id IS UNIQUE",
            "CREATE CONSTRAINT date_value IF NOT EXISTS FOR (d:Date) REQUIRE d.value IS UNIQUE"
        ]
        
        for constraint in constraints:
            try:
                self.memgraph.execute(constraint)
                print(f"  ✅ Created constraint: {constraint.split('FOR')[0].strip()}")
            except Exception as e:
                print(f"  ⚠️  Constraint creation warning: {e}")
    
    def load_master_data(self):
        """Load master data (products, categories, countries)"""
        print("📦 Loading master data...")
        
        if "Master Data" not in self.data_cache:
            print("❌ Master Data sheet not found")
            return
        
        df = self.data_cache["Master Data"]
        
        # Create categories
        categories = df['Category'].unique()
        for category in categories:
            self.memgraph.execute(
                "CREATE (c:Category {name: $name})",
                {"name": category}
            )
        
        # Create countries
        countries = df['Country'].unique()
        for country in countries:
            self.memgraph.execute(
                "CREATE (co:Country {name: $name})",
                {"name": country}
            )
        
        # Create products and relationships
        for _, row in df.iterrows():
            # Create product
            self.memgraph.execute("""
                CREATE (p:Product {
                    code: $code,
                    uom: $uom,
                    unit_price: $unit_price,
                    unit_cost: $unit_cost,
                    lead_time: $lead_time
                })
            """, {
                "code": row['SKU Code'],
                "uom": row['UOM'],
                "unit_price": float(row['Unit Price ($)']),
                "unit_cost": float(row['Unit Cost ($)']),
                "lead_time": int(row['Lead Time (days)'])
            })
            
            # Create relationships
            self.memgraph.execute("""
                MATCH (p:Product {code: $code})
                MATCH (c:Category {name: $category})
                CREATE (p)-[:BELONGS_TO]->(c)
            """, {
                "code": row['SKU Code'],
                "category": row['Category']
            })
            
            self.memgraph.execute("""
                MATCH (p:Product {code: $code})
                MATCH (co:Country {name: $country})
                CREATE (p)-[:OPERATES_IN]->(co)
            """, {
                "code": row['SKU Code'],
                "country": row['Country']
            })
        
        print(f"✅ Loaded {len(df)} products with categories and countries")
    
    def load_financial_data(self):
        """Load financial data and create relationships"""
        print("💰 Loading financial data...")
        
        if "Financial Plan" not in self.data_cache:
            print("❌ Financial Plan sheet not found")
            return
        
        df = self.data_cache["Financial Plan"]
        
        for _, row in df.iterrows():
            self.memgraph.execute("""
                MATCH (p:Product {code: $code})
                SET p.total_volume = $volume,
                    p.total_revenue = $revenue,
                    p.total_cogs = $cogs,
                    p.gross_profit = $profit,
                    p.gross_margin = $margin
            """, {
                "code": row['SKU Code'],
                "volume": int(row['Total Volume']),
                "revenue": float(row['Total Revenue ($)']),
                "cogs": float(row['Total COGS ($)']),
                "profit": float(row['Gross Profit ($)']),
                "margin": float(row['Gross Margin (%)'])
            })
        
        print(f"✅ Loaded financial data for {len(df)} products")
    
    def load_logistics_data(self):
        """Load logistics planning data"""
        print("🚚 Loading logistics data...")
        
        if "Logistics Plan" not in self.data_cache:
            print("❌ Logistics Plan sheet not found")
            return
        
        df = self.data_cache["Logistics Plan"]
        
        for _, row in df.iterrows():
            self.memgraph.execute("""
                MATCH (p:Product {code: $code})
                SET p.reorder_point = $reorder_point,
                    p.max_inventory = $max_inventory,
                    p.min_order_quantity = $min_order_qty
            """, {
                "code": row['SKU Code'],
                "reorder_point": int(row['Reorder Point']),
                "max_inventory": int(row['Max Inventory']),
                "min_order_qty": int(row['Min Order Quantity'])
            })
        
        print(f"✅ Loaded logistics data for {len(df)} products")
    
    def load_graph_structure(self):
        """Load graph structure data (nodes and edges)"""
        print("🕸️  Loading graph structure...")
        
        # Load nodes
        if "Raw - Nodes" in self.data_cache:
            nodes_df = self.data_cache["Raw - Nodes"]
            for _, row in nodes_df.iterrows():
                self.memgraph.execute("""
                    CREATE (n:GraphNode {code: $code})
                """, {"code": row['Node']})
            print(f"✅ Loaded {len(nodes_df)} graph nodes")
        
        # Load node types
        if "Raw - Node Types" in self.data_cache:
            types_df = self.data_cache["Raw - Node Types"]
            for _, row in types_df.iterrows():
                self.memgraph.execute("""
                    MATCH (n:GraphNode {code: $code})
                    SET n.group = $group, n.subgroup = $subgroup
                """, {
                    "code": row['Node'],
                    "group": row['Group'],
                    "subgroup": row['Sub-Group']
                })
            print(f"✅ Loaded node types for {len(types_df)} nodes")
        
        # Load edges
        edge_sheets = [sheet for sheet in self.data_cache.keys() if 'Raw - Edges' in sheet]
        for sheet in edge_sheets:
            df = self.data_cache[sheet]
            if 'node1' in df.columns and 'node2' in df.columns:
                for _, row in df.iterrows():
                    relationship_type = sheet.replace('Raw - Edges ', '').replace(' ', '_').upper()
                    self.memgraph.execute(f"""
                        MATCH (n1:GraphNode {{code: $node1}})
                        MATCH (n2:GraphNode {{code: $node2}})
                        CREATE (n1)-[:{relationship_type}]->(n2)
                    """, {
                        "node1": row['node1'],
                        "node2": row['node2']
                    })
                print(f"✅ Loaded {len(df)} edges from {sheet}")
    
    def load_temporal_data(self):
        """Load temporal data (production, sales, etc.)"""
        print("⏰ Loading temporal data...")
        
        temporal_sheets = [sheet for sheet in self.data_cache.keys() if 'Raw -' in sheet and any(x in sheet for x in ['Production', 'Sales', 'Delivery', 'Factory'])]
        
        for sheet in temporal_sheets:
            df = self.data_cache[sheet]
            if 'Date' in df.columns:
                data_type = sheet.replace('Raw - ', '').replace(' - ', '_').replace(' ', '_').upper()
                
                # Create date nodes and relationships
                for _, row in df.iterrows():
                    date_str = str(row['Date']).split()[0]  # Get date part only
                    
                    # Create date node
                    self.memgraph.execute("""
                        MERGE (d:Date {value: $date})
                    """, {"date": date_str})
                    
                    # Create product-date relationships with values
                    for col in df.columns:
                        if col != 'Date' and pd.notna(row[col]):
                            self.memgraph.execute(f"""
                                MATCH (p:Product {{code: $code}})
                                MATCH (d:Date {{value: $date}})
                                CREATE (p)-[:{data_type} {{value: $value}}]->(d)
                            """, {
                                "code": col,
                                "date": date_str,
                                "value": float(row[col])
                            })
                
                print(f"✅ Loaded {data_type} data from {sheet}")
    
    def load_all_data(self):
        """Load all data into the graph database"""
        if not self.connect_to_memgraph():
            return False
        
        if not self.load_excel_data():
            return False
        
        self.clear_database()
        self.create_schema()
        
        # Load data in order
        self.load_master_data()
        self.load_financial_data()
        self.load_logistics_data()
        self.load_graph_structure()
        self.load_temporal_data()
        
        print("🎉 All data loaded successfully!")
        return True
    
    def get_database_stats(self):
        """Get database statistics"""
        print("\n📊 Database Statistics:")
        
        stats_queries = [
            ("Total Products", "MATCH (p:Product) RETURN count(p) as count"),
            ("Total Categories", "MATCH (c:Category) RETURN count(c) as count"),
            ("Total Countries", "MATCH (co:Country) RETURN count(co) as count"),
            ("Total Graph Nodes", "MATCH (n:GraphNode) RETURN count(n) as count"),
            ("Total Relationships", "MATCH ()-[r]->() RETURN count(r) as count"),
            ("Total Dates", "MATCH (d:Date) RETURN count(d) as count")
        ]
        
        for name, query in stats_queries:
            try:
                result = self.memgraph.execute(query)
                count = result[0]['count'] if result else 0
                print(f"   {name}: {count}")
            except Exception as e:
                print(f"   {name}: Error - {e}")

class FMCGGraphAnalyzer:
    """Provides sample queries and analysis for the FMCG graph"""
    
    def __init__(self, memgraph_connection):
        self.memgraph = memgraph_connection
    
    def run_sample_queries(self):
        """Run sample queries to demonstrate graph capabilities"""
        print("\n🔍 Sample Queries and Results:")
        
        queries = [
            {
                "name": "Top 5 Products by Revenue",
                "query": """
                MATCH (p:Product)
                WHERE p.total_revenue IS NOT NULL
                RETURN p.code as product, p.total_revenue as revenue
                ORDER BY p.total_revenue DESC
                LIMIT 5
                """
            },
            {
                "name": "Products by Category with Average Margin",
                "query": """
                MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
                WHERE p.gross_margin IS NOT NULL
                RETURN c.name as category, 
                       count(p) as product_count,
                       avg(p.gross_margin) as avg_margin
                ORDER BY avg_margin DESC
                """
            },
            {
                "name": "Products with Longest Lead Times",
                "query": """
                MATCH (p:Product)
                WHERE p.lead_time IS NOT NULL
                RETURN p.code as product, p.lead_time as lead_time_days
                ORDER BY p.lead_time DESC
                LIMIT 10
                """
            },
            {
                "name": "Country Performance Analysis",
                "query": """
                MATCH (p:Product)-[:OPERATES_IN]->(co:Country)
                WHERE p.total_revenue IS NOT NULL
                RETURN co.name as country,
                       count(p) as product_count,
                       sum(p.total_revenue) as total_revenue,
                       avg(p.gross_margin) as avg_margin
                ORDER BY total_revenue DESC
                """
            },
            {
                "name": "Graph Node Connectivity",
                "query": """
                MATCH (n:GraphNode)-[r]->(m:GraphNode)
                RETURN n.code as source, m.code as target, type(r) as relationship
                LIMIT 10
                """
            }
        ]
        
        for query_info in queries:
            print(f"\n📋 {query_info['name']}:")
            try:
                result = self.memgraph.execute(query_info['query'])
                if result:
                    # Print column headers
                    if result:
                        columns = list(result[0].keys())
                        print("   " + " | ".join(columns))
                        print("   " + "-" * (len(" | ".join(columns))))
                        
                        # Print data rows
                        for row in result[:5]:  # Limit to 5 rows for display
                            values = [str(row[col]) for col in columns]
                            print("   " + " | ".join(values))
                        
                        if len(result) > 5:
                            print(f"   ... and {len(result) - 5} more rows")
                else:
                    print("   No results found")
            except Exception as e:
                print(f"   Error: {e}")

def start_memgraph_lab():
    """Start Memgraph Lab server"""
    print("\n🌐 Starting Memgraph Lab...")
    print("   Memgraph Lab should be available at: http://localhost:3000")
    print("   If not automatically opened, please open your browser to that URL")
    
    # Try to open browser
    try:
        webbrowser.open('http://localhost:3000')
    except:
        pass
    
    print("   💡 In Memgraph Lab:")
    print("   - Connect to: localhost:7687")
    print("   - Username: (leave empty)")
    print("   - Password: (leave empty)")
    print("   - Database: memgraph")

def main():
    """Main function to run the FMCG graph loader and analyzer"""
    print("🚀 Enhanced FMCG SOP Dataset - Memgraph Graph Database Loader")
    print("=" * 70)
    
    # Check if Excel file exists
    excel_file = "Enhanced_FMCG_SOP_Dataset.xlsx"
    if not os.path.exists(excel_file):
        print(f"❌ Excel file '{excel_file}' not found in current directory")
        print("   Please ensure the Enhanced FMCG SOP Dataset Excel file is in the same directory as this script")
        return
    
    # Initialize loader
    loader = FMCGGraphLoader(excel_file)
    
    # Load data
    if loader.load_all_data():
        # Get statistics
        loader.get_database_stats()
        
        # Run sample queries
        analyzer = FMCGGraphAnalyzer(loader.memgraph)
        analyzer.run_sample_queries()
        
        # Start Memgraph Lab
        start_memgraph_lab()
        
        print("\n🎯 Next Steps:")
        print("   1. Open Memgraph Lab at http://localhost:3000")
        print("   2. Connect to localhost:7687")
        print("   3. Explore the graph structure and run queries")
        print("   4. Try the sample queries shown above")
        
        print("\n📝 Sample Cypher Queries to Try in Memgraph Lab:")
        print("   // Find all products in a category")
        print("   MATCH (p:Product)-[:BELONGS_TO]->(c:Category {name: 'Legumes'}) RETURN p")
        print("   ")
        print("   // Find products with high margins")
        print("   MATCH (p:Product) WHERE p.gross_margin > 50 RETURN p")
        print("   ")
        print("   // Find graph relationships")
        print("   MATCH (n:GraphNode)-[r]->(m:GraphNode) RETURN n, r, m LIMIT 20")
        print("   ")
        print("   // Find temporal patterns")
        print("   MATCH (p:Product)-[r:RAW_PRODUCTION_UNIT]->(d:Date) RETURN p, r, d LIMIT 10")
        
    else:
        print("❌ Failed to load data. Please check the error messages above.")

if __name__ == "__main__":
    main()
