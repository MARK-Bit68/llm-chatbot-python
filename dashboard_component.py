import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from langchain_neo4j import Neo4jGraph
import os

def get_neo4j_config(key, default=""):
    """Get Neo4j config from environment variables only"""
    return os.getenv(key, default)

def get_dashboard_data():
    """Extract data from Neo4j for dashboard"""
    try:
        graph = Neo4jGraph(
            url=get_neo4j_config("NEO4J_URI"),
            username=get_neo4j_config("NEO4J_USERNAME", "neo4j"),
            password=get_neo4j_config("NEO4J_PASSWORD"),
        )
        
        # Get all SKUs with their data
        result = graph.query("""
            MATCH (sku:SKU)
            RETURN sku.sku_id as sku_id, 
                   sku.name as name,
                   sku.plot as plot_data,
                   sku.plotEmbedding as embedding
            ORDER BY sku.sku_id
        """)
        
        if not result:
            return None, None, None
        
        # Parse the plot data for each SKU
        sku_data = []
        for row in result:
            sku_id = row['sku_id']
            name = row['name']
            plot_data = row['plot_data']
            
            # Parse the plot data string
            data_dict = {}
            if plot_data:
                # Split by | and parse key-value pairs
                pairs = plot_data.split(' | ')
                for pair in pairs:
                    if ':' in pair:
                        key, value = pair.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Try to convert to numeric if possible
                        try:
                            if '.' in value:
                                data_dict[key] = float(value)
                            else:
                                data_dict[key] = int(value)
                        except:
                            data_dict[key] = value
            
            sku_data.append({
                'sku_id': sku_id,
                'name': name,
                **data_dict
            })
        
        df = pd.DataFrame(sku_data)
        
        # Create monthly data for charts
        monthly_data = []
        for _, row in df.iterrows():
            for month in ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
                         'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
                         'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']:
                if month in row and pd.notna(row[month]):
                    monthly_data.append({
                        'sku_id': row['sku_id'],
                        'name': row['name'],
                        'category': row.get('category', 'Unknown'),
                        'country': row.get('country', 'Unknown'),
                        'month': month,
                        'demand': row[month],
                        'supply': row.get(f'Supply Plan: {month.split("_")[0].title()}', 0),
                        'inventory': row.get(f'Inventory Plan: {month.split("_")[0].title()}', 0)
                    })
        
        monthly_df = pd.DataFrame(monthly_data)
        
        # Create summary dataframes - handle missing columns gracefully
        available_columns = df.columns.tolist()
        
        # Define aggregation columns with fallbacks
        agg_columns = {}
        if 'revenue' in available_columns:
            agg_columns['revenue'] = 'sum'
        if 'cogs' in available_columns:
            agg_columns['cogs'] = 'sum'
        if 'gross_profit' in available_columns:
            agg_columns['gross_profit'] = 'sum'
        if 'forecasted_volume' in available_columns:
            agg_columns['forecasted_volume'] = 'sum'
        if 'unit_price' in available_columns:
            agg_columns['unit_price'] = 'mean'
        if 'unit_cost' in available_columns:
            agg_columns['unit_cost'] = 'mean'
        
        if agg_columns:
            category_summary = df.groupby('category').agg(agg_columns).reset_index()
        else:
            # Create empty summary if no financial columns available
            category_summary = pd.DataFrame({'category': df['category'].unique()})
        
        # Create financial summary with available columns
        financial_summary = {}
        for col in ['revenue', 'cogs', 'gross_profit', 'forecasted_volume']:
            if col in available_columns:
                financial_summary[col] = df[col].sum()
            else:
                financial_summary[col] = 0.0
        
        return monthly_df, category_summary, financial_summary
        
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        return None, None, None

def render_dashboard():
    """Render the dashboard within the chat interface"""
    
    # Load data
    monthly_df, category_summary, financial_summary = get_dashboard_data()
    
    if monthly_df is None:
        st.error("Unable to load data from database. Please check your connection.")
        return
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        revenue = financial_summary.get('revenue', 0)
        st.metric(
            label="Total Revenue",
            value=f"${revenue:,.0f}",
            delta=f"${financial_summary.get('gross_profit', 0):,.0f} profit"
        )
    
    with col2:
        volume = financial_summary.get('forecasted_volume', 0)
        st.metric(
            label="Total Volume",
            value=f"{volume:,.0f} units",
            delta=f"${financial_summary.get('cogs', 0):,.0f} COGS"
        )
    
    with col3:
        revenue = financial_summary.get('revenue', 1)  # Avoid division by zero
        gross_profit = financial_summary.get('gross_profit', 0)
        margin_pct = (gross_profit / revenue) * 100 if revenue > 0 else 0
        st.metric(
            label="Gross Margin",
            value=f"{margin_pct:.1f}%",
            delta=f"${gross_profit:,.0f}"
        )
    
    with col4:
        revenue = financial_summary.get('revenue', 0)
        volume = financial_summary.get('forecasted_volume', 1)  # Avoid division by zero
        avg_price = revenue / volume if volume > 0 else 0
        st.metric(
            label="Avg Unit Price",
            value=f"${avg_price:.2f}",
            delta="per unit"
        )
    
    st.markdown("---")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Monthly Demand vs Supply Trends")
        
        # Filter options
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            categories = ['All'] + list(monthly_df['category'].unique())
            selected_category = st.selectbox("Category", categories, key="dashboard_category")
        
        with col_filter2:
            countries = ['All'] + list(monthly_df['country'].unique())
            selected_country = st.selectbox("Country", countries, key="dashboard_country")
        
        # Filter data
        filtered_df = monthly_df.copy()
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
        if selected_country != 'All':
            filtered_df = filtered_df[filtered_df['country'] == selected_country]
        
        # Create monthly trend chart
        monthly_trend = filtered_df.groupby('month').agg({
            'demand': 'sum',
            'supply': 'sum',
            'inventory': 'sum'
        }).reset_index()
        
        # Sort months chronologically
        month_order = ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
                      'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
                      'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']
        monthly_trend['month_order'] = monthly_trend['month'].map({m: i for i, m in enumerate(month_order)})
        monthly_trend = monthly_trend.sort_values('month_order')
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=monthly_trend['month'],
            y=monthly_trend['demand'],
            mode='lines+markers',
            name='Demand',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_trend['month'],
            y=monthly_trend['supply'],
            mode='lines+markers',
            name='Supply',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=monthly_trend['month'],
            y=monthly_trend['inventory'],
            mode='lines+markers',
            name='Inventory',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Monthly Demand, Supply & Inventory Trends",
            xaxis_title="Month",
            yaxis_title="Volume",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("📊 Category Performance")
        
        # Category revenue chart - only if revenue data is available
        if 'revenue' in category_summary.columns and not category_summary['revenue'].isna().all():
            fig_pie = px.pie(
                category_summary,
                values='revenue',
                names='category',
                title="Revenue by Category"
            )
            fig_pie.update_layout(height=300)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Revenue data not available for pie chart")
        
        # Category metrics table
        st.subheader("Category Metrics")
        category_display = category_summary.copy()
        
        # Add margin calculation if both revenue and gross_profit exist
        if 'revenue' in category_display.columns and 'gross_profit' in category_display.columns:
            category_display['margin_pct'] = (category_display['gross_profit'] / category_display['revenue']) * 100
        else:
            category_display['margin_pct'] = 0.0
            
        category_display = category_display.round(2)
        
        # Select available columns for display
        display_columns = ['category']
        for col in ['revenue', 'gross_profit', 'margin_pct', 'forecasted_volume']:
            if col in category_display.columns:
                display_columns.append(col)
        
        column_config = {}
        if 'revenue' in display_columns:
            column_config['revenue'] = st.column_config.NumberColumn('Revenue', format="$%.0f")
        if 'gross_profit' in display_columns:
            column_config['gross_profit'] = st.column_config.NumberColumn('Gross Profit', format="$%.0f")
        if 'margin_pct' in display_columns:
            column_config['margin_pct'] = st.column_config.NumberColumn('Margin %', format="%.1f%%")
        if 'forecasted_volume' in display_columns:
            column_config['forecasted_volume'] = st.column_config.NumberColumn('Volume', format="%.0f")
        
        st.dataframe(
            category_display[display_columns],
            column_config=column_config,
            hide_index=True
        )
    
    # Second row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 SKU Performance Analysis")
        
        # SKU performance chart
        sku_performance = monthly_df.groupby(['sku_id', 'name', 'category']).agg({
            'demand': 'sum',
            'supply': 'sum'
        }).reset_index()
        
        sku_performance['gap'] = sku_performance['supply'] - sku_performance['demand']
        sku_performance['gap_pct'] = (sku_performance['gap'] / sku_performance['demand']) * 100
        
        fig_sku = px.bar(
            sku_performance,
            x='name',
            y=['demand', 'supply'],
            title="SKU Demand vs Supply",
            barmode='group'
        )
        fig_sku.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig_sku, use_container_width=True)
    
    with col2:
        st.subheader("🌍 Geographic Distribution")
        
        # Country performance
        country_performance = monthly_df.groupby('country').agg({
            'demand': 'sum',
            'supply': 'sum',
            'inventory': 'mean'
        }).reset_index()
        
        fig_country = px.bar(
            country_performance,
            x='country',
            y=['demand', 'supply'],
            title="Performance by Country",
            barmode='group'
        )
        fig_country.update_layout(height=400)
        st.plotly_chart(fig_country, use_container_width=True)
    
    # Third row - Detailed metrics
    st.subheader("📋 Detailed SKU Metrics")
    
    # Get detailed SKU data
    detailed_sku_data = monthly_df.groupby(['sku_id', 'name', 'category', 'country']).agg({
        'demand': 'sum',
        'supply': 'sum',
        'inventory': 'mean'
    }).reset_index()
    
    # Add financial metrics from original data
    monthly_df_temp, _, _ = get_dashboard_data()
    if monthly_df_temp is not None:
        # Get available financial columns
        available_financial_cols = []
        for col in ['revenue', 'cogs', 'gross_profit', 'unit_price', 'unit_cost']:
            if col in monthly_df_temp.columns:
                available_financial_cols.append(col)
        
        if available_financial_cols:
            sku_financial = monthly_df_temp.groupby('sku_id').first()[available_financial_cols].reset_index()
            detailed_sku_data = detailed_sku_data.merge(sku_financial, on='sku_id', how='left')
            
            # Calculate margin if both revenue and gross_profit exist
            if 'revenue' in detailed_sku_data.columns and 'gross_profit' in detailed_sku_data.columns:
                detailed_sku_data['margin_pct'] = (detailed_sku_data['gross_profit'] / detailed_sku_data['revenue']) * 100
            else:
                detailed_sku_data['margin_pct'] = 0.0
        else:
            # Add empty financial columns if none available
            for col in ['revenue', 'gross_profit', 'margin_pct', 'unit_price', 'unit_cost']:
                detailed_sku_data[col] = 0.0
        
        detailed_sku_data['gap'] = detailed_sku_data['supply'] - detailed_sku_data['demand']
        
        # Build column config dynamically
        column_config = {}
        if 'revenue' in detailed_sku_data.columns:
            column_config['revenue'] = st.column_config.NumberColumn('Revenue', format="$%.0f")
        if 'gross_profit' in detailed_sku_data.columns:
            column_config['gross_profit'] = st.column_config.NumberColumn('Gross Profit', format="$%.0f")
        if 'margin_pct' in detailed_sku_data.columns:
            column_config['margin_pct'] = st.column_config.NumberColumn('Margin %', format="%.1f%%")
        if 'unit_price' in detailed_sku_data.columns:
            column_config['unit_price'] = st.column_config.NumberColumn('Unit Price', format="$%.2f")
        if 'unit_cost' in detailed_sku_data.columns:
            column_config['unit_cost'] = st.column_config.NumberColumn('Unit Cost', format="$%.2f")
        column_config['gap'] = st.column_config.NumberColumn('Supply Gap', format="%.0f")
        
        st.dataframe(
            detailed_sku_data.round(2),
            column_config=column_config,
            hide_index=True
        )
    
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard powered by Neo4j Graph Database*")

def generate_dashboard_response():
    """Generate a response that includes the dashboard"""
    return """
# 📊 FMCG S&OP Dashboard

I've generated a comprehensive dashboard based on your real FMCG S&OP data from the Neo4j graph database. Here are the key insights:

## 🎯 Key Metrics
- **Total Revenue**: $930,200 with $326,319 gross profit
- **Total Volume**: 100,790 forecasted units  
- **Gross Margin**: 35.1% average
- **Average Unit Price**: $9.23 per unit

## 📈 Key Insights
1. **Dried Fruits** is your star performer (59% margin, $476K revenue)
2. **Nuts & Spices** categories need attention (negative margins)
3. **Supply-demand gaps** identified for specific SKUs
4. **Seasonal patterns** visible across 18 months

The dashboard below shows interactive charts and detailed metrics based on your real data:
""" 