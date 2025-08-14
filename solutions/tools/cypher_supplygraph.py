#!/usr/bin/env python3
"""
Cypher queries for SupplyGraph dataset.

This module provides Cypher queries specifically designed for the SupplyGraph
benchmark dataset schema, which includes:
- Products (nodes with codes like SOS008L02P, POV005L04P, etc.)
- Product Groups (S, P, A, M, E) and SubGroups (SOS, POV, POP, AT, MAR, etc.)
- Plants (1911, 1916, 1917, 1919, 1920, 1921, 2111, 2114, 2116, 2117, 2119, 2120, 2121)
- Storage Locations (1130.0, 1430.0, 1630.0, 1730.0, 1930.0, 2030.0, 2130.0)
- Temporal data (Production, Sales Order, Factory Issue, Delivery to Distributor)
- Both Unit and Weight measurements
"""

import streamlit as st
import os
from typing import Dict, List, Optional, Any
from llm import get_llm
from monitoring import record_event, timeit
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
import re

def execute_query(query: str, params: Optional[Dict[str, Any]] = None):
    """Execute a raw Cypher query and return results list."""
    graph = get_graph()
    if graph is None:
        return []
    with timeit("neo4j.query", {"query_preview": query[:140]}):
        return graph.query(query, params or {})

def get_product_overview():
    """Get overview of all products with their groups and subgroups"""
    query = """
    MATCH (p:Product)-[:IN_GROUP]->(g:Group)
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    RETURN p.code as product_code, g.code as group, sg.code as subgroup
    ORDER BY p.code
    """
    return execute_query(query)

def get_products_by_group(group_code: str):
    """Get all products in a specific group"""
    query = """
    MATCH (p:Product)-[:IN_GROUP]->(g:Group {code: $group_code})
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    RETURN p.code as product_code, sg.code as subgroup
    ORDER BY p.code
    """
    return execute_query(query, {"group_code": group_code})

def get_products_by_subgroup(subgroup_code: str):
    """Get all products in a specific subgroup"""
    query = """
    MATCH (p:Product)-[:IN_SUBGROUP]->(sg:SubGroup {code: $subgroup_code})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    RETURN p.code as product_code, g.code as group
    ORDER BY p.code
    """
    return execute_query(query, {"subgroup_code": subgroup_code})

def get_products_by_plant(plant_id: str):
    """Get all products produced at a specific plant"""
    query = """
    MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant {id: $plant_id})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    RETURN p.code as product_code, g.code as group, sg.code as subgroup
    ORDER BY p.code
    """
    return execute_query(query, {"plant_id": plant_id})

def get_products_by_storage(storage_id: float):
    """Get all products stored at a specific storage location"""
    query = """
    MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation {id: $storage_id})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    RETURN p.code as product_code, g.code as group, sg.code as subgroup
    ORDER BY p.code
    """
    return execute_query(query, {"storage_id": storage_id})

def get_product_details(product_code: str):
    """Get detailed information about a specific product"""
    query = """
    MATCH (p:Product {code: $product_code})
    OPTIONAL MATCH (p)-[:IN_GROUP]->(g:Group)
    OPTIONAL MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    OPTIONAL MATCH (p)-[:PRODUCED_AT]->(pl:Plant)
    OPTIONAL MATCH (p)-[:STORED_AT]->(sl:StorageLocation)
    OPTIONAL MATCH (p)-[:HAS_TIME_SERIES]->(ts:TimeSeries)
    RETURN p.code as product_code,
           g.code as group,
           sg.code as subgroup,
           collect(DISTINCT pl.id) as plants,
           collect(DISTINCT sl.id) as storage_locations,
           collect(DISTINCT {type: ts.type, measurement: ts.measurement_type}) as time_series
    """
    return execute_query(query, {"product_code": product_code})

def get_production_data(product_code: str, limit: int = 10):
    """Get production time series data for a product"""
    query = """
    MATCH (p:Product {code: $product_code})-[:HAS_TIME_SERIES]->(ts:TimeSeries {type: 'Production'})
    RETURN ts.measurement_type as measurement_type,
           ts.date as date,
           ts.value as value
    ORDER BY ts.date DESC
    LIMIT $limit
    """
    return execute_query(query, {"product_code": product_code, "limit": limit})

def get_sales_data(product_code: str, limit: int = 10):
    """Get sales order time series data for a product"""
    query = """
    MATCH (p:Product {code: $product_code})-[:HAS_TIME_SERIES]->(ts:TimeSeries {type: 'SalesOrder'})
    RETURN ts.measurement_type as measurement_type,
           ts.date as date,
           ts.value as value
    ORDER BY ts.date DESC
    LIMIT $limit
    """
    return execute_query(query, {"product_code": product_code, "limit": limit})

def get_group_statistics():
    """Get statistics for each product group"""
    query = """
    MATCH (p:Product)-[:IN_GROUP]->(g:Group)
    WITH g.code as group_code, count(p) as product_count
    MATCH (p:Product)-[:IN_GROUP]->(g:Group {code: group_code})
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    WITH group_code, product_count, collect(DISTINCT sg.code) as subgroups
    RETURN group_code, product_count, size(subgroups) as subgroup_count, subgroups
    ORDER BY product_count DESC
    """
    return execute_query(query)

def get_subgroup_statistics():
    """Get statistics for each product subgroup"""
    query = """
    MATCH (p:Product)-[:IN_SUBGROUP]->(sg:SubGroup)
    WITH sg.code as subgroup_code, count(p) as product_count
    MATCH (p:Product)-[:IN_SUBGROUP]->(sg:SubGroup {code: subgroup_code})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    WITH subgroup_code, product_count, collect(DISTINCT g.code) as groups
    RETURN subgroup_code, product_count, groups
    ORDER BY product_count DESC
    """
    return execute_query(query)

def get_plant_statistics():
    """Get statistics for each plant"""
    query = """
    MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant)
    WITH pl.id as plant_id, count(p) as product_count
    MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant {id: plant_id})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    WITH plant_id, product_count, collect(DISTINCT g.code) as groups
    RETURN plant_id, product_count, groups
    ORDER BY product_count DESC
    """
    return execute_query(query)

def get_storage_statistics():
    """Get statistics for each storage location"""
    query = """
    MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation)
    WITH sl.id as storage_id, count(p) as product_count
    MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation {id: storage_id})
    MATCH (p)-[:IN_GROUP]->(g:Group)
    WITH storage_id, product_count, collect(DISTINCT g.code) as groups
    RETURN storage_id, product_count, groups
    ORDER BY product_count DESC
    """
    return execute_query(query)

def get_related_products(product_code: str):
    """Get products that are related through groups, subgroups, plants, or storage"""
    query = """
    MATCH (p:Product {code: $product_code})
    OPTIONAL MATCH (p)-[:IN_GROUP]->(g:Group)<-[:IN_GROUP]-(related:Product)
    WHERE related.code <> $product_code
    WITH collect(DISTINCT {product: related.code, relationship: 'Same Group', group: g.code}) as group_related
    
    OPTIONAL MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)<-[:IN_SUBGROUP]-(related:Product)
    WHERE related.code <> $product_code
    WITH group_related + collect(DISTINCT {product: related.code, relationship: 'Same Subgroup', subgroup: sg.code}) as subgroup_related
    
    OPTIONAL MATCH (p)-[:PRODUCED_AT]->(pl:Plant)<-[:PRODUCED_AT]-(related:Product)
    WHERE related.code <> $product_code
    WITH subgroup_related + collect(DISTINCT {product: related.code, relationship: 'Same Plant', plant: pl.id}) as plant_related
    
    OPTIONAL MATCH (p)-[:STORED_AT]->(sl:StorageLocation)<-[:STORED_AT]-(related:Product)
    WHERE related.code <> $product_code
    WITH plant_related + collect(DISTINCT {product: related.code, relationship: 'Same Storage', storage: sl.id}) as all_related
    
    RETURN all_related
    """
    return execute_query(query, {"product_code": product_code})

def get_time_series_summary():
    """Get summary of available time series data"""
    query = """
    MATCH (ts:TimeSeries)
    RETURN ts.type as type,
           ts.measurement_type as measurement_type,
           count(ts) as count
    ORDER BY ts.type, ts.measurement_type
    """
    return execute_query(query)

def search_products(search_term: str):
    """Search for products by code (partial match)"""
    query = """
    MATCH (p:Product)
    WHERE p.code CONTAINS $search_term
    MATCH (p)-[:IN_GROUP]->(g:Group)
    MATCH (p)-[:IN_SUBGROUP]->(sg:SubGroup)
    RETURN p.code as product_code, g.code as group, sg.code as subgroup
    ORDER BY p.code
    LIMIT 20
    """
    return execute_query(query, {"search_term": search_term.upper()})

def get_dashboard_data():
    """Get comprehensive dashboard data"""
    dashboard_data = {
        "product_overview": get_product_overview(),
        "group_statistics": get_group_statistics(),
        "subgroup_statistics": get_subgroup_statistics(),
        "plant_statistics": get_plant_statistics(),
        "storage_statistics": get_storage_statistics(),
        "time_series_summary": get_time_series_summary()
    }
    return dashboard_data

def format_result(result):
    """Format a single result for better readability"""
    if isinstance(result, dict):
        # Format dictionary results
        formatted_parts = []
        for key, value in result.items():
            if value is not None:
                formatted_parts.append(f"{key}: {value}")
        return ", ".join(formatted_parts)
    else:
        return str(result)

def create_summary_statistics(results):
    """Create summary statistics for large result sets"""
    if not results:
        return "No data available"
    
    if isinstance(results[0], dict):
        # Analyze dictionary results
        keys = list(results[0].keys())
        summary = f"**Summary of {len(results)} records**:\n\n"
        
        for key in keys:
            values = [r.get(key) for r in results if r.get(key) is not None]
            if values:
                if isinstance(values[0], (int, float)):
                    # Numeric summary
                    summary += f"- **{key}**: {len(values)} values, avg: {sum(values)/len(values):.2f}\n"
                else:
                    # Categorical summary
                    unique_values = list(set(values))
                    summary += f"- **{key}**: {len(unique_values)} unique values\n"
        
        return summary
    else:
        return f"**Summary**: {len(results)} total results"

def create_supply_chain_dashboard():
    """Create a comprehensive supply chain dashboard with formatted results"""
    try:
        # Get all dashboard data
        dashboard_data = get_dashboard_data()
        
        # Format the dashboard response
        dashboard_text = """
# 📊 SupplyChain Dashboard - SupplyGraph Analysis

## 📈 Key Metrics
"""
        
        # Product Overview
        products = dashboard_data["product_overview"]
        dashboard_text += f"""
**Total Products**: {len(products)} products across the supply chain

**Product Distribution by Group**:
"""
        
        # Group Statistics
        groups = dashboard_data["group_statistics"]
        for group in groups:
            dashboard_text += f"- **Group {group['group_code']}**: {group['product_count']} products ({len(group['subgroups'])} subgroups)\n"
        
        dashboard_text += "\n## 🏭 Plant Analysis\n"
        
        # Plant Statistics
        plants = dashboard_data["plant_statistics"]
        dashboard_text += f"**Total Plants**: {len(plants)} production facilities\n\n"
        
        # Top plants by product count
        top_plants = sorted(plants, key=lambda x: x.get('product_count', 0), reverse=True)[:5]
        dashboard_text += "**Top 5 Plants by Product Count**:\n"
        for plant in top_plants:
            dashboard_text += f"- Plant {plant['plant_id']}: {plant.get('product_count', 0)} products\n"
        
        dashboard_text += "\n## 📦 Storage Analysis\n"
        
        # Storage Statistics
        storage = dashboard_data["storage_statistics"]
        dashboard_text += f"**Total Storage Locations**: {len(storage)} facilities\n\n"
        
        # Top storage by product count
        top_storage = sorted(storage, key=lambda x: x.get('product_count', 0), reverse=True)[:5]
        dashboard_text += "**Top 5 Storage Locations by Product Count**:\n"
        for loc in top_storage:
            dashboard_text += f"- Location {loc['storage_id']}: {loc.get('product_count', 0)} products\n"
        
        dashboard_text += "\n## 📊 Subgroup Analysis\n"
        
        # Subgroup Statistics
        subgroups = dashboard_data["subgroup_statistics"]
        dashboard_text += f"**Total Subgroups**: {len(subgroups)} product categories\n\n"
        
        # Top subgroups by product count
        top_subgroups = sorted(subgroups, key=lambda x: x.get('product_count', 0), reverse=True)[:5]
        dashboard_text += "**Top 5 Subgroups by Product Count**:\n"
        for sg in top_subgroups:
            dashboard_text += f"- {sg['subgroup_code']}: {sg.get('product_count', 0)} products\n"
        
        dashboard_text += "\n## ⏰ Time Series Data\n"
        
        # Time Series Summary
        time_series = dashboard_data["time_series_summary"]
        if time_series:
            dashboard_text += "**Available Time Series Data**:\n"
            for ts in time_series:
                dashboard_text += f"- {ts.get('type', 'Unknown')} ({ts.get('measurement_type', 'Unknown')}): {ts.get('count', 0)} records\n"
        else:
            dashboard_text += "No time series data available\n"
        
        dashboard_text += "\n---\n*Dashboard generated from SupplyGraph dataset analysis*"
        
        return dashboard_text
        
    except Exception as e:
        return f"""
# 📊 SupplyChain Dashboard

**Error**: Unable to generate dashboard due to: {str(e)}

**Note**: Please check the database connection and data availability.
"""

def enhanced_cypher_qa(question: str) -> str:
    """Enhanced Cypher Q&A for SupplyGraph dataset"""
    try:
        # Special handling for dashboard requests
        if "dashboard" in question.lower() or "comprehensive" in question.lower():
            return create_supply_chain_dashboard()
        
        llm = get_llm()
        
        # Create a comprehensive prompt for SupplyGraph queries
        prompt = f"""
You are a SupplyGraph data analyst. Based on the user's question, determine the best Cypher query to answer it.

Available data schema:
- Products: nodes with codes like SOS008L02P, POV005L04P, etc.
- Groups: S, P, A, M, E
- SubGroups: SOS, POV, POP, AT, MAR, etc.
- Plants: 1911, 1916, 1917, 1919, 1920, 1921, 2111, 2114, 2116, 2117, 2119, 2120, 2121
- Storage Locations: 1130.0, 1430.0, 1630.0, 1730.0, 1930.0, 2030.0, 2130.0
- TimeSeries: Production, SalesOrder, FactoryIssue, DeliveryToDistributor (Unit/Weight)

Relationships:
- (Product)-[:IN_GROUP]->(Group)
- (Product)-[:IN_SUBGROUP]->(SubGroup)
- (Product)-[:PRODUCED_AT]->(Plant)
- (Product)-[:STORED_AT]->(StorageLocation)
- (Product)-[:HAS_TIME_SERIES]->(TimeSeries)

Question: "{question}"

IMPORTANT: Respond with ONLY a valid JSON object in this exact format:
{{
    "query": "MATCH (p:Product)-[:IN_GROUP]->(g:Group) WHERE g.code = 'S' RETURN count(p) as productCount",
    "explanation": "This query finds all Product nodes that are connected to the Group node with name 'S' via the IN_GROUP relationship and counts them.",
    "expected_result": "A count of products in Group S"
}}

Focus on:
- Product analysis and categorization
- Plant and storage location analysis
- Time series data (production, sales, etc.)
- Group and subgroup relationships
- Supply chain network analysis

DO NOT include any text before or after the JSON object.
"""

        response = llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # Extract JSON from response with better error handling
        import json
        import re
        
        # Clean the response text to remove control characters
        response_text = response_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        response_text = re.sub(r'[^\x20-\x7E]', '', response_text)  # Remove non-printable characters
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                query_data = json.loads(json_match.group())
                cypher_query = query_data.get("query", "")
                explanation = query_data.get("explanation", "")
            except json.JSONDecodeError as e:
                # Fallback: try to extract query directly
                cypher_match = re.search(r'MATCH.*RETURN', response_text, re.IGNORECASE | re.DOTALL)
                if cypher_match:
                    cypher_query = cypher_match.group()
                    explanation = "Query extracted from LLM response"
                else:
                    cypher_query = ""
                    explanation = "Could not parse query from response"
            
            if cypher_query:
                # Execute the query
                results = execute_query(cypher_query)
                
                # Format the response
                if results:
                    result_summary = f"Found {len(results)} results"
                    
                    # Format results in a more readable way
                    if len(results) <= 5:
                        # For small results, show all data in a table format
                        result_details = "\n".join([f"- {format_result(r)}" for r in results])
                    elif len(results) <= 20:
                        # For medium results, show first 10 in table format
                        result_details = "\n".join([f"- {format_result(r)}" for r in results[:10]])
                        if len(results) > 10:
                            result_details += f"\n... and {len(results) - 10} more results"
                    else:
                        # For large results, show summary statistics
                        result_details = create_summary_statistics(results)
                    
                    return f"""
# 📊 SupplyGraph Analysis Results

**Query**: {explanation}

**Results**: {result_summary}

**Analysis**:
{result_details}
"""
                else:
                    return f"""
# 📊 SupplyGraph Analysis Results

**Query**: {explanation}

**Results**: No data found for this query.

**Note**: The query executed successfully but returned no results. This might indicate:
- The requested data doesn't exist
- The query parameters need adjustment
- The data relationships are different than expected
"""
            else:
                return f"""
# 📊 SupplyGraph Analysis

**Status**: Could not generate a valid Cypher query

**Response**: {response_text}

**Note**: Please try rephrasing your question to be more specific about what you want to analyze in the SupplyGraph dataset.
"""
        else:
            return f"""
# 📊 SupplyGraph Analysis

**Status**: Could not parse response

**Response**: {response_text}

**Note**: Please try rephrasing your question to be more specific about what you want to analyze in the SupplyGraph dataset.
"""
            
    except Exception as e:
        return f"""
# ❌ Error in SupplyGraph Analysis

**Error**: {str(e)}

**Note**: There was an error processing your request. Please try:
1. Rephrasing your question
2. Being more specific about what you want to analyze
3. Using simpler terms
"""

# Common query patterns for specific types of questions
QUERY_PATTERNS = {
    "product_count": "MATCH (p:Product) RETURN count(p) as total_products",
    "group_products": "MATCH (p:Product)-[:IN_GROUP]->(g:Group) RETURN g.code as group, count(p) as product_count ORDER BY product_count DESC",
    "subgroup_products": "MATCH (p:Product)-[:IN_SUBGROUP]->(sg:SubGroup) RETURN sg.code as subgroup, count(p) as product_count ORDER BY product_count DESC",
    "plant_products": "MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant) RETURN pl.id as plant, count(p) as product_count ORDER BY product_count DESC",
    "storage_products": "MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation) RETURN sl.id as storage, count(p) as product_count ORDER BY product_count DESC",
    "time_series_types": "MATCH (ts:TimeSeries) RETURN ts.type as type, ts.measurement_type as measurement, count(ts) as count ORDER BY type, measurement"
}
