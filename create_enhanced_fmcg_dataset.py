#!/usr/bin/env python3
"""
Enhanced FMCG S&OP Dataset Generator
Creates a comprehensive dataset with 500 SKUs, seasonal patterns, and realistic supply chain scenarios
"""

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

class FMCGDatasetGenerator:
    def __init__(self):
        self.categories = {
            'Dried Fruits': {'price_range': (12, 18), 'cost_ratio': 0.4, 'lead_time': (8, 15)},
            'Nuts': {'price_range': (8, 14), 'cost_ratio': 0.6, 'lead_time': (15, 25)},
            'Legumes': {'price_range': (6, 12), 'cost_ratio': 0.5, 'lead_time': (20, 30)},
            'Grains': {'price_range': (4, 8), 'cost_ratio': 0.7, 'lead_time': (10, 20)},
            'Spices': {'price_range': (15, 25), 'cost_ratio': 0.3, 'lead_time': (25, 40)}
        }
        
        self.countries = ['Country A', 'Country B', 'Country C']
        self.uom_options = ['Kg', 'Pack', 'Box', 'Unit']
        
        # Seasonal patterns by category
        self.seasonal_patterns = {
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
        
        self.months = [
            'Jan-2024', 'Feb-2024', 'Mar-2024', 'Apr-2024', 'May-2024', 'Jun-2024',
            'Jul-2024', 'Aug-2024', 'Sep-2024', 'Oct-2024', 'Nov-2024', 'Dec-2024',
            'Jan-2025', 'Feb-2025', 'Mar-2025', 'Apr-2025', 'May-2025', 'Jun-2025'
        ]
    
    def generate_sku_data(self, num_skus=500):
        """Generate comprehensive SKU data with realistic patterns"""
        
        # Create base SKU data
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
            
            # Assign other properties
            country = random.choice(self.countries)
            uom = random.choice(self.uom_options)
            
            sku_data.append({
                'SKU Code': sku_code,
                'Category': category,
                'Country': country,
                'UOM': uom,
                'Unit Price ($)': unit_price,
                'Unit Cost ($)': unit_cost,
                'Lead Time (days)': lead_time
            })
        
        return pd.DataFrame(sku_data)
    
    def generate_seasonal_demand(self, sku_df):
        """Generate seasonal demand data with realistic patterns"""
        
        demand_data = sku_df.copy()
        
        for idx, row in demand_data.iterrows():
            category = row['Category']
            pattern = self.seasonal_patterns[category]
            base_demand = pattern['base_demand']
            
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
                
                # Apply seasonal pattern
                if month_num in pattern['peak_months']:
                    multiplier = pattern['peak_multiplier']
                else:
                    multiplier = pattern['trough_multiplier']
                
                # Add some randomness
                demand = base_demand * multiplier * random.uniform(0.9, 1.1)
                
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
    
    def generate_supply_plan(self, demand_df):
        """Generate supply plan with realistic supply chain scenarios"""
        
        supply_data = demand_df.copy()
        
        for idx, row in supply_data.iterrows():
            category = row['Category']
            lead_time = row['Lead Time (days)']
            
            monthly_supply = []
            
            for i, month in enumerate(self.months):
                demand = row[month]
                
                # Base supply is demand plus some buffer
                base_supply = demand * random.uniform(0.9, 1.1)
                
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
    
    def generate_inventory_plan(self, demand_df, supply_df):
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
    
    def generate_financial_plan(self, sku_df, demand_df):
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
    
    def generate_logistics_plan(self, sku_df):
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
    
    def create_enhanced_dataset(self, output_file='Enhanced_FMCG_SOP_Dataset.xlsx'):
        """Create the complete enhanced dataset"""
        
        print("🚀 Creating enhanced FMCG S&OP dataset...")
        
        # Generate base SKU data
        print("📊 Generating SKU master data...")
        sku_df = self.generate_sku_data(500)
        
        # Generate demand plan with seasonal patterns
        print("📈 Generating demand plan with seasonal patterns...")
        demand_df = self.generate_seasonal_demand(sku_df)
        
        # Generate supply plan with realistic scenarios
        print("📦 Generating supply plan with supply chain scenarios...")
        supply_df = self.generate_supply_plan(demand_df)
        
        # Generate inventory plan
        print("🏪 Generating inventory plan...")
        inventory_df = self.generate_inventory_plan(demand_df, supply_df)
        
        # Generate financial plan
        print("💰 Generating financial metrics...")
        financial_df = self.generate_financial_plan(sku_df, demand_df)
        
        # Generate logistics plan
        print("🚚 Generating logistics data...")
        logistics_df = self.generate_logistics_plan(sku_df)
        
        # Create Excel file with multiple sheets
        print("💾 Saving to Excel file...")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            sku_df.to_excel(writer, sheet_name='Master Data', index=False)
            demand_df.to_excel(writer, sheet_name='Demand Plan', index=False)
            supply_df.to_excel(writer, sheet_name='Supply Plan', index=False)
            inventory_df.to_excel(writer, sheet_name='Inventory Plan', index=False)
            financial_df.to_excel(writer, sheet_name='Financial Plan', index=False)
            logistics_df.to_excel(writer, sheet_name='Logistics Plan', index=False)
        
        print(f"✅ Enhanced dataset created: {output_file}")
        
        # Print summary statistics
        print("\n📊 Dataset Summary:")
        print(f"- Total SKUs: {len(sku_df)}")
        print(f"- Categories: {sku_df['Category'].value_counts().to_dict()}")
        print(f"- Countries: {sku_df['Country'].value_counts().to_dict()}")
        print(f"- Time period: {self.months[0]} to {self.months[-1]}")
        
        # Calculate some key metrics
        total_demand = sum([demand_df[month].sum() for month in self.months])
        total_supply = sum([supply_df[month].sum() for month in self.months])
        avg_margin = financial_df['Gross Margin (%)'].mean()
        
        print(f"- Total demand: {total_demand:,.0f} units")
        print(f"- Total supply: {total_supply:,.0f} units")
        print(f"- Average margin: {avg_margin:.1f}%")
        
        return output_file

if __name__ == "__main__":
    generator = FMCGDatasetGenerator()
    output_file = generator.create_enhanced_dataset()
    print(f"\n🎉 Enhanced FMCG dataset ready: {output_file}") 