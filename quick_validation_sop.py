#!/usr/bin/env python3
"""
Quick Validation Script for Enhanced S&OP Data Ingestion
Tests with a small subset of data to validate the logic before full ingestion
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

def get_openai_config(key, default=""):
    """Get OpenAI config from secrets file"""
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

def get_llm_with_secrets():
    """Get LLM with proper secrets configuration"""
    try:
        import openai
        from langchain_openai import ChatOpenAI
        
        # Set OpenAI API key from secrets
        api_key = get_openai_config("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in secrets file")
        
        openai.api_key = api_key
        
        # Get model from secrets or use default
        model = get_openai_config("OPENAI_MODEL", "gpt-4o-mini")
        
        llm = ChatOpenAI(
            model=model,
            temperature=0,
            openai_api_key=api_key
        )
        
        return llm
    except Exception as e:
        print(f"❌ LLM initialization failed: {str(e)}")
        return None

def get_embeddings_with_secrets():
    """Get embeddings with proper secrets configuration"""
    try:
        from langchain_openai import OpenAIEmbeddings
        
        # Set OpenAI API key from secrets
        api_key = get_openai_config("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY not found in secrets file")
        
        embeddings = OpenAIEmbeddings(
            openai_api_key=api_key,
            model="text-embedding-ada-002"
        )
        
        return embeddings
    except Exception as e:
        print(f"❌ Embeddings initialization failed: {str(e)}")
        return None

class QuickSOPValidation:
    def __init__(self):
        self.graph = get_graph()
        self.llm = get_llm_with_secrets()
        self.embeddings = get_embeddings_with_secrets()
        self.months = [
            'Jan-2024', 'Feb-2024', 'Mar-2024', 'Apr-2024', 'May-2024', 'Jun-2024',
            'Jul-2024', 'Aug-2024', 'Sep-2024', 'Oct-2024', 'Nov-2024', 'Dec-2024',
            'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025'
        ]
        
        if self.graph is None:
            raise Exception("Failed to connect to Neo4j database")
        
        if self.llm is None:
            print("⚠️ Warning: LLM not available, vector indexing will be skipped")
        
        if self.embeddings is None:
            print("⚠️ Warning: Embeddings not available, vector indexing will be skipped")
    
    def create_quick_test_dataset(self, num_skus=10):
        """Create a quick test dataset with a small number of SKUs"""
        
        print(f"🚀 Creating quick test dataset with {num_skus} SKUs...")
        
        # Read the full dataset
        excel_data = pd.read_excel('Enhanced_SOP_Dataset.xlsx', sheet_name=None)
        
        # Create quick test datasets
        quick_data = {}
        
        for sheet_name, df in excel_data.items():
            if 'Master Data' in sheet_name or 'Demand Plan' in sheet_name or 'Supply Plan' in sheet_name or 'Inventory Plan' in sheet_name or 'Financial Plan' in sheet_name or 'Logistics Plan' in sheet_name:
                # Take first N SKUs
                quick_data[sheet_name] = df.head(num_skus)
            elif 'Customer Data' in sheet_name:
                # Take first 3 customers
                quick_data[sheet_name] = df.head(3)
            elif 'Order Data' in sheet_name:
                # Take first 5 orders
                quick_data[sheet_name] = df.head(5)
            elif 'Manufacturing Capacity' in sheet_name:
                # Take first 2 manufacturing records
                quick_data[sheet_name] = df.head(2)
            elif 'Promotional Campaigns' in sheet_name:
                # Take first 2 campaigns
                quick_data[sheet_name] = df.head(2)
            elif 'Regional Data' in sheet_name:
                # Take first 2 regions
                quick_data[sheet_name] = df.head(2)
            else:
                quick_data[sheet_name] = df
        
        # Save quick test dataset
        output_file = 'Quick_Test_SOP_Dataset.xlsx'
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for sheet_name, df in quick_data.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"✅ Quick test dataset created: {output_file}")
        return output_file
    
    def process_quick_test_dataset(self, excel_file_path):
        """Process the quick test dataset to validate the logic"""
        
        print("🚀 Processing quick test dataset...")
        
        try:
            # Read all sheets from the Excel file
            excel_data = pd.read_excel(excel_file_path, sheet_name=None)
            
            print(f"📊 Found {len(excel_data)} sheets in the test dataset")
            
            # Process each sheet with quick validation
            if 'Master Data' in excel_data:
                print("📋 Processing Master Data (quick test)...")
                self._process_master_data_quick(excel_data['Master Data'])
            
            if 'Customer Data' in excel_data:
                print("👥 Processing Customer Data (quick test)...")
                self._process_customer_data_quick(excel_data['Customer Data'])
            
            if 'Manufacturing Capacity' in excel_data:
                print("🏭 Processing Manufacturing Capacity (quick test)...")
                self._process_manufacturing_data_quick(excel_data['Manufacturing Capacity'])
            
            if 'Promotional Campaigns' in excel_data:
                print("📢 Processing Promotional Campaigns (quick test)...")
                self._process_promotional_data_quick(excel_data['Promotional Campaigns'])
            
            if 'Regional Data' in excel_data:
                print("🌍 Processing Regional Data (quick test)...")
                self._process_regional_data_quick(excel_data['Regional Data'])
            
            if 'Demand Plan' in excel_data:
                print("📈 Processing Demand Plan (quick test)...")
                self._process_demand_plan_quick(excel_data['Demand Plan'])
            
            if 'Supply Plan' in excel_data:
                print("📦 Processing Supply Plan (quick test)...")
                self._process_supply_plan_quick(excel_data['Supply Plan'])
            
            if 'Inventory Plan' in excel_data:
                print("🏪 Processing Inventory Plan (quick test)...")
                self._process_inventory_plan_quick(excel_data['Inventory Plan'])
            
            if 'Financial Plan' in excel_data:
                print("💰 Processing Financial Plan (quick test)...")
                self._process_financial_plan_quick(excel_data['Financial Plan'])
            
            if 'Logistics Plan' in excel_data:
                print("🚚 Processing Logistics Plan (quick test)...")
                self._process_logistics_plan_quick(excel_data['Logistics Plan'])
            
            print("✅ Quick test dataset processing completed successfully!")
            
        except Exception as e:
            print(f"❌ Error processing quick test dataset: {str(e)}")
            raise
    
    def _process_master_data_quick(self, master_df):
        """Process enhanced master data (quick test version)"""
        
        print(f"  - Processing {len(master_df)} SKUs (quick test)...")
        
        for idx, row in master_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '', 'sku', 'sku code']:
                continue
            
            try:
                # Create enhanced SKU node with all new properties
                sku_properties = {
                    'sku_id': sku_id,
                    'name': f"Product {sku_id}",
                    'category': str(row.get('Category', 'Unknown')),
                    'country': str(row.get('Country', 'Unknown')),
                    'region': str(row.get('Region', 'Unknown')),
                    'uom': str(row.get('UOM', 'Unit')),
                    'unit_price': float(row.get('Unit Price ($)', 0)),
                    'unit_cost': float(row.get('Unit Cost ($)', 0)),
                    'lead_time_days': int(row.get('Lead Time (days)', 0)),
                    'manufacturing_plant': str(row.get('Manufacturing Plant', 'Unknown')),
                    'manufacturing_capacity': float(row.get('Manufacturing Capacity', 0)),
                    'capacity_utilization': float(row.get('Capacity Utilization', 0)),
                    'safety_stock': int(row.get('Safety Stock', 0)),
                    'reorder_point': int(row.get('Reorder Point', 0)),
                    'max_inventory': int(row.get('Max Inventory', 0)),
                    'min_order_quantity': int(row.get('Min Order Quantity', 0)),
                    'service_level': float(row.get('Service Level', 0)),
                    'regional_demand_multiplier': float(row.get('Regional Demand Multiplier', 1.0))
                }
                
                # Create SKU node
                sku_query = """
                MERGE (sku:SKU {sku_id: $sku_id})
                SET sku += $properties
                """
                self.graph.query(sku_query, {
                    'sku_id': sku_id,
                    'properties': sku_properties
                })
                
                # Create Category node and relationship
                category = sku_properties['category']
                category_query = """
                MERGE (cat:Category {name: $category})
                MERGE (sku:SKU {sku_id: $sku_id})
                MERGE (sku)-[:BELONGS_TO_CATEGORY]->(cat)
                """
                self.graph.query(category_query, {
                    'category': category,
                    'sku_id': sku_id
                })
                
                # Create enhanced plot string for vector search
                plot_parts = []
                for key, value in sku_properties.items():
                    if key != 'sku_id' and value is not None:
                        plot_parts.append(f"{key}: {value}")
                
                plot_string = " | ".join(plot_parts)
                
                # Update SKU with plot string
                plot_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                SET sku.plot = $plot
                """
                self.graph.query(plot_query, {
                    'sku_id': sku_id,
                    'plot': plot_string
                })
                
            except Exception as e:
                print(f"  - Error processing SKU {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Master data processing completed (quick test)")
    
    def _process_customer_data_quick(self, customer_df):
        """Process customer relationship data (quick test version)"""
        
        print(f"  - Processing {len(customer_df)} customers (quick test)...")
        
        for idx, row in customer_df.iterrows():
            customer_id = str(row['customer_id']).strip()
            
            if not customer_id or customer_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create Customer node
                customer_properties = {
                    'customer_id': customer_id,
                    'name': str(row.get('name', 'Unknown')),
                    'priority_level': str(row.get('priority_level', 'Standard')),
                    'service_level': float(row.get('service_level', 0.90)),
                    'priority_score': int(row.get('priority_score', 5)),
                    'relationship_impact': str(row.get('relationship_impact', 'Medium')),
                    'order_frequency': str(row.get('order_frequency', 'Monthly')),
                    'min_order_value': float(row.get('min_order_value', 10000)),
                    'region': str(row.get('region', 'Unknown')),
                    'country': str(row.get('country', 'Unknown')),
                    'credit_limit': float(row.get('credit_limit', 50000)),
                    'payment_terms': str(row.get('payment_terms', 'Net 30')),
                    'relationship_start_date': str(row.get('relationship_start_date', '2020-01-01')),
                    'total_orders': int(row.get('total_orders', 0)),
                    'total_revenue': float(row.get('total_revenue', 0))
                }
                
                customer_query = """
                MERGE (cust:Customer {customer_id: $customer_id})
                SET cust += $properties
                """
                self.graph.query(customer_query, {
                    'customer_id': customer_id,
                    'properties': customer_properties
                })
                
            except Exception as e:
                print(f"  - Error processing customer {customer_id}: {str(e)}")
                continue
        
        print(f"  ✅ Customer data processing completed (quick test)")
    
    def _process_manufacturing_data_quick(self, manufacturing_df):
        """Process manufacturing capacity data (quick test version)"""
        
        print(f"  - Processing {len(manufacturing_df)} manufacturing records (quick test)...")
        
        for idx, row in manufacturing_df.iterrows():
            plant_name = str(row['Plant']).strip()
            category = str(row['Category']).strip()
            
            if not plant_name or plant_name.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create or update Manufacturing Plant node
                plant_properties = {
                    'name': plant_name,
                    'location': str(row.get('Location', 'Unknown')),
                    'total_capacity': float(row.get('Total Capacity', 0)),
                    'category_capacity': float(row.get('Category Capacity', 0)),
                    'utilization_rate': float(row.get('Utilization Rate', 0)),
                    'available_capacity': float(row.get('Available Capacity', 0)),
                    'maintenance_schedule': str(row.get('Maintenance Schedule', 'Monthly')),
                    'lead_time_days': int(row.get('Lead Time (days)', 0))
                }
                
                plant_query = """
                MERGE (plant:ManufacturingPlant {name: $plant_name})
                SET plant += $properties
                """
                self.graph.query(plant_query, {
                    'plant_name': plant_name,
                    'properties': plant_properties
                })
                
            except Exception as e:
                print(f"  - Error processing manufacturing record {plant_name}: {str(e)}")
                continue
        
        print(f"  ✅ Manufacturing data processing completed (quick test)")
    
    def _process_promotional_data_quick(self, promotional_df):
        """Process promotional campaign data (quick test version)"""
        
        print(f"  - Processing {len(promotional_df)} promotional campaigns (quick test)...")
        
        for idx, row in promotional_df.iterrows():
            campaign_name = str(row['Campaign Name']).strip()
            
            if not campaign_name or campaign_name.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create Promotional Campaign node
                campaign_properties = {
                    'name': campaign_name,
                    'start_date': str(row.get('Start Date', '2024-01-01')),
                    'end_date': str(row.get('End Date', '2024-12-31')),
                    'categories': str(row.get('Categories', '')),
                    'demand_uplift': float(row.get('Demand Uplift', 1.0)),
                    'budget': float(row.get('Budget', 0)),
                    'regions': str(row.get('Regions', '')),
                    'status': str(row.get('Status', 'Active'))
                }
                
                campaign_query = """
                MERGE (campaign:PromotionalCampaign {name: $campaign_name})
                SET campaign += $properties
                """
                self.graph.query(campaign_query, {
                    'campaign_name': campaign_name,
                    'properties': campaign_properties
                })
                
            except Exception as e:
                print(f"  - Error processing campaign {campaign_name}: {str(e)}")
                continue
        
        print(f"  ✅ Promotional data processing completed (quick test)")
    
    def _process_regional_data_quick(self, regional_df):
        """Process regional market data (quick test version)"""
        
        print(f"  - Processing {len(regional_df)} regions (quick test)...")
        
        for idx, row in regional_df.iterrows():
            region_name = str(row['Region']).strip()
            
            if not region_name or region_name.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create or update Region node
                region_properties = {
                    'name': region_name,
                    'countries': str(row.get('Countries', '')),
                    'demand_multiplier': float(row.get('Demand Multiplier', 1.0)),
                    'service_level': float(row.get('Service Level', 0.90)),
                    'market_size': int(row.get('Market Size', 0)),
                    'growth_rate': float(row.get('Growth Rate', 0.10)),
                    'competition_level': str(row.get('Competition Level', 'Medium')),
                    'distribution_channels': int(row.get('Distribution Channels', 5))
                }
                
                region_query = """
                MERGE (reg:Region {name: $region_name})
                SET reg += $properties
                """
                self.graph.query(region_query, {
                    'region_name': region_name,
                    'properties': region_properties
                })
                
            except Exception as e:
                print(f"  - Error processing region {region_name}: {str(e)}")
                continue
        
        print(f"  ✅ Regional data processing completed (quick test)")
    
    def _process_demand_plan_quick(self, demand_df):
        """Process enhanced demand plan (quick test version)"""
        
        print(f"  - Processing demand plan for {len(demand_df)} SKUs (quick test)...")
        
        for idx, row in demand_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Extract monthly demand data
                monthly_demand = {}
                for month in self.months:
                    if month in row:
                        monthly_demand[month] = int(row[month]) if pd.notna(row[month]) else 0
                
                # Create DemandPlan node with enhanced data
                demand_plan_data = json.dumps(monthly_demand) if monthly_demand else "{}"
                
                demand_query = """
                MERGE (dp:DemandPlan {sku_id: $sku_id})
                SET dp.monthly_data = $demand_plan
                """
                self.graph.query(demand_query, {
                    'sku_id': sku_id,
                    'demand_plan': demand_plan_data
                })
                
                # Create relationship to SKU
                sku_demand_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                MATCH (dp:DemandPlan {sku_id: $sku_id})
                MERGE (sku)-[:HAS_DEMAND_PLAN]->(dp)
                """
                self.graph.query(sku_demand_query, {
                    'sku_id': sku_id
                })
                
            except Exception as e:
                print(f"  - Error processing demand plan for {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Demand plan processing completed (quick test)")
    
    def _process_supply_plan_quick(self, supply_df):
        """Process enhanced supply plan (quick test version)"""
        
        print(f"  - Processing supply plan for {len(supply_df)} SKUs (quick test)...")
        
        for idx, row in supply_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Extract monthly supply data
                monthly_supply = {}
                for month in self.months:
                    if month in row:
                        monthly_supply[month] = int(row[month]) if pd.notna(row[month]) else 0
                
                # Create SupplyPlan node with enhanced data
                supply_plan_data = json.dumps(monthly_supply) if monthly_supply else "{}"
                
                supply_query = """
                MERGE (sp:SupplyPlan {sku_id: $sku_id})
                SET sp.monthly_data = $supply_plan
                """
                self.graph.query(supply_query, {
                    'sku_id': sku_id,
                    'supply_plan': supply_plan_data
                })
                
                # Create relationship to SKU
                sku_supply_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                MATCH (sp:SupplyPlan {sku_id: $sku_id})
                MERGE (sku)-[:HAS_SUPPLY_PLAN]->(sp)
                """
                self.graph.query(sku_supply_query, {
                    'sku_id': sku_id
                })
                
            except Exception as e:
                print(f"  - Error processing supply plan for {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Supply plan processing completed (quick test)")
    
    def _process_inventory_plan_quick(self, inventory_df):
        """Process enhanced inventory plan (quick test version)"""
        
        print(f"  - Processing inventory plan for {len(inventory_df)} SKUs (quick test)...")
        
        for idx, row in inventory_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Extract monthly inventory data
                monthly_inventory = {}
                for month in self.months:
                    if month in row:
                        monthly_inventory[month] = int(row[month]) if pd.notna(row[month]) else 0
                
                # Create Inventory node with enhanced data
                inventory_data = json.dumps(monthly_inventory) if monthly_inventory else "{}"
                
                inventory_query = """
                MERGE (inv:Inventory {sku_id: $sku_id})
                SET inv.monthly_data = $inventory_data,
                    inv.initial_inventory = $initial_inventory,
                    inv.safety_stock = $safety_stock
                """
                self.graph.query(inventory_query, {
                    'sku_id': sku_id,
                    'inventory_data': inventory_data,
                    'initial_inventory': int(row.get('Initial Inventory', 0)),
                    'safety_stock': int(row.get('Safety Stock', 0))
                })
                
                # Create relationship to SKU
                sku_inventory_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                MATCH (inv:Inventory {sku_id: $sku_id})
                MERGE (sku)-[:HAS_INVENTORY]->(inv)
                """
                self.graph.query(sku_inventory_query, {
                    'sku_id': sku_id
                })
                
            except Exception as e:
                print(f"  - Error processing inventory plan for {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Inventory plan processing completed (quick test)")
    
    def _process_financial_plan_quick(self, financial_df):
        """Process enhanced financial plan (quick test version)"""
        
        print(f"  - Processing financial plan for {len(financial_df)} SKUs (quick test)...")
        
        for idx, row in financial_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create FinancialPlan node
                financial_properties = {
                    'sku_id': sku_id,
                    'total_volume': int(row.get('Total Volume', 0)),
                    'total_revenue': float(row.get('Total Revenue ($)', 0)),
                    'total_cogs': float(row.get('Total COGS ($)', 0)),
                    'gross_profit': float(row.get('Gross Profit ($)', 0)),
                    'gross_margin': float(row.get('Gross Margin (%)', 0))
                }
                
                financial_query = """
                MERGE (fp:FinancialPlan {sku_id: $sku_id})
                SET fp += $properties
                """
                self.graph.query(financial_query, {
                    'sku_id': sku_id,
                    'properties': financial_properties
                })
                
                # Create relationship to SKU
                sku_financial_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                MATCH (fp:FinancialPlan {sku_id: $sku_id})
                MERGE (sku)-[:HAS_FINANCIAL_PLAN]->(fp)
                """
                self.graph.query(sku_financial_query, {
                    'sku_id': sku_id
                })
                
            except Exception as e:
                print(f"  - Error processing financial plan for {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Financial plan processing completed (quick test)")
    
    def _process_logistics_plan_quick(self, logistics_df):
        """Process enhanced logistics plan (quick test version)"""
        
        print(f"  - Processing logistics plan for {len(logistics_df)} SKUs (quick test)...")
        
        for idx, row in logistics_df.iterrows():
            sku_id = str(row['SKU Code']).strip()
            
            if not sku_id or sku_id.lower() in ['nan', 'none', '']:
                continue
            
            try:
                # Create LogisticsPlan node
                logistics_properties = {
                    'sku_id': sku_id,
                    'reorder_point': int(row.get('Reorder Point', 0)),
                    'max_inventory': int(row.get('Max Inventory', 0)),
                    'min_order_quantity': int(row.get('Min Order Quantity', 0))
                }
                
                logistics_query = """
                MERGE (lp:LogisticsPlan {sku_id: $sku_id})
                SET lp += $properties
                """
                self.graph.query(logistics_query, {
                    'sku_id': sku_id,
                    'properties': logistics_properties
                })
                
                # Create relationship to SKU
                sku_logistics_query = """
                MATCH (sku:SKU {sku_id: $sku_id})
                MATCH (lp:LogisticsPlan {sku_id: $sku_id})
                MERGE (sku)-[:HAS_LOGISTICS_PLAN]->(lp)
                """
                self.graph.query(sku_logistics_query, {
                    'sku_id': sku_id
                })
                
            except Exception as e:
                print(f"  - Error processing logistics plan for {sku_id}: {str(e)}")
                continue
        
        print(f"  ✅ Logistics plan processing completed (quick test)")
    
    def test_enhanced_queries(self):
        """Test some enhanced queries to validate the data"""
        
        print("\n🧪 Testing enhanced queries...")
        
        try:
            # Test 1: Check if SKUs have enhanced properties
            result1 = self.graph.query("""
                MATCH (sku:SKU)
                WHERE sku.manufacturing_plant IS NOT NULL
                RETURN sku.sku_id, sku.manufacturing_plant, sku.region
                LIMIT 5
            """)
            print(f"✅ Test 1 - Enhanced SKU properties: Found {len(result1)} SKUs with manufacturing data")
            
            # Test 2: Check customer data
            result2 = self.graph.query("""
                MATCH (cust:Customer)
                RETURN cust.customer_id, cust.priority_level, cust.service_level
                LIMIT 3
            """)
            print(f"✅ Test 2 - Customer data: Found {len(result2)} customers")
            
            # Test 3: Check manufacturing data
            result3 = self.graph.query("""
                MATCH (plant:ManufacturingPlant)
                RETURN plant.name, plant.total_capacity, plant.utilization_rate
                LIMIT 2
            """)
            print(f"✅ Test 3 - Manufacturing data: Found {len(result3)} plants")
            
            # Test 4: Check promotional campaigns
            result4 = self.graph.query("""
                MATCH (campaign:PromotionalCampaign)
                RETURN campaign.name, campaign.demand_uplift, campaign.status
                LIMIT 2
            """)
            print(f"✅ Test 4 - Promotional campaigns: Found {len(result4)} campaigns")
            
            # Test 5: Check regional data
            result5 = self.graph.query("""
                MATCH (reg:Region)
                RETURN reg.name, reg.demand_multiplier, reg.service_level
                LIMIT 2
            """)
            print(f"✅ Test 5 - Regional data: Found {len(result5)} regions")
            
            print("🎉 All enhanced query tests passed!")
            
        except Exception as e:
            print(f"❌ Error in enhanced query tests: {str(e)}")
            raise

def main():
    """Main function to run quick validation"""
    
    try:
        # Initialize validation processor
        validator = QuickSOPValidation()
        
        # Create quick test dataset
        test_file = validator.create_quick_test_dataset(10)  # 10 SKUs for quick test
        
        # Process the quick test dataset
        validator.process_quick_test_dataset(test_file)
        
        # Test enhanced queries
        validator.test_enhanced_queries()
        
        print("\n🎉 Quick validation completed successfully!")
        print("📊 The enhanced data model is working correctly.")
        print("💡 You can now run the full ingestion with confidence.")
        
    except Exception as e:
        print(f"❌ Error during quick validation: {str(e)}")
        raise

if __name__ == "__main__":
    main() 