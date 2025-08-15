# Advanced FastAPI Server with Extracted AI Logic
# World-class graph analytics and AI capabilities

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import json
import os
from datetime import datetime
import logging
from contextlib import asynccontextmanager

# Import our extracted services
from core.graph_analytics_engine import analytics_engine, GraphInsight
from core.ai_agent_service import ai_agent_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatMessage(BaseModel):
    message: str = Field(..., description="The user's message")
    session_id: str = Field(default="default", description="Session identifier for conversation memory")

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    status: str
    session_id: str
    intermediate_steps: Optional[int] = None

class AnalyticsRequest(BaseModel):
    analysis_type: str = Field(..., description="Type of analysis: 'overview', 'patterns', 'clusters', 'risks', 'profitability', 'regional'")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters for analysis")

class GraphOverview(BaseModel):
    node_statistics: Dict[str, Any]
    relationship_statistics: Dict[str, Any]
    advanced_metrics: Dict[str, Any]
    timestamp: str

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Advanced FMCG Analytics API")
    
    # Don't block startup with service initialization
    # Services will be initialized on-demand when needed
    logger.info("✅ FastAPI server ready - services will initialize on-demand")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Advanced FMCG Analytics API")

# Create FastAPI app
app = FastAPI(
    title="Advanced FMCG Supply Chain Analytics API",
    description="""
    🚀 **World-Class Graph Analytics and AI Platform**
    
    Advanced analytics platform for FMCG supply chain management featuring:
    
    ## 🔬 **Advanced Analytics**
    - Graph machine learning and pattern detection
    - Supply chain risk analysis and optimization
    - Profitability modeling and forecasting
    - Regional performance analysis
    
    ## 🤖 **AI Agent Capabilities**
    - Natural language query processing
    - Executive dashboard generation
    - Multi-turn conversations with memory
    - Advanced reasoning and insights
    
    ## 📊 **Graph Database Integration**
    - Real-time Neo4j analytics
    - NetworkX graph algorithms
    - Advanced centrality and clustering analysis
    - Performance optimization
    
    Built with FastAPI, Neo4j, NetworkX, scikit-learn, and advanced ML libraries.
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",     # React dev
        "http://localhost:8501",     # Streamlit
        "https://*.railway.app",     # Railway deployments
        "https://*.vercel.app",      # Vercel deployments
        "https://*.netlify.app",     # Netlify deployments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Simple startup check endpoint
@app.get("/startup", summary="Startup Check")
async def startup_check():
    """Simple startup check - returns immediately when server is ready"""
    return {"status": "ready", "timestamp": datetime.now().isoformat()}

# Health check endpoint
@app.get("/health", summary="Comprehensive Health Check")
async def health_check():
    """Comprehensive health check of all services"""
    try:
        analytics_health = analytics_engine.health_check()
    except Exception as e:
        analytics_health = {"overall_status": "unavailable", "error": str(e)}
    
    try:
        agent_status = ai_agent_service.get_agent_status()
    except Exception as e:
        agent_status = {"agent_available": False, "error": str(e)}
    
    # Server is healthy if it can respond, even if backend services are unavailable
    overall_status = "healthy"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "services": {
            "analytics_engine": analytics_health,
            "ai_agent": agent_status
        }
    }

# Chat endpoints
@app.post("/api/chat", response_model=ChatResponse, summary="Chat with AI Agent")
async def chat_endpoint(chat_message: ChatMessage):
    """
    Chat with advanced AI agent featuring:
    - Natural language processing
    - Graph-aware responses
    - Executive dashboard generation
    - Multi-turn conversation memory
    """
    try:
        response = await ai_agent_service.chat_async(
            message=chat_message.message,
            session_id=chat_message.session_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/stream", summary="Streaming Chat Response")
async def chat_stream_endpoint(chat_message: ChatMessage):
    """Stream chat response in real-time"""
    async def generate_response():
        try:
            # Simulate streaming response (can be enhanced with actual streaming)
            response = await ai_agent_service.chat_async(
                message=chat_message.message,
                session_id=chat_message.session_id
            )
            
            # Stream response in chunks
            response_text = response["response"]
            words = response_text.split()
            
            for i, word in enumerate(words):
                chunk = {
                    "chunk": word + " ",
                    "index": i,
                    "is_final": i == len(words) - 1
                }
                yield f"data: {json.dumps(chunk)}\n\n"
                await asyncio.sleep(0.05)  # Small delay for streaming effect
                
        except Exception as e:
            error_chunk = {
                "error": str(e),
                "is_final": True
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.delete("/api/chat/session/{session_id}", summary="Reset Chat Session")
async def reset_session_endpoint(session_id: str):
    """Reset conversation memory for a session"""
    try:
        ai_agent_service.reset_session(session_id)
        return {
            "message": f"Session {session_id} reset successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Session reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced Analytics endpoints
@app.get("/api/analytics/overview", response_model=GraphOverview, summary="Graph Overview")
async def graph_overview_endpoint():
    """
    Get comprehensive graph overview with advanced metrics:
    - Node and relationship statistics
    - Graph density and connectivity
    - Centrality measures
    - Clustering coefficients
    """
    try:
        overview = await analytics_engine.get_graph_overview()
        return GraphOverview(**overview)
    except Exception as e:
        logger.error(f"Graph overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/graph/overview", summary="Graph Overview (React Frontend)")
async def get_graph_overview_react():
    """Get graph overview for React frontend compatibility"""
    try:
        overview = await analytics_engine.get_graph_overview()
        return overview
    except Exception as e:
        logger.error(f"Graph overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/insights", summary="Advanced Supply Chain Insights")
async def supply_chain_insights_endpoint(background_tasks: BackgroundTasks):
    """
    Generate advanced supply chain insights using machine learning:
    - Product performance clustering
    - Inventory risk analysis
    - Profitability pattern detection
    - Regional performance analysis
    """
    try:
        insights = await analytics_engine.detect_supply_chain_patterns()
        
        # Convert insights to serializable format
        serialized_insights = []
        for insight in insights:
            serialized_insights.append({
                "insight_type": insight.insight_type,
                "title": insight.title,
                "description": insight.description,
                "metrics": insight.metrics,
                "visualization_data": insight.visualization_data,
                "recommendations": insight.recommendations,
                "confidence": insight.confidence,
                "timestamp": insight.timestamp.isoformat()
            })
        
        return {
            "insights": serialized_insights,
            "total_insights": len(serialized_insights),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Supply chain insights error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analytics/custom", summary="Custom Analytics Request")
async def custom_analytics_endpoint(request: AnalyticsRequest):
    """
    Execute custom analytics based on analysis type:
    - overview: Complete graph overview
    - patterns: Pattern detection analysis
    - clusters: Product clustering analysis
    - risks: Inventory risk assessment
    - profitability: Profit pattern analysis
    - regional: Regional performance analysis
    """
    try:
        if request.analysis_type == "overview":
            result = await analytics_engine.get_graph_overview()
        elif request.analysis_type in ["patterns", "clusters", "risks", "profitability", "regional"]:
            insights = await analytics_engine.detect_supply_chain_patterns()
            
            # Filter insights by type if specified
            if request.analysis_type == "clusters":
                insights = [i for i in insights if i.insight_type == "clustering"]
            elif request.analysis_type == "risks":
                insights = [i for i in insights if i.insight_type == "inventory_risk"]
            elif request.analysis_type == "profitability":
                insights = [i for i in insights if i.insight_type == "profitability"]
            elif request.analysis_type == "regional":
                insights = [i for i in insights if i.insight_type == "regional_performance"]
            
            # Serialize insights
            result = []
            for insight in insights:
                result.append({
                    "insight_type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description,
                    "metrics": insight.metrics,
                    "visualization_data": insight.visualization_data,
                    "recommendations": insight.recommendations,
                    "confidence": insight.confidence,
                    "timestamp": insight.timestamp.isoformat()
                })
        else:
            raise HTTPException(status_code=400, detail=f"Unknown analysis type: {request.analysis_type}")
        
        return {
            "analysis_type": request.analysis_type,
            "result": result,
            "parameters": request.parameters,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Custom analytics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Dashboard endpoint
@app.get("/api/dashboard", summary="Executive Dashboard Data")
async def dashboard_endpoint():
    """
    Get executive dashboard data combining:
    - Real-time graph statistics
    - Advanced analytics insights
    - Performance metrics
    - Key recommendations
    """
    try:
        # Get graph overview
        overview = await analytics_engine.get_graph_overview()
        
        # Get supply chain insights
        insights = await analytics_engine.detect_supply_chain_patterns()
        
        # Aggregate key metrics
        total_products = overview.get("node_statistics", {}).get("node_types", {}).get("Product", 0)
        total_groups = overview.get("node_statistics", {}).get("node_types", {}).get("Group", 0)
        total_plants = overview.get("node_statistics", {}).get("node_types", {}).get("Plant", 0)
        total_storage = overview.get("node_statistics", {}).get("node_types", {}).get("StorageLocation", 0)
        
        # Extract key recommendations
        all_recommendations = []
        for insight in insights:
            all_recommendations.extend(insight.recommendations)
        
        # Take top 5 recommendations
        top_recommendations = all_recommendations[:5] if all_recommendations else [
            "No specific recommendations available",
            "Run detailed analytics for insights"
        ]
        
        # Calculate performance score based on insights
        performance_score = 85.0  # Base score
        if insights:
            avg_confidence = sum(i.confidence for i in insights) / len(insights)
            performance_score = min(95.0, performance_score + (avg_confidence * 10))
        
        dashboard_data = {
            "totalProducts": total_products,
            "totalGroups": total_groups,
            "totalPlants": total_plants,
            "totalStorageLocations": total_storage,
            "totalCategories": len(overview.get("node_statistics", {}).get("node_types", {})),
            "performanceScore": f"{performance_score:.1f}%",
            "insights_generated": len(insights),
            "graph_density": overview.get("advanced_metrics", {}).get("density", 0),
            "recommendations": top_recommendations,
            "last_updated": datetime.now().isoformat(),
            "status": "success"
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Dashboard endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Graph Visualization endpoint
@app.get("/api/graph/visualization", summary="Graph Visualization Data")
async def graph_visualization_endpoint():
    """
    Get graph data for 3D visualization including:
    - Nodes (products, plants, storage locations)
    - Edges (relationships between nodes)
    - Revenue and profit data
    - Node properties and metadata
    """
    try:
        # Get graph overview for statistics
        overview = await analytics_engine.get_graph_overview()
        
        # Get detailed graph data from Neo4j
        from solutions.graph import get_graph
        graph = get_graph()
        
        if not graph:
            raise HTTPException(status_code=500, detail="Graph database connection unavailable")
        
        # Query nodes with basic information
        nodes_query = """
        MATCH (n)
        RETURN n.code as code,
               n.name as name,
               n.group as group,
               n.subgroup as subgroup,
               labels(n) as labels
        """
        
        nodes_result = graph.query(nodes_query)
        
        # Query relationships
        edges_query = """
        MATCH (a)-[r]->(b)
        WHERE a.code IS NOT NULL AND b.code IS NOT NULL
        RETURN a.code as source,
               b.code as target,
               type(r) as type
        LIMIT 100
        """
        
        edges_result = graph.query(edges_query)
        
        # Process nodes
        nodes = []
        node_types = {}
        
        for record in nodes_result:
            node = record.get('n', {})
            labels = record.get('labels', [])
            node_type = labels[0] if labels else 'Unknown'
            
            # Count node types
            if node_type not in node_types:
                node_types[node_type] = 0
            node_types[node_type] += 1
            
            # Create node object
            node_obj = {
                'id': record.get('code') or record.get('name') or str(hash(str(record))),
                'type': node_type,
                'name': record.get('name') or record.get('code'),
                'code': record.get('code'),
                'group': record.get('group'),
                'subgroup': record.get('subgroup'),
                'properties': record
            }
            
            nodes.append(node_obj)
        
        # Process edges
        edges = []
        for record in edges_result:
            edge_obj = {
                'source': record['source'],
                'target': record['target'],
                'type': record['type']
            }
            edges.append(edge_obj)
        
        # Calculate statistics
        stats = {
            'totalNodes': len(nodes),
            'totalEdges': len(edges),
            'products': node_types.get('Product', 0),
            'plants': node_types.get('Plant', 0),
            'storage': node_types.get('StorageLocation', 0),
            'groups': node_types.get('Group', 0),
            'categories': node_types.get('Category', 0)
        }
        

        
        visualization_data = {
            'nodes': nodes,
            'edges': edges,
            'stats': stats,
            'nodeTypes': node_types,
            'timestamp': datetime.now().isoformat()
        }
        
        return visualization_data
        
    except Exception as e:
        logger.error(f"Graph visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Serve React application
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

react_dist_path = "dist"
if os.path.exists(react_dist_path) and os.path.exists(os.path.join(react_dist_path, "index.html")):
    # Mount static assets
    if os.path.exists(os.path.join(react_dist_path, "assets")):
        app.mount("/assets", StaticFiles(directory=os.path.join(react_dist_path, "assets")), name="assets")
    
    # Serve React app for all other routes
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't serve React for API routes
        if full_path.startswith(("api/", "health", "docs")):
            return {"error": "Route not found", "path": full_path}
        
        # Serve specific files if they exist
        if full_path and "." in full_path.split("/")[-1]:
            file_path = os.path.join(react_dist_path, full_path)
            if os.path.exists(file_path) and os.path.isfile(file_path):
                return FileResponse(file_path)
        
        # Default to React index.html for SPA routing
        return FileResponse(os.path.join(react_dist_path, "index.html"), media_type="text/html")

else:
    # Root endpoint (fallback when React build not found)
    @app.get("/", summary="API Information")
    async def root():
        """API information and documentation links"""
        return {
            "message": "🚀 Advanced FMCG Supply Chain Analytics API",
            "version": "2.0.0",
            "features": [
                "🔬 Advanced graph analytics with machine learning",
                "🤖 Intelligent AI agent with natural language processing", 
                "📊 Real-time Neo4j database integration",
                "💡 Supply chain insights and recommendations",
                "🌟 Executive dashboards and reporting"
            ],
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "chat": "/api/chat",
                "analytics": "/api/analytics/overview",
                "insights": "/api/analytics/insights",
                "dashboard": "/api/dashboard"
            },
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "advanced_api_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False  # Set to True for development
    )# Updated Fri Aug 15 14:49:57 PDT 2025
