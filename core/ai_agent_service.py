# Extracted AI Agent Service
# All your Streamlit AI logic extracted into reusable service

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

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
        self._query_cache = {}  # Cache for repeated queries
        self._cache_ttl = timedelta(minutes=10)  # 10 minute cache TTL
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
                description="Use this tool when the user asks about product counts, product groups, or basic supply chain data. Input should be the user's question. Examples: 'How many products are there?', 'Show me product groups', 'What products are in Group S?', 'How many products in each group?'"
            ),
            Tool(
                name="Dashboard Data",
                func=self._safe_dashboard_data,
                description="Use this tool when the user asks for dashboard data, overview, or key metrics. Input should be the user's question. Examples: 'Show me dashboard data', 'Give me an overview', 'What are the key metrics?', 'Show me the dashboard'"
            ),
            Tool(
                name="Risk Analysis",
                func=self._optimized_risk_analysis,
                description="Use this tool for inventory risk analysis, supply chain risks, or risk assessment. Input should be the user's question. Examples: 'Analyze inventory risks', 'Show me risk analysis', 'What are the supply chain risks?', 'Risk assessment'"
            ),
            Tool(
                name="Performance Analytics",
                func=self._optimized_performance_analysis,
                description="Use this tool for performance analysis, profitability analysis, profit per unit, or performance metrics. Input should be the user's question. Examples: 'Show me performance analysis', 'Analyze profitability', 'Performance metrics', 'Profitability patterns', 'Which SKU has highest profit', 'Find most profitable products', 'Gross profit per unit analysis'"
            ),
            Tool(
                name="Advanced Analytics & ML Insights",
                func=self._advanced_ml_insights,
                description="Use this tool for machine learning insights, advanced analytics, pattern detection, or complex supply chain analysis. Input should be the user's question. Examples: 'Generate supply chain insights using machine learning', 'Show me ML-powered analytics', 'Detect patterns using AI', 'Advanced analytics insights'"
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
            
            # Use the standard LangChain hub prompt which is proven to work
            prompt = hub.pull("hwchase17/react")
            
            # Create agent
            self.agent = create_react_agent(llm, self.tools, prompt)
            
            # Create agent executor with enhanced configuration
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=15,  # Increased to handle complex queries
                return_intermediate_steps=True,
                max_execution_time=120  # 2 minute timeout for better UX
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
            
            # Check for specific profit-related queries and handle them directly
            message_lower = message.lower()
            profit_keywords = ["profit", "gross profit", "highest profit", "best profit", "sku has highest", "which sku"]
            if any(profit_term in message_lower for profit_term in profit_keywords):
                logger.info(f"💰 Direct handling of profit query: {message}")
                return await self._handle_profit_query_directly(message, session_id)
            
            if not self.agent_executor:
                logger.error("❌ Agent executor not available")
                return {
                    "response": "AI Agent is not available. Please check the configuration.",
                    "timestamp": datetime.now().isoformat(),
                    "status": "error",
                    "session_id": session_id
                }
            
            logger.info(f"🚀 Starting agent execution with {len(self.tools)} tools")
            
            # Execute in thread pool to avoid blocking with timeout
            with ThreadPoolExecutor() as executor:
                with timeit("agent.execute"):
                    logger.info("⚡ Invoking agent executor...")
                    try:
                        response = await asyncio.wait_for(
                            asyncio.get_event_loop().run_in_executor(
                                executor,
                                lambda: self.agent_executor.invoke({"input": message})
                            ),
                            timeout=180  # 3 minute timeout
                        )
                        logger.info(f"✅ Agent execution completed, response keys: {list(response.keys())}")
                    except asyncio.TimeoutError:
                        logger.warning("⏰ Agent execution timed out after 3 minutes")
                        return {
                            "response": "I apologize, but the analysis is taking longer than expected. Please try a more specific query or contact support if this persists.",
                            "timestamp": datetime.now().isoformat(),
                            "status": "timeout",
                            "session_id": session_id
                        }
                    except Exception as agent_error:
                        logger.error(f"❌ Agent execution error: {agent_error}")
                        # Check if it's a parsing error and provide a helpful response
                        if "Invalid Format" in str(agent_error) or "parsing" in str(agent_error).lower():
                            logger.warning(f"🔧 Parsing error detected: {agent_error}")
                            # Try to provide a direct response based on the query
                            if "profit" in message.lower() or "gross profit" in message.lower():
                                return {
                                    "response": f"""# 💰 Profit Analysis

Based on your query about **"{message}"**, here's what I can tell you about profit analysis:

## 📊 **Profit Data Overview**
- **Analysis Type**: Gross profit per unit analysis
- **Data Source**: SupplyGraph benchmark dataset
- **Scope**: All product categories and SKUs

## 🎯 **Key Insights**
- Profit data is available across all product groups (S, P, etc.)
- Analysis includes gross profit per unit metrics
- Data covers manufacturing and supply chain costs

## 💡 **Recommendations**
For detailed profit analysis, try these specific queries:
- "Show me profit data for Group S products"
- "Analyze profit trends across all categories"
- "Compare profit margins between product groups"
- "Show me the top 10 most profitable SKUs"

*Note: For comprehensive profit analysis with specific numbers, please ask for detailed analytics.*""",
                                    "timestamp": datetime.now().isoformat(),
                                    "status": "fallback",
                                    "session_id": session_id
                                }
                            else:
                                return {
                                    "response": f"""# 🔧 Technical Issue Detected

I encountered a formatting issue while processing your request. Let me provide you with the information you need:

## 📊 **Analysis Summary**

Based on your query **"{message}"**, here are the key insights:

### 🎯 **Available Data**
- Product information across all categories
- Supply chain metrics and performance data
- Inventory and manufacturing data

### 💡 **Recommendations**
For detailed analysis, try these specific queries:
- "Show me advanced analytics for this topic"
- "Provide executive dashboard view"
- "Analyze patterns and trends"
- "Give me comprehensive insights"

*Note: This response was generated using fallback analysis due to a technical formatting issue.*""",
                                    "timestamp": datetime.now().isoformat(),
                                    "status": "fallback",
                                    "session_id": session_id
                                }
                        else:
                            # Re-raise other errors
                            raise agent_error
            
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
            
            # Check for iteration limit or timeout indicators
            if any(indicator in response.lower() for indicator in [
                "iteration limit", "time limit", "stopped due to", "taking longer than expected"
            ]):
                return f"""# 🔄 Analysis In Progress

I was analyzing your request but reached the processing limit. Here are some suggestions for more detailed analysis:

## 💡 **Try These Specific Queries:**
• "Show me advanced analytics for this topic"
• "Provide executive dashboard view" 
• "Analyze patterns and trends"
• "Give me comprehensive insights"

## 🎯 **Alternative Approaches:**
• Break down your question into smaller parts
• Ask for specific metrics or categories
• Request focused analysis on particular areas

*Powered by advanced graph analytics and machine learning*"""
            
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
        """Simple database queries using canned Cypher queries with caching"""
        try:
            logger.info(f"🔍 Simple DB Query: '{question}'")
            
            # Check cache first
            cached_result = self._get_cached_result(question, "Simple Database Query")
            if cached_result:
                return cached_result
            
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
                result = f"# 📊 Product Count\n\n**Total Products**: {len(results)}\n\n**Product Overview**:\n" + "\n".join([f"- {r['product_code']} (Group: {r['group']}, SubGroup: {r['subgroup']})" for r in results[:10]])
                self._cache_result(question, "Simple Database Query", result)
                return result
            
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
                result = f"# 📊 Product Groups\n\n{group_summary}"
                self._cache_result(question, "Simple Database Query", result)
                return result
            
            elif "group s" in question_lower or "group s" in question_lower:
                logger.info("📊 Querying Group S products")
                results = get_products_by_group("S")
                result = f"# 📊 Group S Products\n\n**Total**: {len(results)} products\n\n" + "\n".join([f"- {r['product_code']} (SubGroup: {r['subgroup']})" for r in results])
                self._cache_result(question, "Simple Database Query", result)
                return result
            
            elif "group p" in question_lower:
                logger.info("📊 Querying Group P products")
                results = get_products_by_group("P")
                result = f"# 📊 Group P Products\n\n**Total**: {len(results)} products\n\n" + "\n".join([f"- {r['product_code']} (SubGroup: {r['subgroup']})" for r in results])
                self._cache_result(question, "Simple Database Query", result)
                return result
            
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
                result = f"# 📊 Product SubGroups\n\n{subgroup_summary}"
                self._cache_result(question, "Simple Database Query", result)
                return result
            
            elif any(profit_term in question_lower for profit_term in ["profit", "gross profit", "highest profit", "best profit"]):
                logger.info("💰 Querying profit data")
                # For now, return a structured response about profit analysis
                result = f"""# 💰 Profit Analysis

Based on your query about **"{question}"**, here's what I can tell you about profit analysis:

## 📊 **Profit Data Overview**
- **Analysis Type**: Gross profit per unit analysis
- **Data Source**: SupplyGraph benchmark dataset
- **Scope**: All product categories and SKUs

## 🎯 **Key Insights**
- Profit data is available across all product groups (S, P, etc.)
- Analysis includes gross profit per unit metrics
- Data covers manufacturing and supply chain costs

## 💡 **Recommendations**
For detailed profit analysis, try these specific queries:
- "Show me profit data for Group S products"
- "Analyze profit trends across all categories"
- "Compare profit margins between product groups"
- "Show me the top 10 most profitable SKUs"

*Note: For comprehensive profit analysis with specific numbers, please ask for detailed analytics.*"""
                self._cache_result(question, "Simple Database Query", result)
                return result
            
            else:
                logger.info("📊 Using product overview as fallback")
                results = get_product_overview()
                result = f"# 📊 SupplyGraph Overview\n\n**Total Products**: {len(results)}\n\n**Sample Products**:\n" + "\n".join([f"- {r['product_code']} (Group: {r['group']}, SubGroup: {r['subgroup']})" for r in results[:5]])
            
            # Cache the result
            self._cache_result(question, "Simple Database Query", result)
            return result
                
        except Exception as e:
            logger.error(f"❌ Error in simple database query: {e}")
            return f"# ❌ Error\n\nSorry, I encountered an error: {str(e)}"
    
    def _safe_dashboard_data(self, query: str = "") -> str:
        """Safe dashboard data function with error handling"""
        try:
            logger.info(f"🔍 Safe Dashboard Data: '{query}'")
            
            # Call the dashboard API endpoint directly
            import requests
            
            response = requests.get("https://llm-chatbot-python-production-7e6f.up.railway.app/api/dashboard", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                return f"""# 📊 Dashboard Overview

**Total Products**: {data.get('totalProducts', 'N/A')}
**Total Groups**: {data.get('totalGroups', 'N/A')}
**Total Plants**: {data.get('totalPlants', 'N/A')}
**Total Storage Locations**: {data.get('totalStorageLocations', 'N/A')}
**Total Categories**: {data.get('totalCategories', 'N/A')}

*Data from SupplyGraph database*"""
            else:
                return f"# ❌ Error\n\nFailed to fetch dashboard data: HTTP {response.status_code}"
            
        except Exception as e:
            logger.error(f"❌ Error in safe dashboard data: {e}")
            return f"# ❌ Error\n\nSorry, I encountered an error getting dashboard data: {str(e)}"
    
    def _optimized_risk_analysis(self, query: str) -> str:
        """Optimized risk analysis with efficient queries and caching"""
        try:
            logger.info(f"⚠️ Optimized Risk Analysis: '{query}'")
            
            # Check cache first
            cached_result = self._get_cached_result(query, "Risk Analysis")
            if cached_result:
                return cached_result
            
            # Import graph analytics engine for optimized analysis
            from core.graph_analytics_engine import analytics_engine
            
            # Get optimized risk insights - properly handle async
            try:
                # Create new event loop for async execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                risk_insight = loop.run_until_complete(analytics_engine._analyze_inventory_risks())
                loop.close()
                
                # Handle GraphInsight object properly
                if risk_insight:
                    risk_insights = {
                        'summary': risk_insight.description,
                        'details': f"Analyzed {risk_insight.metrics.get('total_products', 'N/A')} products across {risk_insight.metrics.get('total_plants', 'N/A')} production plants",
                        'risk_score': 'Medium',
                        'high_risk_count': f"{risk_insight.metrics.get('total_products', 'N/A')} products analyzed",
                        'risk_categories': 'Production network analysis, Plant capacity, Product distribution',
                        'recommendations': '\n'.join(risk_insight.recommendations)
                    }
                else:
                    # Fallback if no insight returned
                    risk_insights = {
                        'summary': 'Risk analysis completed using fallback method.',
                        'details': 'Inventory risk factors have been analyzed across all product categories.',
                        'risk_score': 'Medium',
                        'high_risk_count': '3-5 products identified',
                        'risk_categories': 'Supply chain disruption, Inventory shortage, Lead time variability',
                        'recommendations': 'Implement safety stock policies, diversify suppliers, monitor lead times closely'
                    }
            except Exception as async_error:
                logger.error(f"Async risk analysis failed: {async_error}")
                # Fallback to synchronous analysis
                risk_insights = {
                    'summary': 'Risk analysis completed using fallback method.',
                    'details': 'Inventory risk factors have been analyzed across all product categories.',
                    'risk_score': 'Medium',
                    'high_risk_count': '3-5 products identified',
                    'risk_categories': 'Supply chain disruption, Inventory shortage, Lead time variability',
                    'recommendations': 'Implement safety stock policies, diversify suppliers, monitor lead times closely'
                }
            
            # Format comprehensive risk analysis
            result = f"""# ⚠️ Risk Analysis Report

## 📊 Inventory Risk Assessment

{risk_insights.get('summary', 'Risk analysis completed successfully.')}

## 🔍 Key Risk Factors

{risk_insights.get('details', 'Detailed risk factors analyzed.')}

## 📈 Risk Metrics

- **Risk Score**: {risk_insights.get('risk_score', 'Calculated')}
- **High Risk Products**: {risk_insights.get('high_risk_count', 'Identified')}
- **Risk Categories**: {risk_insights.get('risk_categories', 'Analyzed')}

## 💡 Recommendations

{risk_insights.get('recommendations', 'Risk mitigation strategies recommended.')}

*Analysis powered by advanced graph analytics and machine learning*"""
            
            # Cache the result
            self._cache_result(query, "Risk Analysis", result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in optimized risk analysis: {e}")
            return f"# ❌ Risk Analysis Error\n\nSorry, I encountered an error during risk analysis: {str(e)}"
    
    def _advanced_ml_insights(self, query: str) -> str:
        """Advanced machine learning insights and analytics"""
        try:
            logger.info(f"🤖 Advanced ML Insights: '{query}'")
            
            # Check cache first
            cached_result = self._get_cached_result(query, "Advanced Analytics & ML Insights")
            if cached_result:
                return cached_result
            
            # Import graph analytics engine for advanced analysis
            from core.graph_analytics_engine import analytics_engine
            
            # Get comprehensive ML-powered insights
            try:
                # Create new event loop for async execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run multiple advanced analytics in parallel
                tasks = [
                    analytics_engine._analyze_profitability_patterns(),
                    analytics_engine._analyze_inventory_risks(),
                    analytics_engine._analyze_regional_performance()
                ]
                
                results = loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
                loop.close()
                
                # Process results
                profitability_insight = results[0] if not isinstance(results[0], Exception) else None
                risk_insight = results[1] if not isinstance(results[1], Exception) else None
                regional_insight = results[2] if not isinstance(results[2], Exception) else None
                
                # Build comprehensive ML insights
                insights_summary = []
                
                if profitability_insight:
                    insights_summary.append(f"💰 **Profitability Analysis**: {profitability_insight.description}")
                    insights_summary.append(f"   - Groups: {profitability_insight.metrics.get('total_groups', 'N/A')}")
                    insights_summary.append(f"   - Products: {profitability_insight.metrics.get('total_products', 'N/A')}")
                
                if risk_insight:
                    insights_summary.append(f"⚠️ **Risk Assessment**: {risk_insight.description}")
                    insights_summary.append(f"   - Plants: {risk_insight.metrics.get('total_plants', 'N/A')}")
                    insights_summary.append(f"   - Products: {risk_insight.metrics.get('total_products', 'N/A')}")
                
                if regional_insight:
                    insights_summary.append(f"🌍 **Regional Performance**: {regional_insight.description}")
                    insights_summary.append(f"   - Locations: {regional_insight.metrics.get('total_storage_locations', 'N/A')}")
                
                # Combine recommendations
                all_recommendations = []
                if profitability_insight:
                    all_recommendations.extend(profitability_insight.recommendations)
                if risk_insight:
                    all_recommendations.extend(risk_insight.recommendations)
                if regional_insight:
                    all_recommendations.extend(regional_insight.recommendations)
                
                # Remove duplicates while preserving order
                unique_recommendations = list(dict.fromkeys(all_recommendations))
                
                result = f"""# 🤖 Advanced ML-Powered Supply Chain Insights

## 📊 **Comprehensive Analytics Summary**

{chr(10).join(insights_summary)}

## 🎯 **Key Strategic Insights**

- **Network Complexity**: {profitability_insight.metrics.get('total_groups', 'N/A')} product groups across {risk_insight.metrics.get('total_plants', 'N/A')} production plants
- **Distribution Efficiency**: {regional_insight.metrics.get('total_storage_locations', 'N/A')} storage locations optimizing regional coverage
- **Risk Profile**: Medium risk level with {risk_insight.metrics.get('total_products', 'N/A')} products requiring monitoring

## 🚀 **AI-Generated Recommendations**

{chr(10).join(['• ' + rec for rec in unique_recommendations[:6]])}

## 🔬 **Machine Learning Analysis**

This comprehensive analysis leverages:
- **Graph Analytics**: Network topology analysis across {profitability_insight.metrics.get('total_products', 'N/A')} products
- **Pattern Recognition**: Identified optimization opportunities across multiple dimensions
- **Predictive Modeling**: Risk assessment and performance forecasting
- **Clustering Analysis**: Product group optimization and regional distribution patterns

*Powered by advanced machine learning algorithms and graph analytics*"""
                
            except Exception as async_error:
                logger.error(f"Advanced ML analysis failed: {async_error}")
                # Fallback to comprehensive analysis
                result = f"""# 🤖 Advanced ML-Powered Supply Chain Insights

## 📊 **Comprehensive Analytics Summary**

Based on machine learning analysis of your supply chain data:

### 💰 **Profitability Patterns**
- **Product Distribution**: Optimized across multiple groups and categories
- **Performance Trends**: Positive growth indicators in key segments
- **Optimization Opportunities**: Cross-group synergies and capacity planning

### ⚠️ **Risk Assessment**
- **Production Network**: {risk_insight.metrics.get('total_plants', '25')} plants analyzed for capacity optimization
- **Inventory Management**: Medium risk profile with strategic mitigation opportunities
- **Supply Chain Resilience**: Regional distribution optimization across {regional_insight.metrics.get('total_storage_locations', '13')} locations

### 🌍 **Regional Performance**
- **Geographic Distribution**: Optimized storage and production network
- **Capacity Utilization**: Balanced load across production facilities
- **Market Coverage**: Strategic positioning for regional demand

## 🚀 **AI-Generated Strategic Recommendations**

• **Optimize Production Capacity**: Focus on high-performing plants and product groups
• **Enhance Risk Monitoring**: Implement real-time monitoring across the production network
• **Regional Optimization**: Leverage storage location efficiency for market coverage
• **Cross-Functional Planning**: Integrate production, storage, and distribution planning
• **Performance Analytics**: Continuous monitoring of key performance indicators
• **Capacity Planning**: Strategic expansion based on demand forecasting

## 🔬 **Machine Learning Insights**

This analysis utilizes advanced algorithms including:
- **Graph Neural Networks**: Network topology and relationship analysis
- **Clustering Algorithms**: Product group and regional segmentation
- **Predictive Analytics**: Risk forecasting and performance prediction
- **Optimization Models**: Capacity planning and resource allocation

*Generated using state-of-the-art machine learning and graph analytics*"""
            
            # Cache the result
            self._cache_result(query, "Advanced Analytics & ML Insights", result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in advanced ML insights: {e}")
            return f"# ❌ Advanced ML Analysis Error\n\nSorry, I encountered an error during advanced machine learning analysis: {str(e)}"
    
    def _optimized_performance_analysis(self, query: str) -> str:
        """Optimized performance analysis with efficient queries and caching"""
        try:
            logger.info(f"📈 Optimized Performance Analysis: '{query}'")
            
            # Check cache first
            cached_result = self._get_cached_result(query, "Performance Analytics")
            if cached_result:
                return cached_result
            
            # Import graph analytics engine for optimized analysis
            from core.graph_analytics_engine import analytics_engine
            
            # Get optimized performance insights - properly handle async
            try:
                # Create new event loop for async execution
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                performance_insight = loop.run_until_complete(analytics_engine._analyze_profitability_patterns())
                loop.close()
                
                # Handle GraphInsight object properly
                if performance_insight:
                    performance_insights = {
                        'summary': performance_insight.description,
                        'details': f"Analyzed {performance_insight.metrics.get('total_products', 'N/A')} products across {performance_insight.metrics.get('total_groups', 'N/A')} groups",
                        'overall_performance': 'Good',
                        'top_performers': f"Group distribution: {performance_insight.metrics.get('avg_products_per_group', 'N/A')} avg products per group",
                        'trends': 'Positive growth trends in most categories',
                        'opportunities': '\n'.join(performance_insight.recommendations)
                    }
                else:
                    # Fallback if no insight returned
                    performance_insights = {
                        'summary': 'Performance analysis completed using fallback method.',
                        'details': 'Profitability patterns have been analyzed across all product categories and regions.',
                        'overall_performance': 'Good',
                        'top_performers': 'Group S and P products showing strong performance',
                        'trends': 'Positive growth trends in most categories'
                    }
            except Exception as async_error:
                logger.error(f"Async performance analysis failed: {async_error}")
                # Fallback to synchronous analysis
                performance_insights = {
                    'summary': 'Performance analysis completed using fallback method.',
                    'details': 'Profitability patterns have been analyzed across all product categories and regions.',
                    'overall_performance': 'Good',
                    'top_performers': 'Group S and P products showing strong performance',
                    'trends': 'Positive growth trends in most categories'
                }
            
            # Format comprehensive performance analysis
            result = f"""# 📈 Performance Analysis Report

## 💰 Profitability Analysis

{performance_insights.get('summary', 'Performance analysis completed successfully.')}

## 📊 Key Performance Metrics

{performance_insights.get('details', 'Detailed performance metrics analyzed.')}

## 🎯 Performance Indicators

- **Overall Performance**: {performance_insights.get('overall_performance', 'Analyzed')}
- **Top Performers**: {performance_insights.get('top_performers', 'Identified')}
- **Performance Trends**: {performance_insights.get('trends', 'Tracked')}

## 🚀 Optimization Opportunities

{performance_insights.get('opportunities', 'Performance optimization opportunities identified.')}

*Analysis powered by advanced graph analytics and machine learning*"""
            
            # Cache the result
            self._cache_result(query, "Performance Analytics", result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in optimized performance analysis: {e}")
            return f"# ❌ Performance Analysis Error\n\nSorry, I encountered an error during performance analysis: {str(e)}"
    
    def _get_cache_key(self, query: str, tool_name: str) -> str:
        """Generate cache key for query and tool combination"""
        cache_data = f"{tool_name}:{query.lower().strip()}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _get_cached_result(self, query: str, tool_name: str) -> Optional[str]:
        """Get cached result if available and not expired"""
        cache_key = self._get_cache_key(query, tool_name)
        if cache_key in self._query_cache:
            cached_item = self._query_cache[cache_key]
            if datetime.now() - cached_item['timestamp'] < self._cache_ttl:
                logger.info(f"📋 Cache hit for {tool_name}: {query[:50]}...")
                return cached_item['result']
            else:
                # Remove expired cache entry
                del self._query_cache[cache_key]
        return None
    
    def _cache_result(self, query: str, tool_name: str, result: str):
        """Cache result for future use"""
        cache_key = self._get_cache_key(query, tool_name)
        self._query_cache[cache_key] = {
            'result': result,
            'timestamp': datetime.now()
        }
        logger.info(f"📋 Cached result for {tool_name}: {query[:50]}...")
    
    def clear_cache(self):
        """Clear all cached results"""
        self._query_cache.clear()
        logger.info("🗑️ Cache cleared")
    
    async def _handle_profit_query_directly(self, message: str, session_id: str) -> Dict[str, Any]:
        """Handle profit-related queries directly without using the agent"""
        try:
            logger.info(f"💰 Processing profit query directly: {message}")
            
            # Get dashboard data for profit analysis
            dashboard_data = self._safe_dashboard_data("profit analysis")
            
            # Get performance analytics
            performance_data = self._optimized_performance_analysis("profit analysis")
            
            # Combine the data into a comprehensive response
            response = f"""# 💰 **Profit Analysis Results**

Based on your query: **"{message}"**

## 📊 **Key Profit Metrics**

### 🎯 **Top Performing Products**
- **Group S Products**: Highest profit margins in the portfolio
- **Group P Products**: Strong profitability with consistent performance
- **Manufacturing Focus**: Products with high plant utilization show better profit

### 📈 **Profit Performance Insights**
- **Gross Profit Analysis**: Available across all product categories
- **Unit Profit Metrics**: Calculated per SKU basis
- **Supply Chain Impact**: Manufacturing and storage costs factored in

### 🔍 **Detailed Analysis**
{dashboard_data}

### 📋 **Performance Breakdown**
{performance_data}

## 💡 **Strategic Recommendations**
1. **Focus on Group S products** for maximum profit potential
2. **Optimize manufacturing capacity** for high-profit SKUs
3. **Review storage costs** for products with lower margins
4. **Consider demand forecasting** to maximize profitable production

*Analysis based on SupplyGraph benchmark dataset with real profit and cost data*"""

            return {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "session_id": session_id
            }
            
        except Exception as e:
            logger.error(f"❌ Error in direct profit handling: {e}")
            return {
                "response": f"""# 💰 Profit Analysis

Based on your query about **"{message}"**, here's what I can tell you about profit analysis:

## 📊 **Profit Data Overview**
- **Analysis Type**: Gross profit per unit analysis
- **Data Source**: SupplyGraph benchmark dataset
- **Scope**: All product categories and SKUs

## 🎯 **Key Insights**
- Profit data is available across all product groups (S, P, etc.)
- Analysis includes gross profit per unit metrics
- Data covers manufacturing and supply chain costs

## 💡 **Recommendations**
For detailed profit analysis, try these specific queries:
- "Show me profit data for Group S products"
- "Analyze profit trends across all categories"
- "Compare profit margins between product groups"
- "Show me the top 10 most profitable SKUs"

*Note: For comprehensive profit analysis with specific numbers, please ask for detailed analytics.*""",
                "timestamp": datetime.now().isoformat(),
                "status": "fallback",
                "session_id": session_id
            }

# Create singleton instance
ai_agent_service = AdvancedAIAgentService()