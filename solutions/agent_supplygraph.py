#!/usr/bin/env python3
"""
SupplyGraph Agent for LLM-based RAG flow.

This agent is specifically designed to work with the SupplyGraph benchmark dataset,
providing comprehensive supply chain analysis capabilities.
"""

import streamlit as st
from llm import get_llm
from monitoring import record_event, timeit
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from utils import get_session_id

from solutions.tools.cypher_supplygraph import (
    enhanced_cypher_qa, get_dashboard_data, get_product_details,
    get_products_by_group, get_products_by_subgroup, get_products_by_plant,
    get_products_by_storage, get_production_data, get_sales_data,
    get_group_statistics, get_subgroup_statistics, get_plant_statistics,
    get_storage_statistics, get_related_products, search_products
)

# Domain configuration for SupplyGraph
SUPPLYGRAPH_CONFIG = {
    "domain_name": "SupplyGraph benchmark dataset for supply chain planning",
    "entity_type": "Product",
    "entity_label": "Product", 
    "entity_id_field": "code",
    "domain_expertise": "supply chain planning, manufacturing capacity, inventory management, demand forecasting, production analysis, plant utilization, storage optimization, and supply chain network analysis",
    "entity_plural": "Products",
    "entity_singular": "Product"
}

# SupplyGraph-specific chat prompt
supplygraph_chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a SupplyGraph data analyst specializing in supply chain planning and analysis. You work with a comprehensive benchmark dataset that includes:

**Data Schema:**
- **Products**: 40 products with codes like SOS008L02P, POV005L04P, etc.
- **Groups**: 5 main groups (S, P, A, M, E) representing different product categories
- **SubGroups**: 19 subgroups (SOS, POV, POP, AT, MAR, etc.) for detailed categorization
- **Plants**: 25 manufacturing plants (1911, 1916, 1917, 1919, 1920, 1921, 2111, 2114, 2116, 2117, 2119, 2120, 2121)
- **Storage Locations**: 13 storage facilities (1130.0, 1430.0, 1630.0, 1730.0, 1930.0, 2030.0, 2130.0)
- **Time Series Data**: Production, Sales Order, Factory Issue, Delivery to Distributor (both Unit and Weight measurements)

**Your Expertise:**
- Supply chain network analysis and optimization
- Production capacity planning and plant utilization
- Inventory management and storage optimization
- Demand forecasting and sales analysis
- Product categorization and relationship analysis
- Time series data analysis for supply chain metrics

**Communication Style:**
- Professional but approachable
- Data-driven insights with practical business implications
- Clear explanations of complex supply chain concepts
- Collaborative problem-solving approach

You can analyze the SupplyGraph dataset to provide insights on manufacturing efficiency, supply chain optimization, demand patterns, and operational improvements."""),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# Define SupplyGraph-specific tools
supplygraph_tools = [
    Tool(
        name="SupplyGraph Database Query",
        func=enhanced_cypher_qa,
        description="Use this tool for ANY SupplyGraph supply chain analysis, including product analysis, plant utilization, storage optimization, time series analysis, and supply chain network analysis. Input: the question (e.g., 'How many products are in Group S?', 'Which plant produces the most products?', 'Show me production data for SOS008L02P', 'What are the storage locations for products in subgroup POV?', 'Analyze sales patterns across different groups', 'Find products with similar production characteristics'). This tool queries the SupplyGraph database and returns comprehensive analysis with detailed insights."
    ),
    Tool(
        name="Product Search",
        func=search_products,
        description="Search for products by code (partial match). Input: search term (e.g., 'SOS', 'POV', 'AT'). Returns matching products with their group and subgroup information."
    ),
    Tool(
        name="Product Details",
        func=get_product_details,
        description="Get detailed information about a specific product including its group, subgroup, plants, storage locations, and available time series data. Input: product code (e.g., 'SOS008L02P')."
    ),
    Tool(
        name="Group Analysis",
        func=get_products_by_group,
        description="Get all products in a specific group. Input: group code (S, P, A, M, or E)."
    ),
    Tool(
        name="Subgroup Analysis",
        func=get_products_by_subgroup,
        description="Get all products in a specific subgroup. Input: subgroup code (e.g., 'SOS', 'POV', 'POP')."
    ),
    Tool(
        name="Plant Analysis",
        func=get_products_by_plant,
        description="Get all products produced at a specific plant. Input: plant ID (e.g., '1911', '2120')."
    ),
    Tool(
        name="Storage Analysis",
        func=get_products_by_storage,
        description="Get all products stored at a specific storage location. Input: storage ID (e.g., 2030.0, 1130.0)."
    ),
    Tool(
        name="Production Data",
        func=get_production_data,
        description="Get production time series data for a specific product. Input: product code (e.g., 'SOS008L02P')."
    ),
    Tool(
        name="Sales Data",
        func=get_sales_data,
        description="Get sales order time series data for a specific product. Input: product code (e.g., 'SOS008L02P')."
    ),
    Tool(
        name="Group Statistics",
        func=get_group_statistics,
        description="Get comprehensive statistics for all product groups including product counts and subgroups."
    ),
    Tool(
        name="Subgroup Statistics",
        func=get_subgroup_statistics,
        description="Get comprehensive statistics for all product subgroups including product counts and groups."
    ),
    Tool(
        name="Plant Statistics",
        func=get_plant_statistics,
        description="Get comprehensive statistics for all plants including product counts and groups."
    ),
    Tool(
        name="Storage Statistics",
        func=get_storage_statistics,
        description="Get comprehensive statistics for all storage locations including product counts and groups."
    ),
    Tool(
        name="Related Products",
        func=get_related_products,
        description="Find products related to a specific product through groups, subgroups, plants, or storage locations. Input: product code (e.g., 'SOS008L02P')."
    ),
    Tool(
        name="SupplyGraph Dashboard",
        func=get_dashboard_data,
        description="Get comprehensive dashboard data including product overview, group/subgroup statistics, plant/storage statistics, and time series summary."
    ),
    Tool(
        name="General SupplyGraph Chat",
        func=lambda x: f"I can help you analyze the SupplyGraph dataset for supply chain planning insights. Please ask about specific products, groups, plants, storage locations, or supply chain analysis.",
        description="General conversation about SupplyGraph supply chain topics. Input: general questions about the dataset or supply chain concepts."
    )
]

def get_supplygraph_memory(session_id):
    """Get memory for SupplyGraph agent"""
    return Neo4jChatMessageHistory(session_id=session_id, graph=get_graph())

# SupplyGraph agent prompt
supplygraph_agent_prompt = PromptTemplate.from_template("""
You are a SupplyGraph data analyst specializing in supply chain planning and analysis. You work with a comprehensive benchmark dataset that includes products, groups, subgroups, plants, storage locations, and time series data.

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

When analyzing SupplyGraph data, focus on:
1. **Product Analysis**: Understanding product categorization, relationships, and characteristics
2. **Plant Utilization**: Analyzing manufacturing capacity and production patterns
3. **Storage Optimization**: Understanding storage location usage and product distribution
4. **Time Series Analysis**: Examining production, sales, and delivery patterns over time
5. **Supply Chain Network**: Analyzing relationships between products, plants, and storage locations

Always provide insights that are relevant to supply chain planning and optimization.

Question: {input}
Thought:{agent_scratchpad}
""")

def create_supplygraph_agent():
    """Create the SupplyGraph agent"""
    agent = create_react_agent(
        llm=get_llm(),
        tools=supplygraph_tools,
        prompt=supplygraph_agent_prompt
    )
    
    return AgentExecutor(
        agent=agent,
        tools=supplygraph_tools,
        verbose=True,
        handle_parsing_errors=True
    )

def generate_supplygraph_response(question: str, session_id: str = None) -> str:
    """Generate a response for SupplyGraph queries"""
    try:
        if session_id is None:
            session_id = get_session_id()
        
        agent = create_supplygraph_agent()
        
        with timeit("supplygraph.agent.response", {"question_preview": question[:100]}):
            response = agent.invoke({
                "input": question,
                "session_id": session_id
            })
        
        return response.get("output", "I couldn't generate a response for that question.")
        
    except Exception as e:
        record_event("supplygraph.agent.error", {"error": str(e), "question": question})
        return f"I encountered an error while processing your question: {str(e)}. Please try rephrasing your question or ask about a different aspect of the SupplyGraph dataset."

# Quick test functions for common SupplyGraph queries
def test_supplygraph_queries():
    """Test common SupplyGraph queries"""
    test_queries = [
        "How many products are in the dataset?",
        "What are the main product groups?",
        "Which plant produces the most products?",
        "Show me products in group S",
        "What storage locations are used?",
        "Get details for product SOS008L02P",
        "Show me production data for SOS008L02P",
        "Find products related to POV005L04P",
        "Analyze group statistics",
        "Create a supply chain dashboard"
    ]
    
    results = {}
    for query in test_queries:
        try:
            response = generate_supplygraph_response(query)
            results[query] = {
                "status": "success",
                "response_length": len(response),
                "response_preview": response[:200] + "..." if len(response) > 200 else response
            }
        except Exception as e:
            results[query] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

if __name__ == "__main__":
    # Test the SupplyGraph agent
    print("Testing SupplyGraph agent...")
    results = test_supplygraph_queries()
    
    for query, result in results.items():
        print(f"\nQuery: {query}")
        print(f"Status: {result['status']}")
        if result['status'] == 'success':
            print(f"Response Length: {result['response_length']}")
            print(f"Preview: {result['response_preview']}")
        else:
            print(f"Error: {result['error']}")
