"""
Chart Generation Tools for Executive Dashboard
Creates rich visualizations for FMCG supply chain data
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import io
import base64
from datetime import datetime
import seaborn as sns

# Set style for professional charts
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def create_monthly_demand_chart(sku_data):
    """
    Create a comprehensive monthly demand analysis chart
    """
    # Extract monthly data
    months = ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
              'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
              'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']
    
    # Safely extract and convert data to float
    demand_data = []
    supply_data = []
    inventory_data = []
    
    for month in months:
        try:
            demand_val = sku_data.get(f'demand_{month}', 0)
            supply_val = sku_data.get(f'supply_{month}', 0)
            inventory_val = sku_data.get(f'inventory_{month}', 0)
            
            # Convert to float safely
            demand_data.append(float(demand_val) if demand_val is not None else 0.0)
            supply_data.append(float(supply_val) if supply_val is not None else 0.0)
            inventory_data.append(float(inventory_val) if inventory_val is not None else 0.0)
        except (ValueError, TypeError):
            demand_data.append(0.0)
            supply_data.append(0.0)
            inventory_data.append(0.0)
    
    # Create date range
    dates = pd.date_range(start='2024-01-01', periods=18, freq='ME')
    
    # Create the chart
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Top chart: Demand vs Supply
    ax1.plot(dates, demand_data, 'o-', linewidth=2, markersize=6, label='Demand', color='#2E86AB')
    ax1.plot(dates, supply_data, 's-', linewidth=2, markersize=6, label='Supply Plan', color='#A23B72')
    ax1.fill_between(dates, demand_data, supply_data, alpha=0.3, color='#F18F01')
    ax1.set_title(f'Monthly Demand vs Supply Analysis - {sku_data.get("sku_id", "SKU")}', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Units', fontsize=12)
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Bottom chart: Inventory Levels
    ax2.bar(dates, inventory_data, alpha=0.7, color='#C73E1D', label='Inventory Plan')
    ax2.axhline(y=sku_data.get('safety_stock', 0), color='red', linestyle='--', linewidth=2, label='Safety Stock')
    ax2.axhline(y=sku_data.get('initial_inventory', 0), color='green', linestyle='--', linewidth=2, label='Initial Inventory')
    ax2.set_title('Inventory Levels and Safety Stock', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Units', fontsize=12)
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    
    # Format x-axis
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax2.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64

def create_financial_metrics_chart(sku_data):
    """
    Create a financial performance dashboard chart
    """
    # Extract financial data
    unit_price = sku_data.get('unit_price', 0)
    unit_cost = sku_data.get('unit_cost', 0)
    revenue = sku_data.get('revenue', 0)
    cogs = sku_data.get('cogs', 0)
    gross_profit = sku_data.get('gross_profit', 0)
    distribution_cost = sku_data.get('distribution_cost', 0)
    
    # Create the chart
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Top left: Cost Structure Pie Chart
    cost_breakdown = [unit_cost, distribution_cost]
    cost_labels = ['Unit Cost', 'Distribution Cost']
    colors = ['#FF6B6B', '#4ECDC4']
    ax1.pie(cost_breakdown, labels=cost_labels, autopct='%1.1f%%', colors=colors, startangle=90)
    ax1.set_title('Cost Structure Breakdown', fontsize=12, fontweight='bold')
    
    # Top right: Revenue vs Cost Bar Chart
    categories = ['Revenue', 'COGS', 'Gross Profit']
    values = [revenue, cogs, gross_profit]
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax2.bar(categories, values, color=colors, alpha=0.7)
    ax2.set_title('Revenue vs Cost Analysis', fontsize=12, fontweight='bold')
    ax2.set_ylabel('USD', fontsize=10)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'${value:,.0f}', ha='center', va='bottom', fontsize=9)
    
    # Bottom left: Profit Margin Gauge
    margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
    ax3.pie([margin, 100-margin], labels=[f'{margin:.1f}%', ''], colors=['#4ECDC4', '#F7F7F7'], startangle=90)
    ax3.set_title('Gross Profit Margin', fontsize=12, fontweight='bold')
    
    # Bottom right: Unit Economics
    metrics = ['Unit Price', 'Unit Cost', 'Gross Profit/Unit']
    values = [unit_price, unit_cost, unit_price - unit_cost]
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax4.bar(metrics, values, color=colors, alpha=0.7)
    ax4.set_title('Unit Economics', fontsize=12, fontweight='bold')
    ax4.set_ylabel('USD per Unit', fontsize=10)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'${value:.2f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64

def create_inventory_analysis_chart(sku_data):
    """
    Create inventory analysis and forecasting chart
    """
    # Extract inventory data
    initial_inventory = sku_data.get('initial_inventory', 0)
    safety_stock = sku_data.get('safety_stock', 0)
    forecasted_volume = sku_data.get('forecasted_volume', 0)
    lead_time_days = sku_data.get('lead_time_days', 0)
    
    # Calculate average monthly demand
    months = ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
              'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
              'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']
    avg_monthly_demand = sum(sku_data.get(f'demand_{month}', 0) for month in months) / len(months)
    
    # Create the chart
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Left: Inventory Levels
    categories = ['Initial Inventory', 'Safety Stock', 'Avg Monthly Demand']
    values = [initial_inventory, safety_stock, avg_monthly_demand]
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax1.bar(categories, values, color=colors, alpha=0.7)
    ax1.set_title('Inventory Levels Analysis', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Units', fontsize=12)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{value:,.0f}', ha='center', va='bottom', fontsize=10)
    
    # Right: Supply Chain Metrics
    metrics = ['Lead Time (Days)', 'Forecasted Volume', 'Safety Stock Ratio']
    values = [lead_time_days, forecasted_volume/1000, safety_stock/avg_monthly_demand if avg_monthly_demand > 0 else 0]
    colors = ['#4ECDC4', '#FF6B6B', '#95E1D3']
    bars = ax2.bar(metrics, values, color=colors, alpha=0.7)
    ax2.set_title('Supply Chain Performance Metrics', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Days / K Units / Ratio', fontsize=12)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        if metrics[list(bars).index(bar)] == 'Forecasted Volume':
            label = f'{value:.1f}K'
        elif metrics[list(bars).index(bar)] == 'Safety Stock Ratio':
            label = f'{value:.2f}'
        else:
            label = f'{value:.0f}'
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                label, ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    # Convert to base64 for embedding
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
    img_buffer.seek(0)
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_base64

def generate_executive_charts(sku_data):
    """
    Generate all executive charts for a SKU
    """
    try:
        charts = {}
        
        # Generate monthly demand chart
        charts['monthly_demand'] = create_monthly_demand_chart(sku_data)
        
        # Generate financial metrics chart
        charts['financial_metrics'] = create_financial_metrics_chart(sku_data)
        
        # Generate inventory analysis chart
        charts['inventory_analysis'] = create_inventory_analysis_chart(sku_data)
        
        return charts
        
    except Exception as e:
        print(f"❌ DEBUG: Error generating charts: {e}")
        return {}

def embed_charts_in_response(response_text, charts):
    """
    Embed charts into the response text
    """
    if not charts:
        return response_text
    
    # Add chart section to response
    chart_section = "\n\n## 📊 Executive Visualizations\n\n"
    
    if 'monthly_demand' in charts:
        chart_section += f"### 📈 Monthly Demand & Supply Analysis\n"
        chart_section += f"![Monthly Demand Chart](data:image/png;base64,{charts['monthly_demand']})\n\n"
    
    if 'financial_metrics' in charts:
        chart_section += f"### 💰 Financial Performance Dashboard\n"
        chart_section += f"![Financial Metrics](data:image/png;base64,{charts['financial_metrics']})\n\n"
    
    if 'inventory_analysis' in charts:
        chart_section += f"### 📦 Inventory & Supply Chain Analysis\n"
        chart_section += f"![Inventory Analysis](data:image/png;base64,{charts['inventory_analysis']})\n\n"
    
    return response_text + chart_section 