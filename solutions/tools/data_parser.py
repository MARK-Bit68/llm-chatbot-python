import re
import json
from typing import Dict, List, Tuple

def parse_financial_data(plot_text: str) -> Dict[str, float]:
    """Parse financial data from plot text"""
    financial_data = {}
    
    # Extract unit_price
    unit_price_match = re.search(r'unit_price: ([^|]+)', plot_text)
    if unit_price_match:
        try:
            financial_data['unit_price'] = float(unit_price_match.group(1).strip())
        except ValueError:
            pass
    
    # Extract unit_cost
    unit_cost_match = re.search(r'unit_cost: ([^|]+)', plot_text)
    if unit_cost_match:
        try:
            financial_data['unit_cost'] = float(unit_cost_match.group(1).strip())
        except ValueError:
            pass
    
    # Extract total_revenue (correct field name)
    revenue_match = re.search(r'total_revenue: ([^|]+)', plot_text)
    if revenue_match:
        try:
            financial_data['total_revenue'] = float(revenue_match.group(1).strip())
            # Also set legacy field name for backward compatibility
            financial_data['revenue'] = float(revenue_match.group(1).strip())
        except ValueError:
            pass
    
    # Extract total_cogs (correct field name)
    cogs_match = re.search(r'total_cogs: ([^|]+)', plot_text)
    if cogs_match:
        try:
            financial_data['total_cogs'] = float(cogs_match.group(1).strip())
            # Also set legacy field name for backward compatibility
            financial_data['cogs'] = float(cogs_match.group(1).strip())
        except ValueError:
            pass
    
    # Extract gross_profit
    gross_profit_match = re.search(r'gross_profit: ([^|]+)', plot_text)
    if gross_profit_match:
        try:
            financial_data['gross_profit'] = float(gross_profit_match.group(1).strip())
        except ValueError:
            pass
    
    return financial_data

def parse_demand_data(plot_text: str) -> Dict[str, int]:
    """Parse monthly demand data from plot text"""
    demand_data = {}
    
    # Find all monthly demand entries - look for the first value after month_year:
    monthly_pattern = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)_\d{4}: (\d+)'
    matches = re.findall(monthly_pattern, plot_text)
    
    for month, value in matches:
        try:
            # Extract the demand value (first number after the month)
            demand_value = int(value)
            demand_data[f"{month}_2024"] = demand_value
        except ValueError:
            pass
    
    return demand_data

def calculate_average_demand(demand_data: Dict[str, int]) -> float:
    """Calculate average monthly demand"""
    if not demand_data:
        return 0.0
    
    total_demand = sum(demand_data.values())
    return total_demand / len(demand_data)

def analyze_cost_impact(current_unit_cost: float, current_avg_demand: float, demand_multiplier: float) -> Dict[str, float]:
    """Analyze cost impact of demand changes"""
    
    new_demand = current_avg_demand * demand_multiplier
    
    # Apply economies of scale logic
    conservative_reduction = 0.05  # 5%
    aggressive_reduction = 0.15    # 15%
    
    conservative_cost = current_unit_cost * (1 - conservative_reduction)
    aggressive_cost = current_unit_cost * (1 - aggressive_reduction)
    
    return {
        'current_unit_cost': current_unit_cost,
        'current_avg_demand': current_avg_demand,
        'new_demand': new_demand,
        'conservative_cost': conservative_cost,
        'aggressive_cost': aggressive_cost,
        'cost_range': (aggressive_cost, conservative_cost)
    }

def parse_sku_data(plot_text: str, demand_multiplier: float = 1.0) -> Dict[str, any]:
    """Main function to parse SKU data and analyze cost impact"""
    
    # Parse financial data
    financial_data = parse_financial_data(plot_text)
    
    # Parse demand data
    demand_data = parse_demand_data(plot_text)
    
    # Calculate average demand
    avg_demand = calculate_average_demand(demand_data)
    
    # Analyze cost impact if unit cost is available
    cost_analysis = {}
    if 'unit_cost' in financial_data:
        cost_analysis = analyze_cost_impact(
            financial_data['unit_cost'], 
            avg_demand, 
            demand_multiplier
        )
    
    return {
        'financial_data': financial_data,
        'demand_data': demand_data,
        'avg_monthly_demand': avg_demand,
        'cost_analysis': cost_analysis
    } 