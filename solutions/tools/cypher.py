import streamlit as st
from llm import get_llm
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
import re

def generate_dynamic_cypher_query(question, available_data=None):
    """
    Generate a dynamic Cypher query based on the user's question and available data.
    If the question contains one or more valid SKU IDs (e.g., SKU001), override the query to filter for those SKUs.
    Otherwise, use the LLM to generate the query as before.
    """
    print(f"🔍 DEBUG: generate_dynamic_cypher_query() called with question: '{question}'")

    # Check for analytical queries FIRST (before SKU detection)
    question_lower = question.lower()
    
    # Detect all valid SKU IDs in the question (e.g., SKU001, SKU002, ...)
    sku_pattern = r"SKU\d{3,}"  # Matches SKU followed by at least 3 digits
    sku_ids = re.findall(sku_pattern, question.upper())
    sku_ids = list(set(sku_ids))  # Remove duplicates
    print(f"🔍 DEBUG: Detected SKU IDs: {sku_ids}")
    print(f"🔍 DEBUG: Question in uppercase: '{question.upper()}'")
    print(f"🔍 DEBUG: Regex pattern: {sku_pattern}")

    # PRIORITY 1: If SKU is detected, handle it as a SKU query (not analytical)
    if len(sku_ids) >= 1:
        if len(sku_ids) == 1:
            # Single SKU query (case-insensitive)
            cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) = '{sku_ids[0].upper()}' RETURN sku.sku_id, sku.name, sku.plot"
            print(f"🔍 DEBUG: Overriding query for single SKU: {cypher_query}")
            return cypher_query
        elif len(sku_ids) > 1:
            # Multi-SKU query (case-insensitive)
            sku_list = ', '.join([f"'{sku.upper()}'" for sku in sku_ids])
            cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) IN [{sku_list}] RETURN sku.sku_id, sku.name, sku.plot"
            print(f"🔍 DEBUG: Overriding query for multiple SKUs: {cypher_query}")
            return cypher_query
    
    # PRIORITY 2: Check for "all SKUs" type queries
    simple_all_patterns = [
        "what skus are in the master data",
        "show me all skus",
        "list all skus", 
        "display all skus",
        "display every sku",
        "what skus do we have",
        "which skus do we have",
        "which skus are available",
        "show me all products",
        "list all products",
        "what products are in the master data"
    ]
    
    # Check for exact simple patterns first
    if any(pattern in question_lower for pattern in simple_all_patterns):
        # "All SKUs" query detected
        cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category ORDER BY sku.sku_id"
        print(f"🔍 DEBUG: Detected 'all SKUs' query, using simple query: {cypher_query}")
        return cypher_query
    
    # PRIORITY 3: Only then check for analytical queries (more specific patterns)
    analytical_indicators = [
        # True analytical/calculation terms
        "what if", "if we", "impact", "analysis", "compare", "versus", "vs", "negative", "positive", 
        "top", "bottom", "average", "sum", "count", "profit", "revenue", "cost", "added", "increased", 
        "decreased", "reduced", "more", "less",
        
        # Complex analytical scenarios
        "capacity planning", "resource planning", "mrp", "erp", "s&op", "sales and operations planning",
        "demand planning", "supply planning", "financial planning",
        "budget", "forecast accuracy", "bias", "seasonality", "trend", "volatility",
        "optimization", "efficiency", "productivity", "utilization", "bottleneck", "constraint",
        "scenario", "simulation", "what-if", "sensitivity", "risk", "mitigation", "contingency",
        "escalation", "escalate", "alert", "threshold", "kpi", "metric", "performance",
        "baseline", "target", "goal", "objective", "strategy", "tactical", "operational",
        "strategic", "tactical", "operational", "daily", "weekly", "monthly", "quarterly", "annual",
        "yearly", "period", "cycle", "season", "peak", "off-peak", "holiday", "promotion",
        "campaign", "marketing", "advertising", "discount", "pricing", "margin", "markup",
        "cost structure", "fixed cost", "variable cost", "direct cost", "indirect cost",
        "overhead", "allocation", "absorption", "standard cost", "actual cost", "variance",
        "efficiency variance", "price variance", "usage variance", "volume variance",
        "absorption variance", "capacity variance", "mix variance", "yield variance"
    ]
    
    has_analytical_indicator = any(indicator in question_lower for indicator in analytical_indicators)
    if has_analytical_indicator:
        print(f"🔍 DEBUG: Detected analytical query, falling back to LLM")
        # Let LLM handle analytical queries - return None to fall back to LLM generation
        return None
    
    print(f"🔍 DEBUG: No specific patterns detected, falling back to LLM query generation")

    # Otherwise, use the LLM to generate the query as before
    # Create a prompt for the LLM to generate Cypher queries
    cypher_generation_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Cypher query expert for Neo4j. Your task is to generate precise Cypher queries based on user questions.

IMPORTANT: The data structure is different than typical. SKU nodes have this structure:
- sku_id: The SKU identifier
- name: Product name  
- plot: A pipe-separated string containing all data (category, country, unit_price, unit_cost, etc.)
- data_type: Type of data
- plotEmbedding: Vector embedding (don't return this)

The plot field contains data like: "category: Legumes | country: Country B | unit_price: 10.9 | unit_cost: 5.24 | lead_time_days: 22 | ..."

To extract data from the plot field, use Cypher string functions with proper syntax:
- To get category: split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- To get unit_price: split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as unit_price
- To get unit_cost: split(split(sku.plot, 'unit_cost: ')[1], ' | ')[0] as unit_cost
- To get country: split(split(sku.plot, 'country: ')[1], ' | ')[0] as country

Example queries:
- ALL SKUs: MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10
- Specific SKU: MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- SKU category: MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- Price analysis: MATCH (sku:SKU) WITH sku, split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price RETURN sku.sku_id, sku.name, price WHERE price IS NOT NULL
- Category count: MATCH (sku:SKU) RETURN split(split(sku.plot, 'category: ')[1], ' | ')[0] as category, count(*) as count

Analytical Query Examples:
- Top selling product:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'revenue: ')[1], ' | ')[0]) AS revenue RETURN sku.sku_id, sku.name, revenue ORDER BY revenue DESC LIMIT 1
- SKUs with negative gross profit:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'gross_profit: ')[1], ' | ')[0]) AS gp WHERE gp < 0 RETURN sku.sku_id, sku.name, gp
- Average lead time by category:
  MATCH (sku:SKU) WITH split(split(sku.plot, 'category: ')[1], ' | ')[0] AS category, toFloat(split(split(sku.plot, 'lead_time_days: ')[1], ' | ')[0]) AS lead_time RETURN category, avg(lead_time) AS avg_lead_time
- Warehouse with highest inventory value:
  MATCH (sku:SKU) WITH split(split(sku.plot, 'warehouse: ')[1], ' | ')[0] AS warehouse, toFloat(split(sku.plot, 'unit_price: ')[1], ' | ')[0]) AS price, toFloat(split(split(sku.plot, 'initial_inventory: ')[1], ' | ')[0]) AS inv RETURN warehouse, sum(price * inv) AS inventory_value ORDER BY inventory_value DESC LIMIT 1
- SKUs with forecasted volume above 10,000:
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'forecasted_volume: ')[1], ' | ')[0]) AS fv WHERE fv > 10000 RETURN sku.sku_id, sku.name, fv

IMPORTANT RULES:
- DO NOT return plotEmbedding as it contains large data
- Use proper nested split syntax: split(split(sku.plot, 'field: ')[1], ' | ')[0]
- Handle cases where data might not exist in the plot
- Generate ONLY the Cypher query, no explanations
- Make queries specific to the user's question

CRITICAL: When the user asks about a SPECIFIC SKU (e.g., "Tell me about SKU001", "What is the category of SKU001?"), use:
MATCH (sku:SKU {{sku_id: 'SKU001'}}) RETURN sku.sku_id, sku.name, sku.plot

When the user asks about ALL SKUs (e.g., "What SKUs are in the Master Data?", "Show me all SKUs"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10

When the user asks about countries (e.g., "Which countries are our products from?"), use:
MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'country: ')[1], ' | ')[0] as country

IMPORTANT: Look for specific SKU IDs in the question (like SKU001, SKU002, etc.) and use the specific SKU query pattern.

Generate the Cypher query:"""),
        ("human", "{question}")
    ])
    
    try:
        # Generate the query using the LLM
        chain = cypher_generation_prompt | get_llm()
        response = chain.invoke({
            "question": question
        })
        
        # Extract the query from the response
        query = response.content.strip()
        
        # Clean up the query (remove markdown formatting if present)
        if query.startswith("```cypher"):
            query = query.replace("```cypher", "").replace("```", "").strip()
        elif query.startswith("```"):
            query = query.replace("```", "").strip()
        
        # Validate the query has basic Cypher structure
        if not query.upper().startswith("MATCH"):
            # Generate a safe fallback query
            query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 10"
        
        # Ensure we don't return large fields
        if "plotEmbedding" in query:
            # Remove plotEmbedding from the query
            query = query.replace("plotEmbedding", "").replace("sku.plotEmbedding", "")
        
        print(f"🔍 DEBUG: Final query: {query}")
        return query
    except Exception as e:
        print(f"❌ DEBUG: Error generating Cypher query: {e}")
        # Return a safe fallback query
        fallback_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 5"
        print(f"🔍 DEBUG: Using error fallback query: {fallback_query}")
        return fallback_query

def execute_dynamic_query(question, available_data=None):
    """
    Execute a dynamically generated Cypher query and return structured results
    """
    try:
        # Generate the query
        query = generate_dynamic_cypher_query(question, available_data)
        
        if not query:
            return {"error": "Failed to generate query"}
        
        print(f"Generated Cypher query: {query}")
        
        # Execute the query
        results = get_graph().query(query)
        
        return {
            "query": query,
            "results": results,
            "count": len(results) if results else 0
        }
    except Exception as e:
        return {"error": f"Query execution failed: {str(e)}"}

def analyze_and_format_results(question, results, count):
    """
    Format query results with executive-level analysis and insights.
    """
    if not results or count == 0:
        return "No results found."

    # Parse the data for executive insights
    parsed_data = []
    for row in results:
        if isinstance(row, dict):
            parsed_row = {}
            for key, value in row.items():
                if key == 'sku.plot' and value:
                    # Parse the complex plot data
                    plot_data = parse_sku_plot_data(value)
                    parsed_row.update(plot_data)
                else:
                    parsed_row[key] = value
            parsed_data.append(parsed_row)
        else:
            parsed_data.append(row)

    # Generate executive-level response
    if count == 1:
        return generate_executive_single_sku_response(question, parsed_data[0])
    else:
        return generate_executive_multi_sku_response(question, parsed_data)

def parse_sku_plot_data(plot_string):
    """
    Parse the complex plot data string into structured data
    """
    data = {}
    if not plot_string:
        return data
    
    # Split by | and parse key-value pairs
    parts = plot_string.split(' | ')
    for part in parts:
        if ':' in part:
            key, value = part.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Handle special cases
            if key in ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
                      'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
                      'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']:
                try:
                    data[f'demand_{key}'] = int(value)
                except:
                    data[f'demand_{key}'] = value
            elif key in ['unit_price', 'unit_cost', 'distribution_cost']:
                try:
                    data[key] = float(value)
                except:
                    data[key] = value
            elif key in ['initial_inventory', 'safety_stock', 'forecasted_volume', 'revenue', 'cogs', 'gross_profit']:
                try:
                    data[key] = float(value)
                except:
                    data[key] = value
            else:
                data[key] = value
    
    return data

def generate_executive_single_sku_response(question, sku_data):
    """
    Generate executive-level response for single SKU queries with rich visualizations
    """
    # Import chart generation
    try:
        from solutions.tools.charts import generate_executive_charts, embed_charts_in_response
        charts = generate_executive_charts(sku_data)
    except Exception as e:
        print(f"❌ DEBUG: Chart generation failed: {e}")
        charts = {}
    
    response = f"# 📊 Executive Summary: {sku_data.get('sku_id', 'SKU')}\n\n"
    
    # Basic Information
    response += f"## 🏷️ Product Overview\n"
    response += f"- **Product Name:** {sku_data.get('name', 'N/A')}\n"
    response += f"- **Category:** {sku_data.get('category', 'N/A')}\n"
    response += f"- **Country of Origin:** {sku_data.get('country', 'N/A')}\n"
    response += f"- **Unit of Measure:** {sku_data.get('uom', 'N/A')}\n"
    response += f"- **Warehouse:** {sku_data.get('warehouse', 'N/A')}\n\n"
    
    # Financial Metrics
    response += f"## 💰 Financial Performance\n"
    unit_price = sku_data.get('unit_price', 0)
    unit_cost = sku_data.get('unit_cost', 0)
    revenue = sku_data.get('revenue', 0)
    cogs = sku_data.get('cogs', 0)
    gross_profit = sku_data.get('gross_profit', 0)
    distribution_cost = sku_data.get('distribution_cost', 0)
    
    response += f"- **Unit Price:** ${unit_price:.2f}\n"
    response += f"- **Unit Cost:** ${unit_cost:.2f}\n"
    response += f"- **Gross Profit per Unit:** ${unit_price - unit_cost:.2f}\n"
    
    # Calculate margin safely
    margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
    response += f"- **Gross Profit Margin:** {margin:.1f}%\n"
    
    response += f"- **Total Revenue:** ${revenue:,.2f}\n"
    response += f"- **Cost of Goods Sold:** ${cogs:,.2f}\n"
    response += f"- **Gross Profit:** ${gross_profit:,.2f}\n"
    response += f"- **Distribution Cost:** ${distribution_cost:.2f}\n\n"
    
    # Inventory Management
    response += f"## 📦 Inventory Management\n"
    response += f"- **Initial Inventory:** {sku_data.get('initial_inventory', 0):,} units\n"
    response += f"- **Safety Stock:** {sku_data.get('safety_stock', 0):,} units\n"
    response += f"- **Forecasted Volume:** {sku_data.get('forecasted_volume', 0):,} units\n"
    response += f"- **Lead Time:** {sku_data.get('lead_time_days', 0)} days\n\n"
    
    # Monthly Demand Analysis
    response += f"## 📈 Monthly Demand Analysis (2024-2025)\n"
    months = ['jan_2024', 'feb_2024', 'mar_2024', 'apr_2024', 'may_2024', 'jun_2024',
              'jul_2024', 'aug_2024', 'sep_2024', 'oct_2024', 'nov_2024', 'dec_2024',
              'jan_2025', 'feb_2025', 'mar_2025', 'apr_2025', 'may_2025', 'jun_2025']
    
    response += "| Month | Demand | Supply Plan | Inventory Plan |\n"
    response += "|------|--------|-------------|----------------|\n"
    
    for month in months:
        demand = sku_data.get(f'demand_{month}', 0)
        supply = sku_data.get(f'supply_{month}', 0)
        inventory = sku_data.get(f'inventory_{month}', 0)
        month_name = month.replace('_', ' ').title()
        response += f"| {month_name} | {demand:,} | {supply:,} | {inventory:,} |\n"
    
    response += "\n"
    
    # Strategic Insights
    response += f"## 🎯 Strategic Insights\n"
    
    # Calculate key metrics
    avg_demand = sum(sku_data.get(f'demand_{month}', 0) for month in months) / len(months)
    avg_inventory = sum(sku_data.get(f'inventory_{month}', 0) for month in months) / len(months)
    total_revenue = sku_data.get('revenue', 0)
    total_profit = sku_data.get('gross_profit', 0)
    forecasted_volume = sku_data.get('forecasted_volume', 1)
    
    response += f"- **Average Monthly Demand:** {avg_demand:,.0f} units\n"
    response += f"- **Average Monthly Inventory:** {avg_inventory:,.0f} units\n"
    response += f"- **Inventory Turnover Ratio:** {avg_demand / avg_inventory if avg_inventory > 0 else 0:.2f}\n"
    response += f"- **Revenue per Unit:** ${total_revenue / forecasted_volume:.2f}\n"
    response += f"- **Profit per Unit:** ${total_profit / forecasted_volume:.2f}\n\n"
    
    # Recommendations
    response += f"## 💡 Executive Recommendations\n"
    
    if avg_inventory > avg_demand * 1.5:
        ratio = avg_inventory/avg_demand if avg_demand > 0 else 0
        response += f"- ⚠️ **Inventory Optimization Needed:** Current inventory levels are {ratio:.1f}x higher than demand\n"
    elif avg_inventory < avg_demand * 0.8:
        ratio = avg_demand/avg_inventory if avg_inventory > 0 else 0
        response += f"- ⚠️ **Stockout Risk:** Inventory levels are {ratio:.1f}x lower than demand\n"
    else:
        response += f"- ✅ **Optimal Inventory Levels:** Inventory is well-balanced with demand\n"
    
    if sku_data.get('gross_profit', 0) > 0:
        unit_price = sku_data.get('unit_price', 0)
        unit_cost = sku_data.get('unit_cost', 0)
        margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
        response += f"- ✅ **Profitable Product:** Strong gross profit margin of {margin:.1f}%\n"
    else:
        response += f"- ❌ **Loss-Making Product:** Negative gross profit margin\n"
    
    response += f"- 📊 **Market Position:** {sku_data.get('category', 'N/A')} category with {sku_data.get('country', 'N/A')} sourcing\n"
    
    # Embed charts if available
    if charts:
        response = embed_charts_in_response(response, charts)
    
    return response

def generate_executive_multi_sku_response(question, sku_data_list):
    """
    Generate executive-level response for multiple SKU queries
    """
    response = f"# 📊 Executive Dashboard: {len(sku_data_list)} SKUs\n\n"
    
    # Summary Statistics
    total_revenue = sum(sku.get('revenue', 0) for sku in sku_data_list)
    total_profit = sum(sku.get('gross_profit', 0) for sku in sku_data_list)
    total_volume = sum(sku.get('forecasted_volume', 0) for sku in sku_data_list)
    
    response += f"## 📈 Portfolio Overview\n"
    response += f"- **Total Revenue:** ${total_revenue:,.2f}\n"
    response += f"- **Total Gross Profit:** ${total_profit:,.2f}\n"
    response += f"- **Total Forecasted Volume:** {total_volume:,.0f} units\n"
    avg_margin = (total_profit/total_revenue*100) if total_revenue > 0 else 0
    response += f"- **Average Profit Margin:** {avg_margin:.1f}%\n\n"
    
    # Category Analysis
    categories = {}
    for sku in sku_data_list:
        category = sku.get('category', 'Unknown')
        if category not in categories:
            categories[category] = {'revenue': 0, 'profit': 0, 'volume': 0, 'count': 0}
        categories[category]['revenue'] += sku.get('revenue', 0)
        categories[category]['profit'] += sku.get('gross_profit', 0)
        categories[category]['volume'] += sku.get('forecasted_volume', 0)
        categories[category]['count'] += 1
    
    response += f"## 🏷️ Category Performance\n"
    response += "| Category | SKUs | Revenue | Profit | Volume | Margin |\n"
    response += "|----------|------|---------|--------|--------|--------|\n"
    
    for category, data in categories.items():
        margin = (data['profit'] / data['revenue'] * 100) if data['revenue'] > 0 else 0
        response += f"| {category} | {data['count']} | ${data['revenue']:,.0f} | ${data['profit']:,.0f} | {data['volume']:,.0f} | {margin:.1f}% |\n"
    
    response += "\n"
    
    # Top Performers
    response += f"## 🏆 Top Performers\n"
    sorted_by_revenue = sorted(sku_data_list, key=lambda x: x.get('revenue', 0), reverse=True)
    
    response += "| Rank | SKU | Revenue | Profit | Margin | Category |\n"
    response += "|------|-----|---------|--------|--------|----------|\n"
    
    for i, sku in enumerate(sorted_by_revenue[:5], 1):
        revenue = sku.get('revenue', 0)
        profit = sku.get('gross_profit', 0)
        margin = (profit / revenue * 100) if revenue > 0 else 0
        response += f"| {i} | {sku.get('sku_id', 'N/A')} | ${revenue:,.0f} | ${profit:,.0f} | {margin:.1f}% | {sku.get('category', 'N/A')} |\n"
    
    response += "\n"
    
    # Strategic Insights
    response += f"## 🎯 Strategic Insights\n"
    
    # Profitability analysis
    profitable_skus = [sku for sku in sku_data_list if sku.get('gross_profit', 0) > 0]
    loss_making_skus = [sku for sku in sku_data_list if sku.get('gross_profit', 0) <= 0]
    
    response += f"- **Profitable SKUs:** {len(profitable_skus)} ({len(profitable_skus)/len(sku_data_list)*100:.1f}% of portfolio)\n"
    response += f"- **Loss-Making SKUs:** {len(loss_making_skus)} ({len(loss_making_skus)/len(sku_data_list)*100:.1f}% of portfolio)\n"
    
    # Category insights
    best_category = max(categories.items(), key=lambda x: x[1]['profit']) if categories else None
    if best_category:
        response += f"- **Best Performing Category:** {best_category[0]} (${best_category[1]['profit']:,.0f} profit)\n"
    
    response += f"- **Portfolio Health:** {'Strong' if len(profitable_skus) > len(loss_making_skus) else 'Needs Attention'}\n"
    
    return response

def enhanced_cypher_qa(question):
    print(f"🔍 DEBUG: ===== ENHANCED_CYPHER_QA CALLED =====")
    print(f"🔍 DEBUG: enhanced_cypher_qa() called with question: '{question}'")
    try:
        cypher_query = generate_dynamic_cypher_query(question)
        
        # If analytical query detected, return a message to let LLM handle it
        if cypher_query is None:
            print(f"🔍 DEBUG: Analytical query detected, returning message for LLM handling")
            return "ANALYTICAL_QUERY_DETECTED: This is an analytical query that requires LLM reasoning. Please use the LLM to perform calculations and analysis based on the data."
            
        print(f"🔍 DEBUG: Final Cypher query to execute: {cypher_query}")
        
        graph = get_graph()
        if graph is None:
            print("❌ DEBUG: Graph instance is None")
            return "Database connection not available."
        
        result = graph.query(cypher_query)
        print(f"🔍 DEBUG: Query returned {len(result)} results")
        
        formatted_response = analyze_and_format_results(question, result, len(result))
        return formatted_response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in enhanced_cypher_qa: {e}")
        return f"Error processing your request: {str(e)}"

# Keep the original simple cypher_search for backward compatibility
def cypher_search(query):
    """Simple keyword-based search (legacy function)"""
    if not get_graph():
        return []
    
    try:
        # Simple keyword-based search
        cypher_query = """
        MATCH (sku:SKU)
        WHERE toLower(sku.name) CONTAINS toLower($query) 
           OR toLower(sku.plot) CONTAINS toLower($query)
        RETURN sku.name, sku.plot, sku.sku_id
        LIMIT 10
        """
        
        results = get_graph().query(cypher_query, {'query': query})
        return results
    except Exception as e:
        print(f"Cypher search error: {e}")
        return []

def cypher_qa(question):
    """
    Legacy function for backward compatibility - now uses enhanced version
    """
    return enhanced_cypher_qa(question)