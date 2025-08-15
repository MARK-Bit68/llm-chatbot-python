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
                name="Simple Database Query",
                func=self._simple_database_query,
                description="Simple database queries for basic supply chain questions. Input: simple questions like 'How many products are there?' or 'Show me product groups'"
            ),
            Tool(
                name="Dashboard Data",
                func=self._safe_dashboard_data,
                description="Get comprehensive dashboard data including product overview and statistics."
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
            
            # Simplified agent prompt to prevent loops
            agent_prompt = PromptTemplate.from_template("""
You are a helpful supply chain AI assistant. You have access to the following tools:
{tools}

RULES:
1. For simple data questions like "How many products are there?" or "Show me product groups", use the "Simple Database Query" tool
2. For comprehensive dashboard data or overview requests, use the "Dashboard Data" tool
3. For greetings or simple questions, respond directly with "Final Answer:"
4. Use proper ReAct format: "Action:" then tool name, then "Action Input:" then your query
5. For direct responses: "Final Answer:" then your response
6. Don't loop or repeat actions
7. If a tool fails, provide a helpful response

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
                max_iterations=5,  # Reduced to prevent loops
                return_intermediate_steps=True
            )
            
            logger.info(f"✅ Agent created with {len(self.tools)} tools: {[tool.name for tool in self.tools]}")
            
            logger.info("✅ AI Agent created successfully")
            
        except Exception as e:
            logger.error(f"❌ Error creating AI agent: {e}")
            self.agent_executor = None
    
    async def chat_async(self, message: str, session_id: str = "default") -> Dict[str, Any]:
        """Async chat with AI agent"""
        try:
            logger.info(f"🔍 Chat request: '{message[:50]}...' (session: {session_id})")
            record_event("chat.request", {"message_preview": message[:100], "session_id": session_id})
            
            if not self.agent_executor:
                logger.error("❌ Agent executor not available")
                return {
                    "response": "AI Agent is not available. Please check the configuration.",
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "session_id": session_id
                }
            
            logger.info(f"🚀 Starting agent execution with {len(self.tools)} tools")
            
            # Execute in thread pool to avoid blocking
            with ThreadPoolExecutor() as executor:
                with timeit("agent.execute"):
                    logger.info("⚡ Invoking agent executor...")
                    response = await asyncio.get_event_loop().run_in_executor(
                        executor,
                        lambda: self.agent_executor.invoke({"input": message})
                    )
                    logger.info(f"✅ Agent execution completed, response keys: {list(response.keys())}")
            
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
    
    def _simple_database_query(self, question: str) -> str:
        """Simple database queries using canned Cypher queries"""
        try:
            logger.info(f"🔍 Simple DB Query: '{question}'")
            
            # Import the canned query functions
            from solutions.tools.cypher_supplygraph import (
                get_product_overview, get_products_by_group, get_products_by_subgroup,
                get_products_by_plant, get_products_by_storage, get_product_details
            )
            
            question_lower = question.lower()
            
            # Simple pattern matching for common queries
            if "how many products" in question_lower or "total products" in question_lower:
                logger.info("📊 Querying total product count")
                results = get_product_overview()
                return f"# 📊 Product Count\n\n**Total Products**: {len(results)}\n\n**Product Overview**:\n" + "\n".join([f"- {r['product_code']} (Group: {r['group']}, SubGroup: {r['subgroup']})" for r in results[:10]])
            
            elif "product groups" in question_lower or "groups" in question_lower:
                logger.info("📊 Querying product groups")
                results = get_product_overview()
                groups = {}
                for r in results:
                    group = r['group']
                    if group not in groups:
                        groups[group] = []
                    groups[group].append(r['product_code'])
                
                group_summary = "\n".join([f"- **Group {g}**: {len(products)} products" for g, products in groups.items()])
                return f"# 📊 Product Groups\n\n{group_summary}"
            
            elif "group s" in question_lower or "group s" in question_lower:
                logger.info("📊 Querying Group S products")
                results = get_products_by_group("S")
                return f"# 📊 Group S Products\n\n**Total**: {len(results)} products\n\n" + "\n".join([f"- {r['product_code']} (SubGroup: {r['subgroup']})" for r in results])
            
            elif "group p" in question_lower:
                logger.info("📊 Querying Group P products")
                results = get_products_by_group("P")
                return f"# 📊 Group P Products\n\n**Total**: {len(results)} products\n\n" + "\n".join([f"- {r['product_code']} (SubGroup: {r['subgroup']})" for r in results])
            
            elif "subgroup" in question_lower:
                logger.info("📊 Querying subgroups")
                results = get_product_overview()
                subgroups = {}
                for r in results:
                    subgroup = r['subgroup']
                    if subgroup not in subgroups:
                        subgroups[subgroup] = []
                    subgroups[subgroup].append(r['product_code'])
                
                subgroup_summary = "\n".join([f"- **{sg}**: {len(products)} products" for sg, products in subgroups.items()])
                return f"# 📊 Product SubGroups\n\n{subgroup_summary}"
            
            else:
                logger.info("📊 Using product overview as fallback")
                results = get_product_overview()
                return f"# 📊 SupplyGraph Overview\n\n**Total Products**: {len(results)}\n\n**Sample Products**:\n" + "\n".join([f"- {r['product_code']} (Group: {r['group']}, SubGroup: {r['subgroup']})" for r in results[:5]])
                
        except Exception as e:
            logger.error(f"❌ Error in simple database query: {e}")
            return f"# ❌ Error\n\nSorry, I encountered an error: {str(e)}"
    
    def _safe_dashboard_data(self, query: str = "") -> str:
        """Safe dashboard data function with error handling"""
        try:
            logger.info(f"🔍 Safe Dashboard Data: '{query}'")
            
            # Import the dashboard function
            from solutions.tools.cypher_supplygraph import get_dashboard_data
            
            # Get dashboard data
            dashboard_data = get_dashboard_data()
            
            return f"# 📊 Dashboard Data\n\n{dashboard_data}"
            
        except Exception as e:
            logger.error(f"❌ Error in safe dashboard data: {e}")
            return f"# ❌ Error\n\nSorry, I encountered an error getting dashboard data: {str(e)}"

# Create singleton instance
ai_agent_service = AdvancedAIAgentService()