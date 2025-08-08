#!/usr/bin/env python3
"""
Debug Specific Data
Check what's actually stored in specific nodes
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

class SpecificDataDebugger:
    def __init__(self):
        self.graph = get_graph()
        
        if self.graph is None:
            raise Exception("Failed to connect to Neo4j database")
    
    def debug_specific_sku(self):
        """Debug a specific SKU to see all its properties"""
        
        print("🔍 Debugging Specific SKU Data...")
        
        try:
            # Get all properties of a specific SKU
            result = self.graph.query("""
                MATCH (sku:SKU)
                RETURN sku
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                sku_data = result[0]
                if isinstance(sku_data, dict) and 'sku' in sku_data:
                    sku = sku_data['sku']
                    print(f"📦 SKU Properties:")
                    for key, value in sku.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"📦 SKU Data: {sku_data}")
            else:
                print("❌ No SKU data found")
            
        except Exception as e:
            print(f"❌ Error in SKU debug: {str(e)}")
    
    def debug_specific_customer(self):
        """Debug a specific customer to see all its properties"""
        
        print("\n🔍 Debugging Specific Customer Data...")
        
        try:
            # Get all properties of a specific customer
            result = self.graph.query("""
                MATCH (cust:Customer)
                RETURN cust
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                customer_data = result[0]
                if isinstance(customer_data, dict) and 'cust' in customer_data:
                    customer = customer_data['cust']
                    print(f"👥 Customer Properties:")
                    for key, value in customer.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"👥 Customer Data: {customer_data}")
            else:
                print("❌ No customer data found")
            
        except Exception as e:
            print(f"❌ Error in Customer debug: {str(e)}")
    
    def debug_specific_manufacturing_plant(self):
        """Debug a specific manufacturing plant to see all its properties"""
        
        print("\n🔍 Debugging Specific Manufacturing Plant Data...")
        
        try:
            # Get all properties of a specific manufacturing plant
            result = self.graph.query("""
                MATCH (plant:ManufacturingPlant)
                RETURN plant
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                plant_data = result[0]
                if isinstance(plant_data, dict) and 'plant' in plant_data:
                    plant = plant_data['plant']
                    print(f"🏭 Manufacturing Plant Properties:")
                    for key, value in plant.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"🏭 Plant Data: {plant_data}")
            else:
                print("❌ No manufacturing plant data found")
            
        except Exception as e:
            print(f"❌ Error in Manufacturing Plant debug: {str(e)}")
    
    def debug_specific_promotional_campaign(self):
        """Debug a specific promotional campaign to see all its properties"""
        
        print("\n🔍 Debugging Specific Promotional Campaign Data...")
        
        try:
            # Get all properties of a specific promotional campaign
            result = self.graph.query("""
                MATCH (campaign:PromotionalCampaign)
                RETURN campaign
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                campaign_data = result[0]
                if isinstance(campaign_data, dict) and 'campaign' in campaign_data:
                    campaign = campaign_data['campaign']
                    print(f"📢 Promotional Campaign Properties:")
                    for key, value in campaign.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"📢 Campaign Data: {campaign_data}")
            else:
                print("❌ No promotional campaign data found")
            
        except Exception as e:
            print(f"❌ Error in Promotional Campaign debug: {str(e)}")
    
    def debug_specific_region(self):
        """Debug a specific region to see all its properties"""
        
        print("\n🔍 Debugging Specific Region Data...")
        
        try:
            # Get all properties of a specific region
            result = self.graph.query("""
                MATCH (reg:Region)
                RETURN reg
                LIMIT 1
            """)
            
            if result and len(result) > 0:
                region_data = result[0]
                if isinstance(region_data, dict) and 'reg' in region_data:
                    region = region_data['reg']
                    print(f"🌍 Region Properties:")
                    for key, value in region.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"🌍 Region Data: {region_data}")
            else:
                print("❌ No region data found")
            
        except Exception as e:
            print(f"❌ Error in Region debug: {str(e)}")
    
    def run_specific_debug(self):
        """Run all specific debug functions"""
        
        print("🚀 Starting Specific Data Debug...")
        print("=" * 60)
        
        try:
            self.debug_specific_sku()
            self.debug_specific_customer()
            self.debug_specific_manufacturing_plant()
            self.debug_specific_promotional_campaign()
            self.debug_specific_region()
            
            print("\n" + "=" * 60)
            print("🎉 Specific Data Debug Completed!")
            
        except Exception as e:
            print(f"❌ Error during debug: {str(e)}")
            raise

def main():
    """Main function to debug specific data"""
    
    try:
        # Initialize debugger
        debugger = SpecificDataDebugger()
        
        # Run specific debug
        debugger.run_specific_debug()
        
    except Exception as e:
        print(f"❌ Error during debug: {str(e)}")
        raise

if __name__ == "__main__":
    main() 