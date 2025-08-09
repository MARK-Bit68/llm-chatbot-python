import streamlit as st
from llm import get_llm
from monitoring import record_event, timeit
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
import re

def generate_dynamic_cypher_query(question, available_data=None):
    """
    Generate a dynamic Cypher query based on the user's question using LLM classification.
    """
    print(f"🔍 DEBUG: generate_dynamic_cypher_query() called with question: '{question}'")

    # Use LLM to classify the query type instead of hard-coded patterns
    query_classification = classify_query_with_llm(question)
    print(f"🔍 DEBUG: LLM classified query as: {query_classification}")
    record_event("cypher.query.classified", {"class": query_classification})

    # Handle based on LLM classification
    if query_classification == "SKU_SPECIFIC":
        # Detect SKU IDs in the question
        sku_pattern = r"SKU\d{3,}"
        sku_ids = re.findall(sku_pattern, question.upper())
        sku_ids = list(set(sku_ids))
        
        if len(sku_ids) >= 1:
            if len(sku_ids) == 1:
                cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) = '{sku_ids[0].upper()}' RETURN sku.sku_id, sku.name, sku.plot"
                print(f"🔍 DEBUG: Single SKU query: {cypher_query}")
                record_event("cypher.query.generated", {"type": "single_sku"})
                return cypher_query
            else:
                sku_list = ', '.join([f"'{sku.upper()}'" for sku in sku_ids])
                cypher_query = f"MATCH (sku:SKU) WHERE toUpper(sku.sku_id) IN [{sku_list}] RETURN sku.sku_id, sku.name, sku.plot"
                print(f"🔍 DEBUG: Multi-SKU query: {cypher_query}")
                record_event("cypher.query.generated", {"type": "multi_sku", "count": len(sku_ids)})
                return cypher_query
    
    elif query_classification == "ALL_SKUS":
        # Use LLM to determine if financial data is needed
        financial_classification = classify_financial_data_needed(question)
        if financial_classification == "FINANCIAL_DATA_NEEDED":
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: All SKUs with financial data query: {cypher_query}")
        else:
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: All SKUs query: {cypher_query}")
        record_event("cypher.query.generated", {"type": "all_skus"})
        return cypher_query
    
    elif query_classification == "DATA_QUERY":
        # Use LLM to determine if financial data is needed
        financial_classification = classify_financial_data_needed(question)
        if financial_classification == "FINANCIAL_DATA_NEEDED":
            # For financial data queries, return full plot data
            cypher_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot ORDER BY sku.sku_id"
            print(f"🔍 DEBUG: Data query with financial data: {cypher_query}")
            return cypher_query
        else:
            # Generate Cypher query using LLM for non-financial data queries
            q = generate_cypher_with_llm(question)
            record_event("cypher.query.generated", {"type": "data_query"})
            return q
    
    elif query_classification == "ANALYTICAL":
        print(f"🔍 DEBUG: Analytical query detected, falling back to LLM")
        record_event("cypher.query.analytical", {"note": "handled by LLM"})
        return None
    
    else:
        # Default to LLM generation
        q = generate_cypher_with_llm(question)
        record_event("cypher.query.generated", {"type": "default"})
        return q

def classify_query_with_llm(question):
    """
    Use LLM to classify the query type instead of hard-coded patterns.
    """
    try:
        from llm import get_llm
        llm = get_llm()
        
        prompt = f"""
        Classify this FMCG supply chain query into one of these categories:
        
        - SKU_SPECIFIC: Queries about specific SKU IDs (e.g., "Tell me about SKU001", "What is SKU002's category?")
        - ALL_SKUS: Queries asking for all SKUs or general data (e.g., "Show me all SKUs", "List all products")
        - DATA_QUERY: Queries that can be answered with direct data lookup (e.g., "Which SKUs have negative profit?", "Show me profitable SKUs")
        - ANALYTICAL: Queries requiring complex calculations or what-if scenarios (e.g., "What if we increase prices by 10%?", "How would demand change if...")
        
        User Query: "{question}"
        
        Return only the category name (SKU_SPECIFIC, ALL_SKUS, DATA_QUERY, or ANALYTICAL):
        """
        
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            result_text = result.content
        elif hasattr(result, 'strip'):
            result_text = result.strip()
        else:
            result_text = str(result)
        
        # Clean up the response
        category = result_text.strip().upper()
        valid_categories = ["SKU_SPECIFIC", "ALL_SKUS", "DATA_QUERY", "ANALYTICAL"]
        
        if category in valid_categories:
            return category
        else:
            return "DATA_QUERY"  # Default to data query
            
    except Exception as e:
        print(f"🔍 DEBUG: Query classification failed: {e}")
        return "DATA_QUERY"  # Default to data query

def classify_financial_data_needed(question):
    """
    Use LLM to determine if financial data is needed for the query.
    """
    try:
        from llm import get_llm
        llm = get_llm()
        
        prompt = f"""
        Determine if this FMCG supply chain query requires financial data (revenue, profit, cost, margin, etc.).
        
        Return ONLY one of these classifications:
        - FINANCIAL_DATA_NEEDED: Query explicitly asks for financial metrics, money, revenue, profit, cost, margin, pricing, financial analysis, supply chain gaps, performance analysis, or profitability assessment
        - GENERAL_DATA_ONLY: Query asks for general information like categories, names, basic data without financial focus
        
        Examples:
        - "Show me all SKUs with revenue" → FINANCIAL_DATA_NEEDED
        - "List all products with profit data" → FINANCIAL_DATA_NEEDED  
        - "Show me all SKUs" → GENERAL_DATA_ONLY
        - "What categories do we have?" → GENERAL_DATA_ONLY
        - "Which SKUs are profitable?" → FINANCIAL_DATA_NEEDED
        - "Show me supply chain gaps" → FINANCIAL_DATA_NEEDED
        - "Analyze supply chain performance" → FINANCIAL_DATA_NEEDED
        - "Which products are loss-making?" → FINANCIAL_DATA_NEEDED
        
        User Query: "{question}"
        
        Return only the classification (FINANCIAL_DATA_NEEDED or GENERAL_DATA_ONLY):
        """
        
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            result_text = result.content
        elif hasattr(result, 'strip'):
            result_text = result.strip()
        else:
            result_text = str(result)
        
        # Clean up the response
        classification = result_text.strip().upper()
        valid_classifications = ["FINANCIAL_DATA_NEEDED", "GENERAL_DATA_ONLY"]
        
        if classification in valid_classifications:
            return classification
        else:
            return "GENERAL_DATA_ONLY"  # Default to general data
            
    except Exception as e:
        print(f"🔍 DEBUG: Financial classification failed: {e}")
        return "GENERAL_DATA_ONLY"  # Default to general data
    
def generate_cypher_with_llm(question):
    """
    Generate Cypher query using LLM instead of hard-coded patterns.
    """
    print(f"🔍 DEBUG: Generating Cypher query with LLM for: '{question}'")

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
  MATCH (sku:SKU) WITH sku, toFloat(split(split(sku.plot, 'total_revenue: ')[1], ' | ')[0]) AS revenue RETURN sku.sku_id, sku.name, revenue ORDER BY revenue DESC LIMIT 1
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

When the user asks about ALL SKUs with financial data (e.g., "Show me all SKUs with revenue", "List all products with profit data"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10

When the user asks about ALL SKUs without financial data (e.g., "What SKUs are in the Master Data?", "Show me all SKUs"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 10

When the user asks about countries (e.g., "Which countries are our products from?"), use:
MATCH (sku:SKU) RETURN DISTINCT split(split(sku.plot, 'country: ')[1], ' | ')[0] as country

IMPORTANT: Look for specific SKU IDs in the question (like SKU001, SKU002, etc.) and use the specific SKU query pattern.

Generate the Cypher query:"""),
        ("human", "{question}")
    ])
    
    try:
        # Generate the query using the LLM
        chain = cypher_generation_prompt | get_llm()
        with timeit("llm.generate_cypher", {"preview": question[:120]}):
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
        record_event("cypher.query.generated.llm", {"length": len(query)})
        return query
    except Exception as e:
        print(f"❌ DEBUG: Error generating Cypher query: {e}")
        # Return a safe fallback query
        fallback_query = "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 5"
        print(f"🔍 DEBUG: Using error fallback query: {fallback_query}")
        record_event("cypher.query.fallback", {})
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
        with timeit("neo4j.query", {"query_preview": query[:140]}):
            results = get_graph().query(query)
        
        payload = {
            "query": query,
            "results": results,
            "count": len(results) if results else 0
        }
        record_event("cypher.query.results", {"count": payload["count"]})
        return payload
    except Exception as e:
        record_event("cypher.query.error", {"message": str(e)})
        return {"error": f"Query execution failed: {str(e)}"}

def analyze_and_format_results(question, results, count):
    """
    Format query results with executive-level analysis and insights.
    """
    if not results or count == 0:
        return "No results found."

    # Check if this is a non-SKU query (like country, category, etc.)
    if results and isinstance(results[0], dict):
        first_row = results[0]
        # If the query doesn't return SKU fields, handle it specially
        if 'sku.sku_id' not in first_row and 'sku_id' not in first_row:
            return generate_simple_list_response(question, results)

    # Parse the data for executive insights
    parsed_data = []
    for row in results:
        if isinstance(row, dict):
            parsed_row = {}
            for key, value in row.items():
                if key == 'sku.plot' and value:
                    # Parse the complex plot data
                    sku_id = row.get('sku.sku_id') or row.get('sku_id')
                    plot_data = parse_sku_plot_data(value, sku_id)
                    parsed_row.update(plot_data)
                elif key == 'sku.sku_id':
                    # Ensure sku_id is set even when plot data is not available
                    parsed_row['sku_id'] = value
                elif key == 'sku.name':
                    # Ensure name is set
                    parsed_row['name'] = value
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

def parse_sku_plot_data(plot_string, sku_id=None):
    """
    Parse the complex plot data string into structured data
    """
    data = {}
    if not plot_string:
        return data
    
    # Set the sku_id if provided
    if sku_id:
        data['sku_id'] = sku_id
    
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
            elif key in ['initial_inventory', 'safety_stock', 'forecasted_volume', 'total_revenue', 'total_cogs', 'gross_profit', 'revenue', 'cogs']:
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
    charts = {}
    try:
        from solutions.tools.charts import generate_executive_charts, embed_charts_in_response
        charts = generate_executive_charts(sku_data)
    except ImportError:
        print("🔍 DEBUG: Chart generation not available (matplotlib not installed)")
    except Exception as e:
        print(f"❌ DEBUG: Chart generation failed: {e}")
    
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
    # Use correct field names with fallbacks and ensure numeric types
    revenue = float(sku_data.get('total_revenue', sku_data.get('revenue', 0)) or 0)
    cogs = float(sku_data.get('total_cogs', sku_data.get('cogs', 0)) or 0)
    gross_profit = float(sku_data.get('gross_profit', 0) or 0)
    distribution_cost = float(sku_data.get('distribution_cost', 0) or 0)
    
    response += f"- **Unit Price:** ${unit_price:.2f}\n"
    response += f"- **Unit Cost:** ${unit_cost:.2f}\n"
    response += f"- **Gross Profit per Unit:** ${unit_price - unit_cost:.2f}\n"
    
    # Calculate margin safely
    margin = ((unit_price - unit_cost) / unit_price * 100) if unit_price > 0 else 0
    response += f"- **Gross Profit Margin:** {margin:.1f}%\n"
    
    response += f"- **Total Revenue:** ${revenue:,.2f}\n"
    response += f"- **Cost of Goods Sold:** ${cogs:,.2f}\n"
    response += f"- **Gross Profit:** ${gross_profit:,.2f}\n"
    response += f"- **Distribution Cost:** ${distribution_cost:,.2f}\n\n"
    
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
    avg_demand = sum(float(sku_data.get(f'demand_{month}', 0) or 0) for month in months) / len(months)
    avg_inventory = sum(float(sku_data.get(f'inventory_{month}', 0) or 0) for month in months) / len(months)
    total_revenue = float(sku_data.get('total_revenue', sku_data.get('revenue', 0)) or 0)
    total_profit = float(sku_data.get('gross_profit', 0) or 0)
    forecasted_volume = float(sku_data.get('forecasted_volume', 1) or 1)
    
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
    
    # Filter out corrupted records and use correct field names
    valid_skus = [sku for sku in sku_data_list if sku.get('sku_id') and sku.get('sku_id') != 'None']
    
    # Summary Statistics
    total_revenue = sum(float(sku.get('total_revenue', sku.get('revenue', 0)) or 0) for sku in valid_skus)
    total_profit = sum(float(sku.get('gross_profit', 0) or 0) for sku in valid_skus)
    total_volume = sum(float(sku.get('forecasted_volume', 0) or 0) for sku in valid_skus)
    
    response += f"## 📈 Portfolio Overview\n"
    response += f"- **Total Revenue:** ${total_revenue:,.2f}\n"
    response += f"- **Total Gross Profit:** ${total_profit:,.2f}\n"
    response += f"- **Total Forecasted Volume:** {total_volume:,.0f} units\n"
    avg_margin = (total_profit/total_revenue*100) if total_revenue > 0 else 0
    response += f"- **Average Profit Margin:** {avg_margin:.1f}%\n\n"
    
    # Category Analysis
    categories = {}
    for sku in valid_skus:
        category = sku.get('category', 'Unknown')
        if category not in categories:
            categories[category] = {'revenue': 0, 'profit': 0, 'volume': 0, 'count': 0}
        categories[category]['revenue'] += float(sku.get('total_revenue', sku.get('revenue', 0)) or 0)
        categories[category]['profit'] += float(sku.get('gross_profit', 0) or 0)
        categories[category]['volume'] += float(sku.get('forecasted_volume', 0) or 0)
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
    sorted_by_revenue = sorted(valid_skus, key=lambda x: float(x.get('total_revenue', x.get('revenue', 0)) or 0), reverse=True)
    
    response += "| Rank | SKU | Revenue | Profit | Margin | Category |\n"
    response += "|------|-----|---------|--------|--------|----------|\n"
    
    for i, sku in enumerate(sorted_by_revenue[:5], 1):
        revenue = float(sku.get('total_revenue', sku.get('revenue', 0)) or 0)
        profit = float(sku.get('gross_profit', 0) or 0)
        margin = (profit / revenue * 100) if revenue > 0 else 0
        response += f"| {i} | {sku.get('sku_id', 'N/A')} | ${revenue:,.0f} | ${profit:,.0f} | {margin:.1f}% | {sku.get('category', 'N/A')} |\n"
    
    response += "\n"
    
    # Strategic Insights
    response += f"## 🎯 Strategic Insights\n"
    
    # Profitability analysis
    profitable_skus = [sku for sku in valid_skus if float(sku.get('gross_profit', 0) or 0) > 0]
    loss_making_skus = [sku for sku in valid_skus if float(sku.get('gross_profit', 0) or 0) <= 0]
    
    valid_count = len(valid_skus)
    if valid_count > 0:
        response += f"- **Profitable SKUs:** {len(profitable_skus)} ({len(profitable_skus)/valid_count*100:.1f}% of portfolio)\n"
        response += f"- **Loss-Making SKUs:** {len(loss_making_skus)} ({len(loss_making_skus)/valid_count*100:.1f}% of portfolio)\n"
    else:
        response += f"- **No valid SKUs found**\n"
    
    # Category insights
    best_category = max(categories.items(), key=lambda x: x[1]['profit']) if categories else None
    if best_category:
        response += f"- **Best Performing Category:** {best_category[0]} (${best_category[1]['profit']:,.0f} profit)\n"
    
    response += f"- **Portfolio Health:** {'Strong' if len(profitable_skus) > len(loss_making_skus) else 'Needs Attention'}\n"
    
    return response

def generate_simple_list_response(question, results):
    """
    Generate a simple response for non-SKU queries (like country, category lists)
    """
    if not results:
        return "No results found."
    
    # Extract the main field from the results
    if isinstance(results[0], dict):
        # Get the first non-None field
        first_row = results[0]
        main_field = None
        main_values = []
        
        for key, value in first_row.items():
            if value is not None and value != '':
                main_field = key
                break
        
        if main_field:
            # Extract all values for this field
            for row in results:
                if isinstance(row, dict) and row.get(main_field):
                    main_values.append(row[main_field])
            
            # Remove duplicates and None values
            main_values = list(set([v for v in main_values if v is not None]))
            
            if main_values:
                response = f"# 📊 {question.title()}\n\n"
                response += f"Found **{len(main_values)}** unique {main_field.replace('_', ' ').title()}:\n\n"
                
                for i, value in enumerate(main_values, 1):
                    response += f"{i}. **{value}**\n"
                
                return response
    
    # Fallback for unexpected data structure
    return f"# 📊 Query Results\n\nFound **{len(results)}** results for your query."

def enhanced_cypher_qa(question):
    print(f"🔍 DEBUG: ===== ENHANCED_CYPHER_QA CALLED =====")
    print(f"🔍 DEBUG: enhanced_cypher_qa() called with question: '{question}'")
    try:
        cypher_query = generate_dynamic_cypher_query(question)
        
        # If analytical query detected, return a user-friendly message
        if cypher_query is None:
            print(f"🔍 DEBUG: Analytical query detected, returning message for LLM handling")
            return "I understand you're looking for analytical insights. Let me analyze the available data to provide you with a comprehensive response."
            
        print(f"🔍 DEBUG: Final Cypher query to execute: {cypher_query}")
        
        graph = get_graph()
        if graph is None:
            print("❌ DEBUG: Graph instance is None")
            return "Database connection not available."
        
        with timeit("neo4j.query", {"query_preview": cypher_query[:140]}):
            result = graph.query(cypher_query)
        print(f"🔍 DEBUG: Query returned {len(result)} results")
        record_event("cypher.query.results", {"count": len(result)})
        
        formatted_response = analyze_and_format_results(question, result, len(result))
        return formatted_response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in enhanced_cypher_qa: {e}")
        record_event("cypher.qa.error", {"message": str(e)})
        return "I'm having trouble accessing the data right now. Please try again or rephrase your question."

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