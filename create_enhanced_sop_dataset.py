#!/usr/bin/env python3
"""
Enhanced S&OP Dataset Generator for FMCG Supply Chain Planning
Creates a comprehensive dataset with all missing elements for role-based S&OP conversations
"""

import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class EnhancedSOPDatasetGenerator:
    def __init__(self):
        # Existing categories with enhanced configuration
        self.categories = {
            'Dried Fruits': {
                'price_range': (12, 18), 
                'cost_ratio': 0.4, 
                'lead_time': (8, 15),
                'manufacturing_capacity': 15000,
                'capacity_utilization': 0.85
            },
            'Nuts': {
                'price_range': (8, 14), 
                'cost_ratio': 0.6, 
                'lead_time': (15, 25),
                'manufacturing_capacity': 12000,
                'capacity_utilization': 0.90
            },
            'Legumes': {
                'price_range': (6, 12), 
                'cost_ratio': 0.5, 
                'lead_time': (20, 30),
                'manufacturing_capacity': 20000,
                'capacity_utilization': 0.75
            },
            'Grains': {
                'price_range': (4, 8), 
                'cost_ratio': 0.7, 
                'lead_time': (10, 20),
                'manufacturing_capacity': 25000,
                'capacity_utilization': 0.80
            },
            'Spices': {
                'price_range': (15, 25), 
                'cost_ratio': 0.3, 
                'lead_time': (25, 40),
                'manufacturing_capacity': 8000,
                'capacity_utilization': 0.70
            }
        }
        
        # Enhanced geographic and customer data
        self.regions = {
            'North America': {
                'countries': ['USA', 'Canada'],
                'demand_multiplier': 1.2,
                'service_level': 0.95
            },
            'Europe': {
                'countries': ['Germany', 'France', 'UK'],
                'demand_multiplier': 1.0,
                'service_level': 0.90
            },
            'Asia Pacific': {
                'countries': ['Japan', 'Australia', 'Singapore'],
                'demand_multiplier': 1.3,
                'service_level': 0.85
            },
            'Latin America': {
                'countries': ['Brazil', 'Mexico', 'Argentina'],
                'demand_multiplier': 0.8,
                'service_level': 0.80
            }
        }
        
        # Customer priority levels and relationships
        self.customer_priorities = {
            'Strategic': {
                'service_level': 0.98,
                'priority_score': 10,
                'relationship_impact': 'Critical',
                'order_frequency': 'Weekly',
                'min_order_value': 50000
            },
            'Key': {
                'service_level': 0.95,
                'priority_score': 8,
                'relationship_impact': 'High',
                'order_frequency': 'Bi-weekly',
                'min_order_value': 25000
            },
            'Standard': {
                'service_level': 0.90,
                'priority_score': 5,
                'relationship_impact': 'Medium',
                'order_frequency': 'Monthly',
                'min_order_value': 10000
            },
            'Opportunity': {
                'service_level': 0.85,
                'priority_score': 3,
                'relationship_impact': 'Low',
                'order_frequency': 'Quarterly',
                'min_order_value': 5000
            }
        }
        
        # Manufacturing facilities and capacity
        self.manufacturing_facilities = {
            'Plant_A': {
                'location': 'North America',
                'total_capacity': 50000,
                'categories': ['Dried Fruits', 'Nuts'],
                'utilization_rate': 0.85,
                'maintenance_schedule': 'Monthly'
            },
            'Plant_B': {
                'location': 'Europe',
                'total_capacity': 40000,
                'categories': ['Legumes', 'Grains'],
                'utilization_rate': 0.80,
                'maintenance_schedule': 'Bi-monthly'
            },
            'Plant_C': {
                'location': 'Asia Pacific',
                'total_capacity': 35000,
                'categories': ['Spices', 'Dried Fruits'],
                'utilization_rate': 0.75,
                'maintenance_schedule': 'Quarterly'
            }
        }
        
        # Promotional campaigns and marketing initiatives
        self.promotional_campaigns = {
            'Holiday_Season_2024': {
                'start_date': '2024-11-01',
                'end_date': '2024-12-31',
                'categories': ['Nuts', 'Dried Fruits'],
                'demand_uplift': 1.5,
                'budget': 500000,
                'regions': ['North America', 'Europe']
            },
            'Summer_Refresh_2024': {
                'start_date': '2024-06-01',
                'end_date': '2024-08-31',
                'categories': ['Grains', 'Legumes'],
                'demand_uplift': 1.3,
                'budget': 300000,
                'regions': ['North America', 'Asia Pacific']
            },
            'Health_Wellness_2024': {
                'start_date': '2024-01-01',
                'end_date': '2024-03-31',
                'categories': ['Spices', 'Nuts'],
                'demand_uplift': 1.4,
                'budget': 200000,
                'regions': ['Europe', 'Asia Pacific']
            }
        }
        
        self.months = [
            'Jan-2024', 'Feb-2024', 'Mar-2024', 'Apr-2024', 'May-2024', 'Jun-2024',
            'Jul-2024', 'Aug-2024', 'Sep-2024', 'Oct-2024', 'Nov-2024', 'Dec-2024',
            'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025'
        ]
        
        # Generate customer data
        self.customers = self._generate_customer_data()
        
        # Generate order data
        self.orders = self._generate_order_data()
        
    def _generate_customer_data(self):
        """Generate comprehensive customer data with relationships and priorities"""
        customers = []
        
        customer_names = [
            'Global Foods Inc', 'Premium Markets Ltd', 'Health First Co', 'Organic Delights',
            'Supermarket Chain A', 'Retail Giant B', 'Wholesale Club C', 'Gourmet Foods D',
            'International Trading E', 'Regional Distributor F', 'Specialty Store G',
            'Convenience Chain H', 'Online Retailer I', 'Food Service J', 'Export Company K'
        ]
        
        for i, name in enumerate(customer_names):
            priority = random.choices(
                list(self.customer_priorities.keys()),
                weights=[0.15, 0.25, 0.45, 0.15]
            )[0]
            
            priority_config = self.customer_priorities[priority]
            region = random.choice(list(self.regions.keys()))
            
            customers.append({
                'customer_id': f'CUST{i+1:03d}',
                'name': name,
                'priority_level': priority,
                'service_level': priority_config['service_level'],
                'priority_score': priority_config['priority_score'],
                'relationship_impact': priority_config['relationship_impact'],
                'order_frequency': priority_config['order_frequency'],
                'min_order_value': priority_config['min_order_value'],
                'region': region,
                'country': random.choice(self.regions[region]['countries']),
                'credit_limit': priority_config['min_order_value'] * random.uniform(3, 6),
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Net 60']),
                'relationship_start_date': f'202{random.randint(0,3)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
                'total_orders': random.randint(10, 100),
                'total_revenue': priority_config['min_order_value'] * random.uniform(5, 20)
            })
        
        return customers
    
    def _generate_order_data(self):
        """Generate customer order data with realistic patterns"""
        orders = []
        order_id = 1
        
        for customer in self.customers:
            customer_id = customer['customer_id']
            priority = customer['priority_level']
            order_frequency = customer['order_frequency']
            
            # Generate orders based on frequency
            if order_frequency == 'Weekly':
                num_orders = random.randint(40, 52)
            elif order_frequency == 'Bi-weekly':
                num_orders = random.randint(20, 26)
            elif order_frequency == 'Monthly':
                num_orders = random.randint(10, 12)
            else:  # Quarterly
                num_orders = random.randint(3, 4)
            
            for i in range(num_orders):
                # Generate order date
                start_date = datetime(2024, 1, 1)
                end_date = datetime(2025, 6, 30)
                order_date = start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
                
                # Order status based on date
                if order_date < datetime.now():
                    status = random.choices(['Delivered', 'In Transit', 'Processing'], weights=[0.7, 0.2, 0.1])[0]
                else:
                    status = random.choices(['Confirmed', 'Pending', 'Draft'], weights=[0.6, 0.3, 0.1])[0]
                
                # Generate order items (1-5 SKUs per order)
                num_items = random.randint(1, 5)
                order_items = []
                total_value = 0
                
                for j in range(num_items):
                    sku_id = f"SKU{random.randint(1, 500):03d}"
                    quantity = random.randint(10, 1000)
                    unit_price = random.uniform(5, 25)
                    item_value = quantity * unit_price
                    total_value += item_value
                    
                    order_items.append({
                        'sku_id': sku_id,
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'item_value': item_value
                    })
                
                # Ensure order meets minimum value
                if total_value < customer['min_order_value']:
                    # Increase quantities to meet minimum
                    multiplier = customer['min_order_value'] / total_value
                    for item in order_items:
                        item['quantity'] = int(item['quantity'] * multiplier)
                        item['item_value'] = item['quantity'] * item['unit_price']
                    total_value = sum(item['item_value'] for item in order_items)
                
                orders.append({
                    'order_id': f'ORD{order_id:06d}',
                    'customer_id': customer_id,
                    'order_date': order_date.strftime('%Y-%m-%d'),
                    'delivery_date': (order_date + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
                    'status': status,
                    'priority': priority,
                    'total_value': total_value,
                    'items': order_items,
                    'region': customer['region'],
                    'country': customer['country']
                })
                
                order_id += 1
        
        return orders
    
    def generate_enhanced_sku_data(self, num_skus=500):
        """Generate enhanced SKU data with manufacturing and regional information"""
        
        sku_data = []
        
        for i in range(1, num_skus + 1):
            sku_code = f"SKU{i:03d}"
            
            # Assign category with weighted distribution
            category_weights = {
                'Dried Fruits': 0.25,
                'Nuts': 0.20,
                'Legumes': 0.25,
                'Grains': 0.20,
                'Spices': 0.10
            }
            category = random.choices(list(category_weights.keys()), weights=list(category_weights.values()))[0]
            
            # Generate pricing based on category
            cat_config = self.categories[category]
            unit_price = round(random.uniform(*cat_config['price_range']), 2)
            unit_cost = round(unit_price * random.uniform(cat_config['cost_ratio'] - 0.1, cat_config['cost_ratio'] + 0.1), 2)
            lead_time = random.randint(*cat_config['lead_time'])
            
            # Assign manufacturing facility
            available_plants = [plant for plant, config in self.manufacturing_facilities.items() 
                              if category in config['categories']]
            manufacturing_plant = random.choice(available_plants) if available_plants else 'Plant_A'
            
            # Assign region and country
            region = random.choice(list(self.regions.keys()))
            country = random.choice(self.regions[region]['countries'])
            
            # Generate manufacturing capacity data
            plant_config = self.manufacturing_facilities[manufacturing_plant]
            manufacturing_capacity = plant_config['total_capacity'] * (cat_config['manufacturing_capacity'] / 100000)
            current_utilization = plant_config['utilization_rate']
            
            sku_data.append({
                'SKU Code': sku_code,
                'Category': category,
                'Country': country,
                'Region': region,
                'UOM': random.choice(['Kg', 'Pack', 'Box', 'Unit']),
                'Unit Price ($)': unit_price,
                'Unit Cost ($)': unit_cost,
                'Lead Time (days)': lead_time,
                'Manufacturing Plant': manufacturing_plant,
                'Manufacturing Capacity': manufacturing_capacity,
                'Capacity Utilization': current_utilization,
                'Safety Stock': int(lead_time * random.uniform(0.5, 1.0)),
                'Reorder Point': int(lead_time * random.uniform(0.8, 1.2)),
                'Max Inventory': int(lead_time * random.uniform(2, 3)),
                'Min Order Quantity': int(lead_time * random.uniform(0.5, 1.0)),
                'Service Level': self.regions[region]['service_level'],
                'Regional Demand Multiplier': self.regions[region]['demand_multiplier']
            })
        
        return pd.DataFrame(sku_data)
    
    def generate_enhanced_demand_plan(self, sku_df):
        """Generate enhanced demand plan with regional and promotional impacts"""
        
        demand_data = sku_df.copy()
        
        for idx, row in demand_data.iterrows():
            category = row['Category']
            region = row['Region']
            regional_multiplier = row['Regional Demand Multiplier']
            
            # Base seasonal pattern
            pattern = self._get_seasonal_pattern(category)
            base_demand = pattern['base_demand'] * regional_multiplier
            
            # Add some randomness to base demand
            base_demand *= random.uniform(0.8, 1.2)
            
            monthly_demand = []
            
            for month in self.months:
                # Parse month name to number
                month_name = month.split('-')[0]
                month_mapping = {
                    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
                }
                month_num = month_mapping.get(month_name, 1)
                year = int(month.split('-')[1])
                
                # Apply seasonal pattern
                if month_num in pattern['peak_months']:
                    multiplier = pattern['peak_multiplier']
                else:
                    multiplier = pattern['trough_multiplier']
                
                # Apply promotional impact
                promotional_multiplier = self._get_promotional_impact(category, month, year)
                
                # Calculate final demand
                demand = base_demand * multiplier * promotional_multiplier * random.uniform(0.9, 1.1)
                
                # Add some gaps/errors (5% chance of missing data)
                if random.random() < 0.05:
                    demand = 0
                
                # Add some extreme values (2% chance)
                if random.random() < 0.02:
                    demand *= random.uniform(2, 4)
                
                monthly_demand.append(int(demand))
            
            # Add monthly columns
            for i, month in enumerate(self.months):
                demand_data.loc[idx, month] = monthly_demand[i]
        
        return demand_data
    
    def _get_seasonal_pattern(self, category):
        """Get seasonal pattern for category"""
        patterns = {
            'Dried Fruits': {
                'peak_months': [11, 12, 1, 2],  # Winter holidays
                'base_demand': 800,
                'peak_multiplier': 1.8,
                'trough_multiplier': 0.6
            },
            'Nuts': {
                'peak_months': [11, 12, 1],  # Holiday season
                'base_demand': 600,
                'peak_multiplier': 2.2,
                'trough_multiplier': 0.5
            },
            'Legumes': {
                'peak_months': [3, 4, 5, 9, 10],  # Spring and Fall
                'base_demand': 1000,
                'peak_multiplier': 1.5,
                'trough_multiplier': 0.7
            },
            'Grains': {
                'peak_months': [6, 7, 8],  # Summer
                'base_demand': 1200,
                'peak_multiplier': 1.3,
                'trough_multiplier': 0.8
            },
            'Spices': {
                'peak_months': [10, 11, 12],  # Holiday cooking
                'base_demand': 400,
                'peak_multiplier': 2.0,
                'trough_multiplier': 0.6
            }
        }
        return patterns.get(category, patterns['Legumes'])
    
    def _get_promotional_impact(self, category, month, year):
        """Calculate promotional impact for category and month"""
        promotional_multiplier = 1.0
        
        for campaign_name, campaign in self.promotional_campaigns.items():
            if category in campaign['categories']:
                start_date = datetime.strptime(campaign['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(campaign['end_date'], '%Y-%m-%d')
                
                # Check if month falls within campaign period
                month_date = datetime.strptime(f"{month.split('-')[1]}-{month.split('-')[0]}-01", '%Y-%b-%d')
                
                if start_date <= month_date <= end_date:
                    promotional_multiplier *= campaign['demand_uplift']
        
        return promotional_multiplier
    
    def generate_enhanced_supply_plan(self, demand_df):
        """Generate enhanced supply plan with manufacturing constraints"""
        
        supply_data = demand_df.copy()
        
        for idx, row in supply_data.iterrows():
            category = row['Category']
            manufacturing_plant = row['Manufacturing Plant']
            manufacturing_capacity = row['Manufacturing Capacity']
            capacity_utilization = row['Capacity Utilization']
            
            # Calculate available capacity
            available_capacity = manufacturing_capacity * capacity_utilization
            
            monthly_supply = []
            
            for i, month in enumerate(self.months):
                demand = row[month]
                
                # Base supply is demand plus some buffer
                base_supply = demand * random.uniform(0.9, 1.1)
                
                # Apply manufacturing capacity constraints
                if base_supply > available_capacity:
                    base_supply = available_capacity * random.uniform(0.8, 0.95)
                
                # Add supply chain issues
                supply_issue_chance = 0.08  # 8% chance of supply issues
                
                if random.random() < supply_issue_chance:
                    # Supply shortage
                    base_supply *= random.uniform(0.3, 0.7)
                elif random.random() < 0.05:
                    # Supply surplus
                    base_supply *= random.uniform(1.3, 1.8)
                
                # Add some missing supply data (3% chance)
                if random.random() < 0.03:
                    base_supply = 0
                
                monthly_supply.append(int(base_supply))
            
            # Add monthly columns
            for i, month in enumerate(self.months):
                supply_data.loc[idx, month] = monthly_supply[i]
        
        return supply_data
    
    def create_enhanced_sop_dataset(self, output_file='Enhanced_SOP_Dataset.xlsx'):
        """Create the complete enhanced S&OP dataset with all missing elements"""
        
        print("🚀 Creating enhanced S&OP dataset with all missing elements...")
        
        # Generate enhanced SKU data
        print("📊 Generating enhanced SKU master data...")
        sku_df = self.generate_enhanced_sku_data(500)
        
        # Generate enhanced demand plan
        print("📈 Generating enhanced demand plan with regional and promotional impacts...")
        demand_df = self.generate_enhanced_demand_plan(sku_df)
        
        # Generate enhanced supply plan
        print("📦 Generating enhanced supply plan with manufacturing constraints...")
        supply_df = self.generate_enhanced_supply_plan(demand_df)
        
        # Generate inventory plan
        print("🏪 Generating inventory plan...")
        inventory_df = self._generate_inventory_plan(demand_df, supply_df)
        
        # Generate financial plan
        print("💰 Generating financial metrics...")
        financial_df = self._generate_financial_plan(sku_df, demand_df)
        
        # Generate logistics plan
        print("🚚 Generating logistics data...")
        logistics_df = self._generate_logistics_plan(sku_df)
        
        # Generate customer data
        print("👥 Generating customer relationship data...")
        customer_df = pd.DataFrame(self.customers)
        
        # Generate order data
        print("📋 Generating order management data...")
        order_df = pd.DataFrame(self.orders)
        
        # Generate manufacturing capacity data
        print("🏭 Generating manufacturing capacity data...")
        manufacturing_df = self._generate_manufacturing_data()
        
        # Generate promotional campaign data
        print("📢 Generating promotional campaign data...")
        promotional_df = self._generate_promotional_data()
        
        # Generate regional data
        print("🌍 Generating regional market data...")
        regional_df = self._generate_regional_data()
        
        # Create Excel file with multiple sheets
        print("💾 Saving to Excel file...")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            sku_df.to_excel(writer, sheet_name='Master Data', index=False)
            demand_df.to_excel(writer, sheet_name='Demand Plan', index=False)
            supply_df.to_excel(writer, sheet_name='Supply Plan', index=False)
            inventory_df.to_excel(writer, sheet_name='Inventory Plan', index=False)
            financial_df.to_excel(writer, sheet_name='Financial Plan', index=False)
            logistics_df.to_excel(writer, sheet_name='Logistics Plan', index=False)
            customer_df.to_excel(writer, sheet_name='Customer Data', index=False)
            order_df.to_excel(writer, sheet_name='Order Data', index=False)
            manufacturing_df.to_excel(writer, sheet_name='Manufacturing Capacity', index=False)
            promotional_df.to_excel(writer, sheet_name='Promotional Campaigns', index=False)
            regional_df.to_excel(writer, sheet_name='Regional Data', index=False)
        
        print(f"✅ Enhanced S&OP dataset created: {output_file}")
        
        # Print summary statistics
        print("\n📊 Enhanced Dataset Summary:")
        print(f"- Total SKUs: {len(sku_df)}")
        print(f"- Total Customers: {len(self.customers)}")
        print(f"- Total Orders: {len(self.orders)}")
        print(f"- Manufacturing Plants: {len(self.manufacturing_facilities)}")
        print(f"- Promotional Campaigns: {len(self.promotional_campaigns)}")
        print(f"- Regions: {len(self.regions)}")
        
        # Calculate some key metrics
        total_demand = sum([demand_df[month].sum() for month in self.months])
        total_supply = sum([supply_df[month].sum() for month in self.months])
        avg_margin = financial_df['Gross Margin (%)'].mean()
        total_order_value = sum(order['total_value'] for order in self.orders)
        
        print(f"- Total demand: {total_demand:,.0f} units")
        print(f"- Total supply: {total_supply:,.0f} units")
        print(f"- Average margin: {avg_margin:.1f}%")
        print(f"- Total order value: ${total_order_value:,.0f}")
        
        return output_file
    
    def _generate_inventory_plan(self, demand_df, supply_df):
        """Generate inventory plan with safety stock and realistic levels"""
        
        inventory_data = demand_df.copy()
        
        for idx, row in inventory_data.iterrows():
            category = row['Category']
            demand_avg = np.mean([row[month] for month in self.months])
            
            # Calculate safety stock (20-30% of average demand)
            safety_stock = int(demand_avg * random.uniform(0.2, 0.3))
            initial_inventory = int(demand_avg * random.uniform(0.8, 1.2))
            
            inventory_data.loc[idx, 'Initial Inventory'] = initial_inventory
            inventory_data.loc[idx, 'Safety Stock'] = safety_stock
            
            monthly_inventory = []
            current_inventory = initial_inventory
            
            for i, month in enumerate(self.months):
                demand = row[month]
                supply = supply_df.loc[idx, month]
                
                # Calculate inventory: previous + supply - demand
                current_inventory = max(0, current_inventory + supply - demand)
                
                # Add some inventory errors (2% chance)
                if random.random() < 0.02:
                    current_inventory *= random.uniform(0.5, 1.5)
                
                # Add some missing inventory data (2% chance)
                if random.random() < 0.02:
                    current_inventory = 0
                
                monthly_inventory.append(int(current_inventory))
            
            # Add monthly columns
            for i, month in enumerate(self.months):
                inventory_data.loc[idx, month] = monthly_inventory[i]
        
        return inventory_data
    
    def _generate_financial_plan(self, sku_df, demand_df):
        """Generate financial metrics"""
        
        financial_data = sku_df.copy()
        
        for idx, row in financial_data.iterrows():
            unit_price = row['Unit Price ($)']
            unit_cost = row['Unit Cost ($)']
            
            # Calculate total volume and revenue
            total_volume = sum([demand_df.loc[idx, month] for month in self.months])
            total_revenue = total_volume * unit_price
            total_cogs = total_volume * unit_cost
            gross_profit = total_revenue - total_cogs
            gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Add some financial errors (3% chance of negative margins)
            if random.random() < 0.03:
                gross_margin = random.uniform(-10, 5)
                gross_profit = total_revenue * (gross_margin / 100)
            
            financial_data.loc[idx, 'Total Volume'] = total_volume
            financial_data.loc[idx, 'Total Revenue ($)'] = round(total_revenue, 2)
            financial_data.loc[idx, 'Total COGS ($)'] = round(total_cogs, 2)
            financial_data.loc[idx, 'Gross Profit ($)'] = round(gross_profit, 2)
            financial_data.loc[idx, 'Gross Margin (%)'] = round(gross_margin, 2)
        
        return financial_data
    
    def _generate_logistics_plan(self, sku_df):
        """Generate logistics data"""
        
        logistics_data = sku_df.copy()
        
        for idx, row in logistics_data.iterrows():
            category = row['Category']
            lead_time = row['Lead Time (days)']
            
            # Generate logistics metrics
            reorder_point = int(lead_time * random.uniform(0.8, 1.2))
            max_inventory = int(lead_time * random.uniform(2, 3))
            min_order_quantity = int(lead_time * random.uniform(0.5, 1.0))
            
            # Add some logistics errors (2% chance)
            if random.random() < 0.02:
                reorder_point = 0  # Missing data
            if random.random() < 0.02:
                max_inventory = 0  # Missing data
            
            logistics_data.loc[idx, 'Reorder Point'] = reorder_point
            logistics_data.loc[idx, 'Max Inventory'] = max_inventory
            logistics_data.loc[idx, 'Min Order Quantity'] = min_order_quantity
        
        return logistics_data
    
    def _generate_manufacturing_data(self):
        """Generate manufacturing capacity data"""
        
        manufacturing_data = []
        
        for plant_name, plant_config in self.manufacturing_facilities.items():
            for category in plant_config['categories']:
                cat_config = self.categories[category]
                
                manufacturing_data.append({
                    'Plant': plant_name,
                    'Category': category,
                    'Location': plant_config['location'],
                    'Total Capacity': plant_config['total_capacity'],
                    'Category Capacity': cat_config['manufacturing_capacity'],
                    'Utilization Rate': plant_config['utilization_rate'],
                    'Available Capacity': plant_config['total_capacity'] * plant_config['utilization_rate'],
                    'Maintenance Schedule': plant_config['maintenance_schedule'],
                    'Lead Time (days)': random.randint(*cat_config['lead_time'])
                })
        
        return pd.DataFrame(manufacturing_data)
    
    def _generate_promotional_data(self):
        """Generate promotional campaign data"""
        
        promotional_data = []
        
        for campaign_name, campaign in self.promotional_campaigns.items():
            promotional_data.append({
                'Campaign Name': campaign_name,
                'Start Date': campaign['start_date'],
                'End Date': campaign['end_date'],
                'Categories': ', '.join(campaign['categories']),
                'Demand Uplift': campaign['demand_uplift'],
                'Budget': campaign['budget'],
                'Regions': ', '.join(campaign['regions']),
                'Status': 'Active' if datetime.now().strftime('%Y-%m-%d') <= campaign['end_date'] else 'Completed'
            })
        
        return pd.DataFrame(promotional_data)
    
    def _generate_regional_data(self):
        """Generate regional market data"""
        
        regional_data = []
        
        for region_name, region_config in self.regions.items():
            regional_data.append({
                'Region': region_name,
                'Countries': ', '.join(region_config['countries']),
                'Demand Multiplier': region_config['demand_multiplier'],
                'Service Level': region_config['service_level'],
                'Market Size': random.randint(1000000, 5000000),
                'Growth Rate': random.uniform(0.05, 0.15),
                'Competition Level': random.choice(['Low', 'Medium', 'High']),
                'Distribution Channels': random.randint(3, 8)
            })
        
        return pd.DataFrame(regional_data)

if __name__ == "__main__":
    generator = EnhancedSOPDatasetGenerator()
    output_file = generator.create_enhanced_sop_dataset()
    print(f"\n🎉 Enhanced S&OP dataset ready: {output_file}") 