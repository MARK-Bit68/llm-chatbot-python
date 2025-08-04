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
    analytical_indicators = ["what if", "if we", "impact", "analysis", "compare", "versus", "vs", "negative", "positive", "top", "bottom", "average", "sum", "count", "profit", "revenue", "cost"]
    
    has_analytical_indicator = any(indicator in question_lower for indicator in analytical_indicators)
    
    if has_analytical_indicator:
        print(f"🔍 DEBUG: Detected analytical query, falling back to LLM")
        # Let LLM handle analytical queries
        pass
    else:
        # Detect all valid SKU IDs in the question (e.g., SKU001, SKU002, ...)
        sku_pattern = r"SKU\d{3,}"  # Matches SKU followed by at least 3 digits
        sku_ids = re.findall(sku_pattern, question.upper())
        sku_ids = list(set(sku_ids))  # Remove duplicates
        print(f"🔍 DEBUG: Detected SKU IDs: {sku_ids}")
        print(f"🔍 DEBUG: Question in uppercase: '{question.upper()}'")
        print(f"🔍 DEBUG: Regex pattern: {sku_pattern}")

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
    
    # Check for "all SKUs" type queries using intelligent detection
    question_lower = question.lower()
    
    # More specific "all SKUs" patterns to avoid catching analytical queries
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
    Format query results as a markdown table (with all columns) for both all-SKU and single-SKU queries.
    Optionally, add a summary/insights section after the table, but never instead of the table.
    """
    if not results or count == 0:
        return "No results found."

    # Extract all unique keys from the results
    all_keys = set()
    for row in results:
        if isinstance(row, dict):
            all_keys.update(row.keys())
        elif hasattr(row, '_fields'):
            all_keys.update(row._fields)
    all_keys = list(all_keys)

    # Build the markdown table header
    header = "| " + " | ".join(all_keys) + " |"
    separator = "|" + "---|" * len(all_keys)

    # Build the table rows
    rows = []
    for row in results:
        if isinstance(row, dict):
            values = [str(row.get(k, "")) for k in all_keys]
        elif hasattr(row, '_fields'):
            values = [str(getattr(row, k, "")) for k in all_keys]
        else:
            values = [str(row)]
        rows.append("| " + " | ".join(values) + " |")

    table = "\n".join([header, separator] + rows)

    # Optionally, add a summary/insights section
    summary = f"\n\n**Total Results:** {count}"
    if count == 1:
        summary += "\n\n**Details for the requested SKU are shown above.**"
    elif count > 1:
        summary += "\n\n**Details for all matching SKUs are shown above.**"

    return f"{table}{summary}"

def enhanced_cypher_qa(question):
    print(f"🔍 DEBUG: ===== ENHANCED_CYPHER_QA CALLED =====")
    print(f"🔍 DEBUG: enhanced_cypher_qa() called with question: '{question}'")
    try:
        cypher_query = generate_dynamic_cypher_query(question)
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