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
    """Render a world-class dashboard with professional grid layout and KPI cards"""
    
    # Show loading state with user-friendly message
    with st.spinner("🔄 Loading your dashboard data from the database..."):
        st.info("📊 **Building your personalized dashboard** - This may take a moment while I fetch your latest data.")
        
        # Load data
        monthly_df, category_summary, financial_summary = get_dashboard_data()
    
    if monthly_df is None:
        st.error("Unable to load data from database. Please check your connection.")
        return
    
    # Data quality warnings
    if not monthly_df.empty:
        if monthly_df['supply'].sum() == 0:
            st.warning("⚠️ **Data Alert**: No supply data available. All supply values are zero.")
        if monthly_df['inventory'].sum() == 0:
            st.info("📦 **Note**: No inventory data available in current dataset.")
        if total_revenue == 0:
            st.info("💰 **Note**: Financial metrics not available in current dataset.")
    
    # Calculate key metrics for KPI cards
    total_revenue = financial_summary.get('revenue', 0)
    total_volume = financial_summary.get('forecasted_volume', 0)
    gross_profit = financial_summary.get('gross_profit', 0)
    cogs = financial_summary.get('cogs', 0)
    margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    avg_unit_price = (total_revenue / total_volume) if total_volume > 0 else 0
    
    # Calculate trend indicators with robust error handling
    demand_trend = 0
    try:
        if not monthly_df.empty and 'month' in monthly_df.columns and 'demand' in monthly_df.columns:
            # Get available months safely
            available_months = monthly_df['month'].unique()
            
            # Find recent and earlier months that exist in data
            recent_months = [m for m in ['may_2025', 'jun_2025'] if m in available_months]
            earlier_months = [m for m in ['jan_2024', 'feb_2024'] if m in available_months]
            
            if recent_months and earlier_months:
                recent_demand = monthly_df[monthly_df['month'].isin(recent_months)]['demand'].sum()
                earlier_demand = monthly_df[monthly_df['month'].isin(earlier_months)]['demand'].sum()
                
                if earlier_demand > 0:
                    demand_trend = ((recent_demand - earlier_demand) / earlier_demand * 100)
                else:
                    demand_trend = 0
    except Exception as e:
        print(f"Warning: Could not calculate demand trend: {e}")
        demand_trend = 0
    
    # Robust KPI Cards using native Streamlit components
    st.markdown("## 🎯 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"${total_revenue:,.0f}",
            delta=f"${gross_profit:,.0f} profit",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            label="📦 Total Volume",
            value=f"{total_volume:,.0f}",
            delta=f"${cogs:,.0f} COGS",
            delta_color="normal"
        )
    
    with col3:
        trend_delta = f"{demand_trend:+.1f}%" if demand_trend != 0 else "0.0%"
        st.metric(
            label="📊 Gross Margin",
            value=f"{margin_pct:.1f}%",
            delta=trend_delta,
            delta_color="normal" if demand_trend >= 0 else "inverse"
        )
    
    with col4:
        st.metric(
            label="💵 Avg Unit Price",
            value=f"${avg_unit_price:.2f}",
            delta="per unit",
            delta_color="normal"
        )
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Professional Grid Layout (3x3 Grid)
    st.markdown("## 📊 Analytics Dashboard")
    
    # Row 1: Charts
    col1, col2, col3 = st.columns([2, 1, 1])
    
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
        
        # Robust chart styling that works reliably
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
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🥧 Category Distribution")
        
        # Robust category pie chart
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
    
    with col3:
        st.subheader("📊 Quick Metrics")
        
        # Robust category metrics display
        if not category_summary.empty:
            # Find best and worst performers safely
            try:
                if 'gross_profit' in category_summary.columns:
                    best_category = category_summary.loc[category_summary['gross_profit'].idxmax()]
                    worst_category = category_summary.loc[category_summary['gross_profit'].idxmin()]
                    
                    st.metric(
                        label="🏆 Best Performer",
                        value=best_category['category'],
                        delta=f"${best_category.get('gross_profit', 0):,.0f} profit"
                    )
                    
                    st.metric(
                        label="⚠️ Needs Attention",
                        value=worst_category['category'],
                        delta=f"${worst_category.get('gross_profit', 0):,.0f} profit"
                    )
            except Exception as e:
                st.info("Category analysis not available")
        
        # Data quality indicator
        if not monthly_df.empty:
            try:
                unique_skus = len(monthly_df['sku_id'].unique())
                unique_months = len(monthly_df['month'].unique())
                
                st.metric(
                    label="📦 Data Coverage",
                    value=f"{unique_skus} SKUs",
                    delta=f"{unique_months} months"
                )
            except Exception as e:
                st.info("Data coverage not available")
    
    # Second row - SKU and Country Performance
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    # Second row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 SKU Performance")
        
        # Robust SKU performance chart with improved grouping
        try:
            sku_performance = monthly_df.groupby(['sku_id', 'name', 'category']).agg({
                'demand': 'sum',
                'supply': 'sum'
            }).reset_index()
            
            sku_performance['gap'] = sku_performance['supply'] - sku_performance['demand']
            
            # Ensure both demand and supply are shown in chart
            fig_sku = px.bar(
                sku_performance,
                x='name',
                y=['demand', 'supply'],
                title="SKU Demand vs Supply",
                barmode='group',
                color_discrete_map={'demand': '#1f77b4', 'supply': '#ff7f0e'}
            )
            fig_sku.update_layout(height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig_sku, use_container_width=True)
            
            # Add insights about supply gaps
            if sku_performance['supply'].sum() == 0:
                st.info("💡 **Insight**: All SKUs show demand but no supply. Consider loading supply data.")
            elif sku_performance['gap'].min() < 0:
                st.info("💡 **Insight**: Some SKUs have supply gaps (demand > supply).")
                
        except Exception as e:
            st.error(f"Could not generate SKU chart: {e}")
    
    with col2:
        st.subheader("🌍 Geographic Performance")
        
        # Robust country performance chart with improved grouping
        try:
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
                barmode='group',
                color_discrete_map={'demand': '#1f77b4', 'supply': '#ff7f0e'}
            )
            fig_country.update_layout(height=400)
            st.plotly_chart(fig_country, use_container_width=True)
            
            # Add geographic insights
            if country_performance['supply'].sum() == 0:
                st.info("🌍 **Geographic Insight**: No supply data available by country.")
            else:
                best_country = country_performance.loc[country_performance['demand'].idxmax()]
                st.info(f"🌍 **Geographic Insight**: {best_country['country']} has highest demand.")
                
        except Exception as e:
            st.error(f"Could not generate country chart: {e}")
    
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
    """Generate a dynamic, user-friendly response with real data and LLM-generated insights"""
    
    # Initial friendly message
    initial_message = """
# 📊 FMCG S&OP Dashboard

🔍 **Connecting to your database and analyzing your data...**

I'm fetching your real FMCG S&OP data from the Neo4j graph database to generate personalized insights for you.
"""
    
    try:
        # Get real data with user feedback
        monthly_df, category_summary, financial_summary = get_dashboard_data()
        
        if monthly_df is None or monthly_df.empty:
            return """
# 📊 FMCG S&OP Dashboard

⚠️ **Limited Data Available**

I connected to your database but found limited data to analyze. Here's what I can show you:

## 📈 Available Insights
- **Data Status**: Connected to Neo4j database successfully
- **SKU Count**: Limited SKU data available
- **Recommendation**: Consider loading more data for comprehensive analysis

The dashboard below shows what data is currently accessible in your database:
"""
        
        # Calculate real metrics from actual data
        total_revenue = financial_summary.get('revenue', 0)
        total_volume = financial_summary.get('forecasted_volume', 0)
        gross_profit = financial_summary.get('gross_profit', 0)
        cogs = financial_summary.get('cogs', 0)
        
        # Calculate margin safely
        margin_pct = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        avg_unit_price = (total_revenue / total_volume) if total_volume > 0 else 0
        
        # Generate dynamic insights based on real data
        insights = []
        
        # Revenue insights
        if total_revenue > 0:
            insights.append(f"💰 **Total Revenue**: ${total_revenue:,.0f} with ${gross_profit:,.0f} gross profit")
            insights.append(f"📊 **Gross Margin**: {margin_pct:.1f}% average")
        else:
            insights.append("📊 **Revenue Data**: Financial metrics not available in current dataset")
        
        # Volume insights
        if total_volume > 0:
            insights.append(f"📦 **Total Volume**: {total_volume:,.0f} forecasted units")
            insights.append(f"💵 **Average Unit Price**: ${avg_unit_price:.2f} per unit")
        else:
            insights.append("📦 **Volume Data**: Demand/supply metrics not available in current dataset")
        
        # Category insights from real data
        if not category_summary.empty and 'revenue' in category_summary.columns and 'gross_profit' in category_summary.columns:
            # Find best performing category
            best_category = category_summary.loc[category_summary['gross_profit'].idxmax()] if len(category_summary) > 0 else None
            worst_category = category_summary.loc[category_summary['gross_profit'].idxmin()] if len(category_summary) > 0 else None
            
            if best_category is not None and best_category['gross_profit'] > 0:
                best_margin = (best_category['gross_profit'] / best_category['revenue'] * 100) if best_category['revenue'] > 0 else 0
                insights.append(f"⭐ **Star Performer**: {best_category['category']} ({best_margin:.0f}% margin, ${best_category['revenue']:,.0f} revenue)")
            
            if worst_category is not None and worst_category['gross_profit'] < 0:
                insights.append(f"⚠️ **Needs Attention**: {worst_category['category']} (negative margins detected)")
        
        # Data quality insights
        if not monthly_df.empty:
            unique_months = len(monthly_df['month'].unique())
            unique_skus = len(monthly_df['sku_id'].unique())
            insights.append(f"📅 **Data Coverage**: {unique_months} months, {unique_skus} SKUs analyzed")
            
            if unique_months > 12:
                insights.append("📈 **Seasonal Analysis**: Multi-year patterns visible in your data")
        
        # Format insights
        insights_text = "\n".join([f"{i+1}. {insight}" for i, insight in enumerate(insights)])
        
        # Generate user-friendly response
        if total_revenue > 0 and total_volume > 0:
            status = "✅ **Analysis Complete**"
            intro = "I've successfully analyzed your FMCG S&OP data and generated personalized insights:"
        else:
            status = "⚠️ **Partial Analysis**"
            intro = "I've analyzed your available data. Some metrics may be limited:"
        
        return f"""
# 📊 FMCG S&OP Dashboard

{status}

{intro}

## 🎯 Key Metrics
{insights_text}

## 💡 Recommendations
- **Explore the charts** below for detailed visual analysis
- **Filter by category** to focus on specific product lines
- **Check monthly trends** to identify seasonal patterns
- **Review supply-demand gaps** for operational insights

The interactive dashboard below shows your real data with detailed charts and metrics:
"""
        
    except Exception as e:
        # Graceful error handling with helpful message
        return f"""
# 📊 FMCG S&OP Dashboard

❌ **Analysis Encountered Issues**

I tried to analyze your data but encountered some technical difficulties. Here's what happened:

## 🔧 Technical Details
- **Database Connection**: Attempted to connect to Neo4j
- **Error Type**: {type(e).__name__}
- **Status**: Analysis incomplete

## 💡 What You Can Do
1. **Check your database connection** - Ensure Neo4j is running
2. **Verify your data** - Make sure SKU data is loaded
3. **Try again** - The dashboard may work on retry
4. **Contact support** - If issues persist

## 📊 Available Dashboard
The charts below will show whatever data is accessible. Some features may be limited.

*Note: This is a fallback response. Your data may still be available for visualization.*
""" 