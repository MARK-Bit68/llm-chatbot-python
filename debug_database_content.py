#!/usr/bin/env python3
"""
Debug Database Content
Check what's actually stored in the Neo4j database
"""

import pandas as pd
import numpy as np
import json
import warnings
import os
from datetime import datetime

warnings.filterwarnings('ignore')

def get_neo4j_config(key, default=""):
    """Get Neo4j config from secrets file"""
    try:
        # Read from .streamlit/secrets.toml
        secrets_path = ".streamlit/secrets.toml"
        if os.path.exists(secrets_path):
            with open(secrets_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                for line in lines:
                    if line.startswith(f"{key}="):
                        return line.split('=', 1)[1].strip()
    except:
        pass
    
    # Fallback to environment variables
    return os.getenv(key, default)

def get_graph():
    """Get Neo4j graph connection with proper configuration"""
    try:
        from langchain_neo4j import Neo4jGraph
        
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Test the connection
        graph.query("RETURN 1 as test")
        return graph
    except Exception as e:
        print(f"❌ Neo4j connection failed: {str(e)}")
        return None

class DatabaseContentDebugger:
    def __init__(self):
        self.graph = get_graph()
        
        if self.graph is None:
            raise Exception("Failed to connect to Neo4j database")
    
    def debug_sku_data(self):
        """Debug SKU data in the database"""
        
        print("🔍 Debugging SKU Data in Database...")
        
        try:
            # Check SKU nodes
            result = self.graph.query("""
                MATCH (sku:SKU)
                RETURN sku.sku_id, sku.name, sku.category, sku.region, 
                       sku.manufacturing_plant, sku.manufacturing_capacity, 
                       sku.capacity_utilization, sku.lead_time_days
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} SKU nodes:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - SKU {row.get('sku_id', 'Unknown')}: {row.get('name', 'Unknown')}")
                    print(f"    Category: {row.get('category', 'Unknown')}")
                    print(f"    Region: {row.get('region', 'Unknown')}")
                    print(f"    Plant: {row.get('manufacturing_plant', 'Unknown')}")
                    print(f"    Capacity: {row.get('manufacturing_capacity', 'Unknown')}")
                    print(f"    Utilization: {row.get('capacity_utilization', 'Unknown')}")
                    print(f"    Lead Time: {row.get('lead_time_days', 'Unknown')}")
                else:
                    print(f"  - SKU {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in SKU debug: {str(e)}")
    
    def debug_customer_data(self):
        """Debug customer data in the database"""
        
        print("\n🔍 Debugging Customer Data in Database...")
        
        try:
            # Check Customer nodes
            result = self.graph.query("""
                MATCH (cust:Customer)
                RETURN cust.customer_id, cust.name, cust.priority_level, 
                       cust.service_level, cust.priority_score, cust.relationship_impact,
                       cust.total_revenue
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} Customer nodes:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - Customer {row.get('customer_id', 'Unknown')}: {row.get('name', 'Unknown')}")
                    print(f"    Priority: {row.get('priority_level', 'Unknown')}")
                    print(f"    Service Level: {row.get('service_level', 'Unknown')}")
                    print(f"    Priority Score: {row.get('priority_score', 'Unknown')}")
                    print(f"    Relationship Impact: {row.get('relationship_impact', 'Unknown')}")
                    print(f"    Revenue: ${row.get('total_revenue', 'Unknown')}")
                else:
                    print(f"  - Customer {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in Customer debug: {str(e)}")
    
    def debug_manufacturing_data(self):
        """Debug manufacturing data in the database"""
        
        print("\n🔍 Debugging Manufacturing Data in Database...")
        
        try:
            # Check Manufacturing Plant nodes
            result = self.graph.query("""
                MATCH (plant:ManufacturingPlant)
                RETURN plant.name, plant.location, plant.total_capacity, 
                       plant.utilization_rate, plant.available_capacity
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} Manufacturing Plant nodes:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - Plant {row.get('name', 'Unknown')}")
                    print(f"    Location: {row.get('location', 'Unknown')}")
                    print(f"    Total Capacity: {row.get('total_capacity', 'Unknown')}")
                    print(f"    Utilization Rate: {row.get('utilization_rate', 'Unknown')}")
                    print(f"    Available Capacity: {row.get('available_capacity', 'Unknown')}")
                else:
                    print(f"  - Plant {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in Manufacturing debug: {str(e)}")
    
    def debug_promotional_data(self):
        """Debug promotional data in the database"""
        
        print("\n🔍 Debugging Promotional Data in Database...")
        
        try:
            # Check Promotional Campaign nodes
            result = self.graph.query("""
                MATCH (campaign:PromotionalCampaign)
                RETURN campaign.name, campaign.demand_uplift, campaign.budget,
                       campaign.status, campaign.categories
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} Promotional Campaign nodes:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - Campaign {row.get('name', 'Unknown')}")
                    print(f"    Demand Uplift: {row.get('demand_uplift', 'Unknown')}")
                    print(f"    Budget: ${row.get('budget', 'Unknown')}")
                    print(f"    Status: {row.get('status', 'Unknown')}")
                    print(f"    Categories: {row.get('categories', 'Unknown')}")
                else:
                    print(f"  - Campaign {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in Promotional debug: {str(e)}")
    
    def debug_regional_data(self):
        """Debug regional data in the database"""
        
        print("\n🔍 Debugging Regional Data in Database...")
        
        try:
            # Check Region nodes
            result = self.graph.query("""
                MATCH (reg:Region)
                RETURN reg.name, reg.demand_multiplier, reg.service_level,
                       reg.market_size, reg.growth_rate
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} Region nodes:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - Region {row.get('name', 'Unknown')}")
                    print(f"    Demand Multiplier: {row.get('demand_multiplier', 'Unknown')}")
                    print(f"    Service Level: {row.get('service_level', 'Unknown')}")
                    print(f"    Market Size: {row.get('market_size', 'Unknown')}")
                    print(f"    Growth Rate: {row.get('growth_rate', 'Unknown')}")
                else:
                    print(f"  - Region {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in Regional debug: {str(e)}")
    
    def debug_relationships(self):
        """Debug relationships in the database"""
        
        print("\n🔍 Debugging Relationships in Database...")
        
        try:
            # Check SKU relationships
            result = self.graph.query("""
                MATCH (sku:SKU)-[:BELONGS_TO_CATEGORY]->(cat:Category)
                RETURN sku.sku_id, cat.name
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} SKU-Category relationships:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - SKU {row.get('sku_id', 'Unknown')} -> Category {row.get('name', 'Unknown')}")
                else:
                    print(f"  - SKU {row[0] if len(row) > 0 else 'Unknown'}")
            
            # Check Customer relationships
            result = self.graph.query("""
                MATCH (cust:Customer)-[:OPERATES_IN]->(reg:Region)
                RETURN cust.customer_id, reg.name
                LIMIT 5
            """)
            
            print(f"📊 Found {len(result)} Customer-Region relationships:")
            for row in result:
                if isinstance(row, dict):
                    print(f"  - Customer {row.get('customer_id', 'Unknown')} -> Region {row.get('name', 'Unknown')}")
                else:
                    print(f"  - Customer {row[0] if len(row) > 0 else 'Unknown'}")
            
        except Exception as e:
            print(f"❌ Error in Relationships debug: {str(e)}")
    
    def debug_node_counts(self):
        """Debug node counts in the database"""
        
        print("\n🔍 Debugging Node Counts in Database...")
        
        try:
            # Count all node types
            result = self.graph.query("""
                MATCH (n)
                RETURN labels(n) as labels, count(n) as count
                ORDER BY count DESC
            """)
            
            print(f"📊 Node counts by type:")
            for row in result:
                if isinstance(row, dict):
                    labels = row.get('labels', [])
                    count = row.get('count', 0)
                    print(f"  - {labels}: {count}")
                else:
                    print(f"  - {row[0] if len(row) > 0 else 'Unknown'}: {row[1] if len(row) > 1 else 0}")
            
        except Exception as e:
            print(f"❌ Error in Node Counts debug: {str(e)}")
    
    def run_comprehensive_debug(self):
        """Run all debug functions"""
        
        print("🚀 Starting Comprehensive Database Content Debug...")
        print("=" * 60)
        
        try:
            self.debug_node_counts()
            self.debug_sku_data()
            self.debug_customer_data()
            self.debug_manufacturing_data()
            self.debug_promotional_data()
            self.debug_regional_data()
            self.debug_relationships()
            
            print("\n" + "=" * 60)
            print("🎉 Database Content Debug Completed!")
            
        except Exception as e:
            print(f"❌ Error during debug: {str(e)}")
            raise

def main():
    """Main function to debug database content"""
    
    try:
        # Initialize debugger
        debugger = DatabaseContentDebugger()
        
        # Run comprehensive debug
        debugger.run_comprehensive_debug()
        
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        raise

if __name__ == "__main__":
    main() 