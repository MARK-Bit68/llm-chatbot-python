import streamlit as st
from llm import get_llm
from graph import get_graph_instance
from langchain_core.prompts import ChatPromptTemplate

def generate_dynamic_cypher_query(question, available_data=None):
    """
    Generate a dynamic Cypher query based on the user's question and available data
    """
    
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
- Specific SKU: MATCH (sku:SKU {sku_id: 'SKU001'}) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- SKU category: MATCH (sku:SKU {sku_id: 'SKU001'}) RETURN sku.sku_id, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category
- Price analysis: MATCH (sku:SKU) WITH sku, split(split(sku.plot, 'unit_price: ')[1], ' | ')[0] as price RETURN sku.sku_id, sku.name, price WHERE price IS NOT NULL
- Category count: MATCH (sku:SKU) RETURN split(split(sku.plot, 'category: ')[1], ' | ')[0] as category, count(*) as count

IMPORTANT RULES:
- DO NOT return plotEmbedding as it contains large data
- Use proper nested split syntax: split(split(sku.plot, 'field: ')[1], ' | ')[0]
- Handle cases where data might not exist in the plot
- Generate ONLY the Cypher query, no explanations
- Make queries specific to the user's question

CRITICAL: When the user asks about a SPECIFIC SKU (e.g., "What is the category of SKU001?"), use:
MATCH (sku:SKU {sku_id: 'SKU001'}) RETURN sku.sku_id, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category

When the user asks about ALL SKUs (e.g., "What SKUs are in the Master Data?"), use:
MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10

Generate the Cypher query:"""),
        ("human", "{question}")
    ])
    
    try:
        # Generate the query using the LLM
        chain = cypher_generation_prompt | get_llm()
        response = chain.invoke({
            "question": question,
            "available_data": available_data or "No specific context provided"
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
        
        return query
    except Exception as e:
        print(f"Error generating Cypher query: {e}")
        # Return a safe fallback query
        return "MATCH (sku:SKU) RETURN sku.sku_id, sku.name, split(split(sku.plot, 'category: ')[1], ' | ')[0] as category LIMIT 5"

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
        results = get_graph_instance().query(query)
        
        return {
            "query": query,
            "results": results,
            "count": len(results) if results else 0
        }
    except Exception as e:
        return {"error": f"Query execution failed: {str(e)}"}

def analyze_and_format_results(question, results, count):
    """
    Use LLM to intelligently analyze and format query results
    """
    
    # Create a prompt for the LLM to analyze and format results
    analysis_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a data analyst expert. Your task is to analyze database query results and format them into a clear, informative response.

Given a user question and the query results, create a well-structured response that:
1. Answers the user's question directly
2. Formats the data in a readable way
3. Provides insights when possible
4. Uses markdown formatting for better presentation

Guidelines:
- Use bullet points for lists
- Use bold formatting for key information
- Group related information together
- Provide context and insights when relevant
- Keep responses concise but informative
- Format numbers appropriately (currency, percentages, etc.)
- Handle empty or null values gracefully

User Question: {question}
Number of Results: {count}
Query Results: {results}

Format the response:"""),
        ("human", "{question}")
    ])
    
    try:
        # Convert results to a readable format
        results_str = str(results[:20])  # Limit to first 20 results to avoid token limits
        
        # Generate the analysis using the LLM
        chain = analysis_prompt | get_llm()
        response = chain.invoke({
            "question": question,
            "count": count,
            "results": results_str
        })
        
        return response.content.strip()
    except Exception as e:
        print(f"Error analyzing results: {e}")
        # Fallback to simple formatting
        return f"Found {count} result(s):\n" + "\n".join([f"- {result}" for result in results[:10]])

def enhanced_cypher_qa(question):
    """
    Enhanced Cypher Q&A with dynamic query generation and intelligent response formatting
    """
    print(f"🔍 DEBUG: enhanced_cypher_qa() called with question: '{question}'")
    
    try:
        # Generate dynamic Cypher query
        print("🔍 DEBUG: Generating dynamic Cypher query...")
        cypher_query = generate_dynamic_cypher_query(question)
        print(f"🔍 DEBUG: Generated query: {cypher_query}")
        
        # Execute the query
        print("🔍 DEBUG: Executing query...")
        graph = get_graph_instance()
        if graph is None:
            print("❌ DEBUG: Graph instance is None")
            return "Database connection not available."
        
        result = graph.query(cypher_query)
        print(f"🔍 DEBUG: Query returned {len(result)} results")
        
        # Format the results intelligently
        print("🔍 DEBUG: Formatting results...")
        formatted_response = analyze_and_format_results(question, result, len(result))
        print(f"🔍 DEBUG: Formatted response: {formatted_response[:100]}...")
        
        return formatted_response
        
    except Exception as e:
        print(f"❌ DEBUG: Error in enhanced_cypher_qa: {e}")
        return f"Error processing your request: {str(e)}"

# Keep the original simple cypher_search for backward compatibility
def cypher_search(query):
    """Simple keyword-based search (legacy function)"""
    if not get_graph_instance():
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
        
        results = get_graph_instance().query(cypher_query, {'query': query})
        return results
    except Exception as e:
        print(f"Cypher search error: {e}")
        return []

def cypher_qa(question):
    """
    Legacy function for backward compatibility - now uses enhanced version
    """
    return enhanced_cypher_qa(question)