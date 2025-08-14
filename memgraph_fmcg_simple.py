#!/usr/bin/env python3
"""
Enhanced FMCG SOP Dataset - Memgraph Graph Database Loader (Simple Version)
Uses neo4j driver to connect to Memgraph and load the dataset
"""

import pandas as pd
import sys
import subprocess
from pathlib import Path
from neo4j import GraphDatabase

class FMCGGraphLoader:
    def __init__(self):
        self.driver = None
        self.excel_file = "Enhanced_FMCG_SOP_Dataset.xlsx"
        
    def connect_to_memgraph(self) -> bool:
        """Connect to Memgraph database using neo4j driver"""
        try:
            # Memgraph uses the same Bolt protocol as Neo4j
            self.driver = GraphDatabase.driver("bolt://localhost:7687", auth=("", ""))
            # Test connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS test")
                print("✅ Connected to Memgraph successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to Memgraph: {e}")
            print("💡 Make sure Memgraph is running with:")
            print("   docker run -p 7687:7687 -p 7444:7444 memgraph/memgraph-platform")
            return False
    
    def clear_database(self):
        """Clear all data from the database"""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                print("✅ Database cleared")
        except Exception as e:
            print(f"❌ Failed to clear database: {e}")
    
    def load_master_data(self):
        """Load master data from Excel"""
        try:
            df = pd.read_excel(self.excel_file, sheet_name="Master Data")
            print(f"📊 Loading {len(df)} master data records...")
            
            with self.driver.session() as session:
                for _, row in df.iterrows():
                    # Create Product nodes
                    if pd.notna(row.get('SKU Code')):
                        session.run("""
                            MERGE (p:Product {code: $code})
                            SET p.category = $category, p.country = $country, p.uom = $uom,
                                p.unit_price = $unit_price, p.unit_cost = $unit_cost, p.lead_time = $lead_time
                        """, {
                            'code': row['SKU Code'],
                            'category': row.get('Category', ''),
                            'country': row.get('Country', ''),
                            'uom': row.get('UOM', ''),
                            'unit_price': row.get('Unit Price ($)', 0),
                            'unit_cost': row.get('Unit Cost ($)', 0),
                            'lead_time': row.get('Lead Time (days)', 0)
                        })
            
            print("✅ Master data loaded")
        except Exception as e:
            print(f"❌ Failed to load master data: {e}")
    
    def load_financial_data(self):
        """Load financial plan data"""
        try:
            df = pd.read_excel(self.excel_file, sheet_name="Financial Plan")
            print(f"💰 Loading {len(df)} financial records...")
            
            with self.driver.session() as session:
                for _, row in df.iterrows():
                    if pd.notna(row.get('SKU Code')):
                        session.run("""
                            MATCH (p:Product {code: $code})
                            SET p.total_volume = $volume, p.total_revenue = $revenue, 
                                p.total_cogs = $cogs, p.gross_profit = $profit, p.gross_margin = $margin
                        """, {
                            'code': row['SKU Code'],
                            'volume': row.get('Total Volume', 0),
                            'revenue': row.get('Total Revenue ($)', 0),
                            'cogs': row.get('Total COGS ($)', 0),
                            'profit': row.get('Gross Profit ($)', 0),
                            'margin': row.get('Gross Margin (%)', 0)
                        })
            
            print("✅ Financial data loaded")
        except Exception as e:
            print(f"❌ Failed to load financial data: {e}")
    
    def load_logistics_data(self):
        """Load logistics plan data"""
        try:
            df = pd.read_excel(self.excel_file, sheet_name="Logistics Plan")
            print(f"🚚 Loading {len(df)} logistics records...")
            
            with self.driver.session() as session:
                for _, row in df.iterrows():
                    if pd.notna(row.get('SKU Code')):
                        session.run("""
                            MATCH (p:Product {code: $code})
                            SET p.reorder_point = $reorder_point, p.max_inventory = $max_inventory, 
                                p.min_order_quantity = $min_order_quantity
                        """, {
                            'code': row['SKU Code'],
                            'reorder_point': row.get('Reorder Point', 0),
                            'max_inventory': row.get('Max Inventory', 0),
                            'min_order_quantity': row.get('Min Order Quantity', 0)
                        })
            
            print("✅ Logistics data loaded")
        except Exception as e:
            print(f"❌ Failed to load logistics data: {e}")
    
    def load_graph_structure(self):
        """Load raw graph nodes and edges"""
        try:
            # Load nodes
            nodes_df = pd.read_excel(self.excel_file, sheet_name="Raw - Nodes")
            print(f"🔗 Loading {len(nodes_df)} graph nodes...")
            
            with self.driver.session() as session:
                for _, row in nodes_df.iterrows():
                    session.run("""
                        MERGE (n:GraphNode {code: $code})
                        SET n.type = $type, n.name = $name
                    """, {
                        'code': row['Node'],
                        'type': row.get('Type', ''),
                        'name': row.get('Name', '')
                    })
            
            # Load different types of edges
            edge_sheets = [
                "Raw - Edges Group", "Raw - Edges SubGroup", 
                "Raw - Edges Plant", "Raw - Edges Storage"
            ]
            
            for sheet in edge_sheets:
                try:
                    edges_df = pd.read_excel(self.excel_file, sheet_name=sheet)
                    print(f"🔗 Loading {len(edges_df)} {sheet} edges...")
                    
                    with self.driver.session() as session:
                        for _, row in edges_df.iterrows():
                            relationship_type = sheet.replace('Raw - Edges ', '').replace(' ', '_').upper()
                            session.run(f"""
                                MATCH (n1:GraphNode {{code: $from_code}})
                                MATCH (n2:GraphNode {{code: $to_code}})
                                MERGE (n1)-[:{relationship_type}]->(n2)
                            """, {
                                'from_code': row['node1'],
                                'to_code': row['node2']
                            })
                    
                    print(f"✅ {sheet} loaded")
                except Exception as e:
                    print(f"⚠️  Skipping {sheet}: {e}")
            
            print("✅ Graph structure loaded")
        except Exception as e:
            print(f"❌ Failed to load graph structure: {e}")
    
    def load_temporal_data(self):
        """Load temporal data (delivery, production, sales)"""
        try:
            temporal_sheets = [
                "Raw - DeliveryTo-Unit", "Raw - DeliveryTo-Weigh",
                "Raw - FactoryIssue - Unit", "Raw - FactoryIssue - Weight",
                "Raw - Production - Unit", "Raw - Production - Weight",
                "Raw - SalesOrder - Unit", "Raw - SalesOrder - Weight"
            ]
            
            for sheet in temporal_sheets:
                try:
                    df = pd.read_excel(self.excel_file, sheet_name=sheet)
                    print(f"📅 Loading {len(df)} {sheet} records...")
                    
                    # Extract data type from sheet name
                    data_type = sheet.replace('Raw - ', '').replace(' - ', '_').replace(' ', '_').upper()
                    
                    with self.driver.session() as session:
                        for _, row in df.iterrows():
                            if pd.notna(row.get('SKU Code')) and pd.notna(row.get('Date')):
                                session.run(f"""
                                    MATCH (p:Product {{code: $product_code}})
                                    MERGE (t:TemporalEvent {{date: $date, type: $type}})
                                    MERGE (p)-[:{data_type} {{value: $value}}]->(t)
                                """, {
                                    'product_code': row['SKU Code'],
                                    'date': str(row['Date']),
                                    'type': data_type,
                                    'value': row.get('Value', 0)
                                })
                    
                    print(f"✅ {sheet} loaded")
                except Exception as e:
                    print(f"⚠️  Skipping {sheet}: {e}")
            
            print("✅ Temporal data loaded")
        except Exception as e:
            print(f"❌ Failed to load temporal data: {e}")
    
    def run_sample_queries(self):
        """Run sample queries to demonstrate the data"""
        print("\n🔍 Sample Queries:")
        print("=" * 50)
        
        queries = [
            ("Product Count", "MATCH (p:Product) RETURN count(p) as product_count"),
            ("GraphNode Count", "MATCH (n:GraphNode) RETURN count(n) as graphnode_count"),
            ("Top Products by Revenue", """
                MATCH (p:Product)
                WHERE p.total_revenue IS NOT NULL
                RETURN p.code, p.category, p.total_revenue
                ORDER BY p.total_revenue DESC
                LIMIT 5
            """),
            ("Products by Category", """
                MATCH (p:Product)
                RETURN p.category, count(p) as count
                ORDER BY count DESC
            """),
            ("Graph Structure", """
                MATCH (n1:GraphNode)-[r]->(n2:GraphNode)
                RETURN type(r) as relationship_type, count(r) as count
                ORDER BY count DESC
            """)
        ]
        
        with self.driver.session() as session:
            for name, query in queries:
                print(f"\n📊 {name}:")
                try:
                    result = session.run(query)
                    for record in result:
                        print(f"   {dict(record)}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
    
    def close(self):
        """Close the database connection"""
        if self.driver:
            self.driver.close()

def main():
    print("🚀 Enhanced FMCG SOP Dataset - Memgraph Graph Database Loader")
    print("=" * 70)
    
    loader = FMCGGraphLoader()
    
    if not loader.connect_to_memgraph():
        print("❌ Failed to load data. Please check the error messages above.")
        return
    
    try:
        # Load data
        loader.clear_database()
        loader.load_master_data()
        loader.load_financial_data()
        loader.load_logistics_data()
        loader.load_graph_structure()
        loader.load_temporal_data()
        
        # Run sample queries
        loader.run_sample_queries()
        
        print("\n🎉 Data loading complete!")
        print("🌐 Open Memgraph Lab at: http://localhost:3000")
        print("💡 Try these sample queries in Memgraph Lab:")
        print("   - MATCH (p:Product) RETURN p LIMIT 10")
        print("   - MATCH (n:GraphNode) RETURN n LIMIT 10")
        print("   - MATCH (n1:GraphNode)-[r]->(n2:GraphNode) RETURN n1, r, n2 LIMIT 10")
        print("   - MATCH (p:Product) WHERE p.total_revenue > 100000 RETURN p.code, p.category, p.total_revenue")
        
    except Exception as e:
        print(f"❌ Error during data loading: {e}")
    finally:
        loader.close()

if __name__ == "__main__":
    main()
