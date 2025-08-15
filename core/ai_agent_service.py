# Extracted AI Agent Service
# All your Streamlit AI logic extracted into reusable service

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor

# LangChain imports (from your existing code)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub

# Import your existing modules
from llm import get_llm
from solutions.graph import get_graph
from solutions.tools.vector import get_sku_data
from solutions.tools.cypher_supplygraph import enhanced_cypher_qa, get_dashboard_data, search_products, get_product_details
from solutions.tools.data_parser import parse_sku_data
from monitoring import record_event, timeit

logger = logging.getLogger(__name__)

class AdvancedAIAgentService:
    """
    Advanced AI Agent Service extracted from Streamlit
    
    Provides all your existing AI capabilities plus enhanced features:
    - Multi-turn conversations with memory
    - Advanced reasoning and analysis
    - Graph-aware responses
    - Performance monitoring
    - Async processing
    """
    
    def __init__(self):
        self.agent_executor = None
        self.chat_agent = None
        self.domain_config = None
        self._session_memories = {}
        self._initialize_ai_services()
    
    def _initialize_ai_services(self):
        """Initialize AI services with your existing configuration"""
        try:
            # Domain configuration for SupplyGraph dataset
            self.domain_config = {
                "domain_name": "SupplyGraph benchmark dataset for supply chain planning",
                "entity_type": "Product",
                "entity_label": "Product", 
                "entity_id_field": "code",
                "domain_expertise": "supply chain planning, manufacturing capacity, inventory management, demand forecasting, production analysis, plant utilization, storage optimization, and supply chain network analysis",
                "entity_plural": "Products",
                "entity_singular": "Product"
            }
            
            # Initialize tools (from your existing code)
            self.tools = self._create_enhanced_tools()
            
            # Create agent
            self._create_agent()
            
            logger.info("✅ AI Agent services initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing AI services: {e}")
            self.agent_executor = None
    
    def _create_enhanced_tools(self) -> List[Tool]:
        """Create enhanced tools with your existing logic"""
        
        tools = [
            Tool(
                name="SupplyGraph Database Query",
                func=enhanced_cypher_qa,
                description="""Use this tool for ANY SupplyGraph supply chain analysis, including product analysis, plant utilization, storage optimization, time series analysis, and supply chain network analysis. 
                
                Input: the question (e.g., 'How many products are in Group S?', 'Which plant produces the most products?', 'Show me production data for SOS008L02P', 'What are the storage locations for products in subgroup POV?', 'Analyze sales patterns across different groups', 'Find products with similar production characteristics', 'Show me plant utilization statistics', 'Analyze inventory distribution across storage locations'). 
                
                This tool queries the SupplyGraph database and returns comprehensive analysis with detailed insights for supply chain planning and optimization.
                
                CRITICAL: When you receive this data, you MUST present the ENTIRE response EXACTLY as provided, including ALL sections and analysis. NEVER summarize, condense, or rephrase this data - present the COMPLETE analysis with all tables, metrics, and insights exactly as received."""
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
                name="SupplyGraph Dashboard",
                func=get_dashboard_data,
                description="Get comprehensive dashboard data including product overview, group/subgroup statistics, plant/storage statistics, and time series summary."
            ),
            Tool(
                name="Entity Information Search",
                func=get_sku_data,
                description="Use ONLY for semantic similarity search when Enhanced Database Query doesn't work. Input: search terms. NEVER use for specific SKU queries or 'all SKUs' queries. For 'What SKUs are in the master data?' use Enhanced Database Query instead."
            ),
            Tool(
                name="Entity Data Parser",
                func=parse_sku_data,
                description="Use ONLY to extract structured data from raw SKU data. Input: raw SKU data. Use after Enhanced Database Query."
            ),
            Tool(
                name="Advanced Analytics",
                func=self._advanced_analytics_tool,
                description="Use for advanced graph analytics, machine learning insights, pattern detection, and sophisticated supply chain analysis. Input: analytical question or request for insights."
            ),
            Tool(
                name="General Chat",
                func=lambda x: f"I can help you with {self.domain_config['domain_name']} questions. Please ask about specific {self.domain_config['entity_plural']}, plant utilization, storage optimization, time series analysis, or supply chain network analysis.",
                description=f"General conversation about {self.domain_config['domain_name']} topics. Input: general questions about SupplyGraph dataset or supply chain concepts."
            )
        ]
        
        return tools
    
    def _advanced_analytics_tool(self, query: str) -> str:
        """Advanced analytics tool using graph analytics engine"""
        try:
            # Import here to avoid circular imports
            from core.graph_analytics_engine import analytics_engine
            
            # Determine type of analysis needed
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['cluster', 'group', 'segment', 'pattern']):
                # Run clustering analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                insights = loop.run_until_complete(analytics_engine.detect_supply_chain_patterns())
                loop.close()
                
                clustering_insights = [i for i in insights if i.insight_type == 'clustering']
                if clustering_insights:
                    insight = clustering_insights[0]
                    return f"""# 🔬 Advanced Analytics: {insight.title}

{insight.description}

## 📊 Key Metrics:
- Clusters Identified: {insight.metrics.get('cluster_count', 'N/A')}
- SKUs Analyzed: {insight.metrics.get('total_skus_analyzed', 'N/A')}
- Analysis Quality Score: {insight.confidence:.2f}

## 💡 Strategic Recommendations:
{chr(10).join(['• ' + rec for rec in insight.recommendations])}

*Generated using advanced machine learning clustering analysis*"""
                
            elif any(word in query_lower for word in ['risk', 'inventory', 'lead time', 'supply']):
                # Run risk analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                insights = loop.run_until_complete(analytics_engine.detect_supply_chain_patterns())
                loop.close()
                
                risk_insights = [i for i in insights if i.insight_type == 'inventory_risk']
                if risk_insights:
                    insight = risk_insights[0]
                    return f"""# ⚠️ Advanced Analytics: {insight.title}

{insight.description}

## 📊 Risk Assessment:
- High Risk SKUs: {insight.metrics.get('high_risk_count', 'N/A')}
- Medium Risk SKUs: {insight.metrics.get('medium_risk_count', 'N/A')}
- Average Lead Time: {insight.metrics.get('average_lead_time', 'N/A')} days

## 🎯 Priority Actions:
{chr(10).join(['• ' + rec for rec in insight.recommendations])}

*Generated using advanced risk modeling and statistical analysis*"""
            
            elif any(word in query_lower for word in ['profit', 'margin', 'performance', 'financial']):
                # Run profitability analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                insights = loop.run_until_complete(analytics_engine.detect_supply_chain_patterns())
                loop.close()
                
                profit_insights = [i for i in insights if i.insight_type == 'profitability']
                if profit_insights:
                    insight = profit_insights[0]
                    return f"""# 💰 Advanced Analytics: {insight.title}

{insight.description}

## 📊 Financial Performance:
- Total Gross Profit: ${insight.metrics.get('total_gross_profit', 0):,.2f}
- Average Profit Margin: {insight.metrics.get('average_profit_margin', 0):.1f}%
- Profitable SKUs: {insight.metrics.get('profitable_skus', 'N/A')}
- Loss-Making SKUs: {insight.metrics.get('loss_making_skus', 'N/A')}

## 🎯 Strategic Focus:
{chr(10).join(['• ' + rec for rec in insight.recommendations])}

*Generated using advanced profitability modeling and Pareto analysis*"""
            
            else:
                # General overview
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                overview = loop.run_until_complete(analytics_engine.get_graph_overview())
                loop.close()
                
                return f"""# 📈 Advanced Analytics: Graph Overview

## 📊 Graph Database Statistics:
- Total Nodes: {overview.get('node_statistics', {}).get('total_nodes', 'N/A')}
- Total Relationships: {overview.get('relationship_statistics', {}).get('total_relationships', 'N/A')}

## 🔍 Advanced Metrics:
- Graph Density: {overview.get('advanced_metrics', {}).get('density', 'N/A')}
- Connected Components: {overview.get('advanced_metrics', {}).get('number_of_components', 'N/A')}
- Average Clustering: {overview.get('advanced_metrics', {}).get('average_clustering', 'N/A')}

*Use specific requests like 'analyze profitability patterns' or 'identify inventory risks' for detailed insights*"""
        
        except Exception as e:
            logger.error(f"Error in advanced analytics tool: {e}")
            return f"Advanced analytics temporarily unavailable. Error: {str(e)}"
    
    def _create_agent(self):
        """Create the AI agent with your existing configuration"""
        try:
            llm = get_llm()
            
            # Enhanced agent prompt (based on your existing prompt)
            agent_prompt = PromptTemplate.from_template("""
You are a thoughtful, collaborative S&OP (Sales & Operations Planning) supply chain colleague. You analyze real-time scenarios across supply, demand, and sales while understanding trade-offs between manufacturing capacity, inventory, customer service levels, and forecast accuracy.

You have access to the following tools:
{tools}

CRITICAL RULES FOR TOOL USAGE:
1. For ANY S&OP supply chain analysis, manufacturing capacity constraints, customer prioritization, regional demand variations, promotional impact, inventory balancing, or cross-functional planning scenarios, you MUST use the Enhanced Database Query tool
2. For advanced analytics, pattern detection, machine learning insights, use the Advanced Analytics tool
3. For greetings, casual conversation, or non-data requests, respond directly with "Final Answer:"
4. ALWAYS use proper ReAct format: "Action:" then tool name, then "Action Input:" then your query
5. For direct responses: "Final Answer:" then your response
6. NEVER include "Invalid Format" or error messages in your response
7. NEVER loop or repeat the same action multiple times
8. If a tool fails, try a different approach or provide a helpful response
9. For supply chain analysis, manufacturing constraints, customer prioritization, regional analysis, promotional impact, or SKU-specific queries, ALWAYS use the Enhanced Database Query tool
10. For general data requests like "show me all SKUs", "list products", or "list categories", you MUST use the Enhanced Database Query tool (do NOT use the Entity Information Search)
11. For analytical queries like "capacity constraints", "customer prioritization", "regional demand", "promotional impact", use the Enhanced Database Query tool
12. For advanced pattern detection, clustering, risk analysis, or machine learning insights, use the Advanced Analytics tool

S&OP ANALYSIS REQUIREMENTS:
- When analyzing manufacturing capacity constraints, consider utilization rates, available capacity, and production feasibility
- When discussing customer prioritization, consider relationship impact, revenue contribution, and strategic importance
- When examining regional demand variations, consider market size, growth rates, and service level requirements
- When assessing promotional impact, consider demand uplift, budget allocation, and production capacity requirements
- When analyzing inventory balancing, consider safety stock, reorder points, and excess inventory opportunities
- When discussing cross-functional planning, consider the feedback loops between Sales, Demand, and Supply Planning
- When using Advanced Analytics, provide sophisticated insights using machine learning and graph algorithms

EXECUTIVE DASHBOARD REQUIREMENTS:
- When you receive comprehensive SKU data with executive dashboard format, PRESENT THE ENTIRE DASHBOARD AS-IS
- NEVER summarize, condense, or rephrase the executive dashboard data
- If the data includes sections like "📊 Executive Summary", "💰 Financial Performance", "📦 Inventory Management", "📈 Monthly Demand Analysis", "🎯 Strategic Insights", and "💡 Executive Recommendations" - PRESENT ALL OF THEM
- Include ALL tables, metrics, and detailed analysis exactly as provided
- For inventory questions, show the complete monthly demand analysis table with all 18 months
- For financial questions, include all revenue, cost, margin, and profitability calculations
- Present the data in the exact same professional format with all markdown formatting
- If charts or visualizations are included, present them as well
- The goal is to provide COMPLETE executive-level business intelligence, not summaries
- Only add brief contextual analysis if the question specifically asks for interpretation
- IMPORTANT: If you receive a comprehensive executive dashboard response from a tool, RETURN THAT EXACT RESPONSE without any modification or summary
- CRITICAL: When you receive data starting with "# 📊 Executive Summary:", return that EXACT data without any changes, summaries, or modifications
- CRITICAL: If you see "# 📊 Executive Summary:" in the tool response, copy and paste that ENTIRE response without any changes
- CRITICAL: DO NOT SUMMARIZE - PRESENT THE COMPLETE EXECUTIVE DASHBOARD

Remember: You are delivering executive dashboard reports with advanced analytics capabilities, not answering simple questions. When you receive rich data, present it exactly as received. NEVER summarize executive dashboard data. COPY AND PASTE THE ENTIRE EXECUTIVE DASHBOARD RESPONSE.

Begin!

Question: {input}
{agent_scratchpad}
""")
            
            # Use the standard LangChain hub prompt with enhancements
            prompt = hub.pull("hwchase17/react")
            
            # Create agent
            self.agent = create_react_agent(llm, self.tools, prompt)
            
            # Create agent executor with enhanced configuration
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,  # Increased for complex analyses
                return_intermediate_steps=True
            )
            
            logger.info("✅ AI Agent created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating AI agent: {e}")
            self.agent_executor = None
    
    async def chat_async(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Async chat with AI agent"""
        try:
            record_event("chat.request", {"message_preview": message[:100], "session_id": session_id})
            
            if not self.agent_executor:
                return {
                    "response": "AI Agent is not available. Please check the configuration.",
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "session_id": session_id
                }
            
            # Execute in thread pool to avoid blocking
            with ThreadPoolExecutor() as executor:
                with timeit("agent.execute"):
                    response = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: self.agent_executor.invoke({"input": message})
                    )
            
            # Extract response
            ai_response = response.get('output', str(response))
            
            # Enhanced response formatting
            formatted_response = self._format_response(ai_response, message)
            
            record_event("chat.success", {"response_length": len(formatted_response)})
            
            return {
                "response": formatted_response,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "session_id": session_id,
                "intermediate_steps": len(response.get('intermediate_steps', []))
            }
            
        except Exception as e:
            logger.error(f"Error in async chat: {e}")
            record_event("chat.error", {"error": str(e)})
            
            return {
                "response": f"I apologize, but I encountered an error processing your request. Please try rephrasing your question or contact support if the issue persists.\n\nError details: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "session_id": session_id
            }
    
    def chat_sync(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Synchronous chat interface"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.chat_async(message, session_id))
        finally:
            loop.close()
    
    def _format_response(self, response: str, original_message: str) -> str:
        """Enhanced response formatting with intelligence"""
        try:
            # If response contains executive dashboard markers, return as-is
            dashboard_markers = [
                "# 📊 Executive Dashboard:",
                "# 📊 Executive Summary:",
                "# 🔬 Advanced Analytics:",
                "# ⚠️ Advanced Analytics:",
                "# 💰 Advanced Analytics:",
                "# 📈 Advanced Analytics:"
            ]
            
            if any(marker in response for marker in dashboard_markers):
                return response
            
            # Add contextual enhancements for simple responses
            if len(response.strip()) < 100 and not any(marker in response for marker in ["##", "###", "```", "|"]):
                # This looks like a simple response, enhance it
                return f"""{response}

💡 **For more detailed analysis**, try asking:
• "Show me advanced analytics for this topic"
• "Provide executive dashboard view"
• "Analyze patterns and trends"
• "Give me comprehensive insights"

*Powered by advanced graph analytics and machine learning*"""
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting response: {e}")
            return response
    
    def get_session_memory(self, session_id: str) -> Neo4jChatMessageHistory:
        """Get or create session memory"""
        if session_id not in self._session_memories:
            try:
                graph = get_graph()
                if graph:
                    self._session_memories[session_id] = Neo4jChatMessageHistory(
                        session_id=session_id, 
                        graph=graph
                    )
                else:
                    logger.warning("No graph connection for session memory")
                    return None
            except Exception as e:
                logger.error(f"Error creating session memory: {e}")
                return None
        
        return self._session_memories[session_id]
    
    def reset_session(self, session_id: str):
        """Reset session memory"""
        if session_id in self._session_memories:
            try:
                memory = self._session_memories[session_id]
                memory.clear()
                del self._session_memories[session_id]
                logger.info(f"Session {session_id} reset successfully")
            except Exception as e:
                logger.error(f"Error resetting session {session_id}: {e}")
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive agent status"""
        return {
            "agent_available": self.agent_executor is not None,
            "tools_count": len(self.tools) if self.tools else 0,
            "active_sessions": len(self._session_memories),
            "domain_config": self.domain_config,
            "timestamp": datetime.now().isoformat()
        }

# Create singleton instance
ai_agent_service = AdvancedAIAgentService()