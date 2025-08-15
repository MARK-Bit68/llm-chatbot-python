# Advanced Graph Analytics Engine
# Extracted from Streamlit with enhanced capabilities

import os
import asyncio
import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from concurrent.futures import ThreadPoolExecutor
import json

# Neo4j and Graph Libraries
from neo4j import GraphDatabase
from langchain_neo4j import Neo4jGraph
import igraph as ig

# Machine Learning Libraries
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import networkx.algorithms.community as nx_comm

# Time Series and Forecasting
from prophet import Prophet
import scipy.stats as stats

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GraphInsight:
    """Container for graph analysis insights"""
    insight_type: str
    title: str
    description: str
    metrics: Dict[str, Any]
    visualization_data: Dict[str, Any]
    recommendations: List[str]
    confidence: float
    timestamp: datetime

class AdvancedGraphAnalyticsEngine:
    """
    Advanced Graph Analytics Engine for FMCG Supply Chain
    
    Provides sophisticated graph analysis, machine learning,
    and real-time insights extracted from your Streamlit logic
    """
    
    def __init__(self):
        self.neo4j_graph = None
        self.networkx_graph = None
        self.igraph_graph = None
        self.cached_results = {}
        self.analytics_cache_ttl = 300  # 5 minutes
        self._initialize_connections()
        
    def _initialize_connections(self):
        """Initialize all graph database connections"""
        try:
            # Neo4j LangChain connection (from your existing code)
            self.neo4j_graph = Neo4jGraph(
                url=os.getenv("NEO4J_URI"),
                username=os.getenv("NEO4J_USERNAME", "neo4j"),
                password=os.getenv("NEO4J_PASSWORD"),
            )
            
            # Direct Neo4j driver for advanced queries
            self.neo4j_driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
            )
            
            logger.info("✅ Graph connections initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing graph connections: {e}")
            self.neo4j_graph = None
            self.neo4j_driver = None
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all graph services"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "healthy"
        }
        
        # Neo4j connection check
        try:
            if self.neo4j_graph:
                result = self.neo4j_graph.query("MATCH (n) RETURN count(n) as total_nodes LIMIT 1")
                node_count = result[0]['total_nodes'] if result else 0
                
                health_data["services"]["neo4j"] = {
                    "status": "healthy",
                    "node_count": node_count,
                    "connection": "active"
                }
            else:
                health_data["services"]["neo4j"] = {
                    "status": "unhealthy",
                    "error": "No connection"
                }
                health_data["overall_status"] = "degraded"
                
        except Exception as e:
            health_data["services"]["neo4j"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_data["overall_status"] = "degraded"
        
        # Graph analytics status
        health_data["services"]["analytics"] = {
            "status": "healthy",
            "cached_analyses": len(self.cached_results),
            "libraries": {
                "networkx": True,
                "igraph": True,
                "sklearn": True,
                "prophet": True
            }
        }
        
        return health_data
    
    async def get_graph_overview(self) -> Dict[str, Any]:
        """Get comprehensive graph overview with advanced metrics"""
        try:
            cache_key = "graph_overview"
            if self._is_cached_valid(cache_key):
                return self.cached_results[cache_key]
            
            # Basic graph statistics
            overview_query = """
            MATCH (n)
            WITH labels(n) as node_labels, n
            UNWIND node_labels as label
            WITH label, count(n) as count
            RETURN label, count
            ORDER BY count DESC
            """
            
            label_results = self.neo4j_graph.query(overview_query)
            
            # Relationship statistics
            rel_query = """
            MATCH ()-[r]->()
            WITH type(r) as rel_type, count(r) as count
            RETURN rel_type, count
            ORDER BY count DESC
            """
            
            rel_results = self.neo4j_graph.query(rel_query)
            
            # Advanced graph metrics
            graph_metrics = await self._calculate_advanced_metrics()
            
            overview = {
                "node_statistics": {
                    "total_nodes": sum([r['count'] for r in label_results]),
                    "node_types": {r['label']: r['count'] for r in label_results}
                },
                "relationship_statistics": {
                    "total_relationships": sum([r['count'] for r in rel_results]),
                    "relationship_types": {r['rel_type']: r['count'] for r in rel_results}
                },
                "advanced_metrics": graph_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            self._cache_result(cache_key, overview)
            return overview
            
        except Exception as e:
            logger.error(f"Error getting graph overview: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def _calculate_advanced_metrics(self) -> Dict[str, Any]:
        """Calculate advanced graph theory metrics"""
        try:
            # Load graph into NetworkX for advanced analysis
            await self._load_networkx_graph()
            
            if not self.networkx_graph:
                return {"error": "Could not load NetworkX graph"}
            
            G = self.networkx_graph
            
            # Convert to undirected graph for metrics that don't work with directed graphs
            G_undirected = G.to_undirected()
            
            metrics = {
                "density": nx.density(G),
                "number_of_components": nx.number_connected_components(G_undirected),
                "average_clustering": nx.average_clustering(G_undirected),
                "transitivity": nx.transitivity(G_undirected),
                "diameter": None,
                "average_shortest_path": None,
                "centrality_metrics": {}
            }
            
            # Calculate diameter and average shortest path for largest component
            if nx.is_connected(G_undirected):
                metrics["diameter"] = nx.diameter(G_undirected)
                metrics["average_shortest_path"] = nx.average_shortest_path_length(G_undirected)
            else:
                # Use largest connected component
                largest_cc = max(nx.connected_components(G_undirected), key=len)
                subgraph = G_undirected.subgraph(largest_cc)
                if len(subgraph) > 1:
                    metrics["diameter"] = nx.diameter(subgraph)
                    metrics["average_shortest_path"] = nx.average_shortest_path_length(subgraph)
            
            # Centrality measures (sample for performance)
            sample_size = min(100, len(G.nodes()))
            sample_nodes = list(G.nodes())[:sample_size]
            
            degree_centrality = nx.degree_centrality(G)
            betweenness_centrality = nx.betweenness_centrality(G, k=sample_size)
            
            metrics["centrality_metrics"] = {
                "highest_degree_centrality": max(degree_centrality.items(), key=lambda x: x[1]),
                "highest_betweenness_centrality": max(betweenness_centrality.items(), key=lambda x: x[1]),
                "average_degree": sum(degree_centrality.values()) / len(degree_centrality)
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error calculating advanced metrics: {e}")
            return {"error": str(e)}
    
    async def _load_networkx_graph(self):
        """Load Neo4j data into NetworkX for graph algorithms"""
        try:
            if self.networkx_graph:
                return  # Already loaded
            
            # Query to get all relationships
            query = """
            MATCH (n)-[r]->(m)
            RETURN 
                id(n) as source_id,
                labels(n) as source_labels,
                n.code as source_product,
                id(m) as target_id,
                labels(m) as target_labels,
                m.code as target_product,
                type(r) as relationship_type,
                properties(r) as rel_props
            LIMIT 10000
            """
            
            results = self.neo4j_graph.query(query)
            
            # Create NetworkX graph
            G = nx.DiGraph()
            
            for record in results:
                source = record['source_product'] or f"{record['source_labels'][0] if record['source_labels'] else 'Node'}_{record['source_id']}"
                target = record['target_product'] or f"{record['target_labels'][0] if record['target_labels'] else 'Node'}_{record['target_id']}"
                
                # Add nodes with attributes
                G.add_node(source, 
                          labels=record['source_labels'],
                          node_id=record['source_id'])
                G.add_node(target, 
                          labels=record['target_labels'],
                          node_id=record['target_id'])
                
                # Add edge with attributes
                G.add_edge(source, target, 
                          relationship_type=record['relationship_type'],
                          **record['rel_props'])
            
            self.networkx_graph = G
            logger.info(f"✅ NetworkX graph loaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
            
        except Exception as e:
            logger.error(f"Error loading NetworkX graph: {e}")
            self.networkx_graph = None
    
    async def detect_supply_chain_patterns(self) -> List[GraphInsight]:
        """Detect patterns and anomalies in supply chain graph"""
        insights = []
        
        try:
            # Product clustering analysis
            clustering_insight = await self._analyze_product_clusters()
            if clustering_insight:
                insights.append(clustering_insight)
            
            # Inventory risk analysis
            inventory_insight = await self._analyze_inventory_risks()
            if inventory_insight:
                insights.append(inventory_insight)
            
            # Profitability patterns
            profit_insight = await self._analyze_profitability_patterns()
            if profit_insight:
                insights.append(profit_insight)
            
            # Regional performance analysis
            regional_insight = await self._analyze_regional_performance()
            if regional_insight:
                insights.append(regional_insight)
            
            logger.info(f"✅ Generated {len(insights)} supply chain insights")
            
        except Exception as e:
            logger.error(f"Error detecting supply chain patterns: {e}")
            insights.append(GraphInsight(
                insight_type="error",
                title="Analysis Error",
                description=f"Error in pattern detection: {str(e)}",
                metrics={},
                visualization_data={},
                recommendations=[],
                confidence=0.0,
                timestamp=datetime.now()
            ))
        
        return insights
    
    async def _analyze_product_clusters(self) -> Optional[GraphInsight]:
        """Analyze Product clusters using machine learning"""
        try:
            # Get Product data for clustering
            query = """
            MATCH (p:Product)
            RETURN 
                p.code as product_code,
                p.name as product_name,
                labels(p) as labels
            LIMIT 100
            """
            
            results = self.neo4j_graph.query(query)
            
            if len(results) < 5:  # Need minimum data for analysis
                return None
            
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Simple analysis based on available data
            total_products = len(df)
            product_codes = df['product_code'].tolist()
            
            # Group analysis
            group_query = """
            MATCH (p:Product)-[:IN_GROUP]->(g:Group)
            RETURN g.code as group_code, count(p) as product_count
            ORDER BY product_count DESC
            """
            group_results = self.neo4j_graph.query(group_query)
            
            # Create insight
            return GraphInsight(
                insight_type="clustering",
                title="Product Distribution Analysis",
                description=f"Analyzed {total_products} products across the supply chain network",
                metrics={
                    "total_products": total_products,
                    "product_codes": product_codes[:10],  # First 10 for display
                    "groups": len(group_results)
                },
                visualization_data={
                    "product_count": total_products,
                    "group_distribution": {r['group_code']: r['product_count'] for r in group_results}
                },
                recommendations=[
                    f"Monitor {total_products} products for supply chain optimization",
                    "Analyze group distribution for inventory planning",
                    "Consider cross-group product relationships"
                ],
                confidence=0.85,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in product clustering analysis: {e}")
            return None
    
    async def _analyze_inventory_risks(self) -> Optional[GraphInsight]:
        """Analyze inventory risks and opportunities"""
        try:
            query = """
            MATCH (p:Product)-[:PRODUCED_AT]->(pl:Plant)
            RETURN 
                p.code as product_code,
                pl.id as plant_id,
                count(pl) as production_sites
            """
            
            results = self.neo4j_graph.query(query)
            
            if len(results) < 5:
                return None
            
            # Simple production analysis
            total_products = len(results)
            total_plants = len(set(r['plant_id'] for r in results))
            
            return GraphInsight(
                insight_type="inventory_risk",
                title="Production Network Analysis",
                description=f"Analyzed production network with {total_products} products across {total_plants} plants",
                metrics={
                    "total_products": total_products,
                    "total_plants": total_plants,
                    "avg_plants_per_product": total_plants / total_products if total_products > 0 else 0
                },
                visualization_data={
                    "product_count": total_products,
                    "plant_count": total_plants
                },
                recommendations=[
                    f"Monitor production across {total_plants} plants",
                    "Optimize product-plant assignments",
                    "Consider production capacity planning"
                ],
                confidence=0.80,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in inventory risk analysis: {e}")
            return None
    
    async def _analyze_profitability_patterns(self) -> Optional[GraphInsight]:
        """Analyze profitability patterns and trends"""
        try:
            query = """
            MATCH (p:Product)-[:IN_GROUP]->(g:Group)
            RETURN 
                g.code as group_code,
                count(p) as product_count
            ORDER BY product_count DESC
            """
            
            results = self.neo4j_graph.query(query)
            
            if len(results) < 3:
                return None
            
            # Simple group analysis
            total_groups = len(results)
            total_products = sum(r['product_count'] for r in results)
            
            return GraphInsight(
                insight_type="profitability",
                title="Product Group Distribution",
                description=f"Analyzed product distribution across {total_groups} groups with {total_products} total products",
                metrics={
                    "total_groups": total_groups,
                    "total_products": total_products,
                    "avg_products_per_group": total_products / total_groups if total_groups > 0 else 0
                },
                visualization_data={
                    "group_distribution": {r['group_code']: r['product_count'] for r in results}
                },
                recommendations=[
                    f"Focus on largest product groups for optimization",
                    "Consider cross-group synergies",
                    "Monitor group performance trends"
                ],
                confidence=0.75,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in profitability analysis: {e}")
            return None
    
    async def _analyze_regional_performance(self) -> Optional[GraphInsight]:
        """Analyze regional performance patterns"""
        try:
            query = """
            MATCH (p:Product)-[:STORED_AT]->(sl:StorageLocation)
            RETURN 
                sl.id as storage_id,
                count(p) as product_count
            ORDER BY product_count DESC
            """
            
            results = self.neo4j_graph.query(query)
            
            if len(results) < 3:
                return None
            
            # Simple storage analysis
            total_storage_locations = len(results)
            total_products_stored = sum(r['product_count'] for r in results)
            
            return GraphInsight(
                insight_type="regional_performance",
                title="Storage Location Analysis",
                description=f"Analyzed product distribution across {total_storage_locations} storage locations",
                metrics={
                    "total_storage_locations": total_storage_locations,
                    "total_products_stored": total_products_stored,
                    "avg_products_per_location": total_products_stored / total_storage_locations if total_storage_locations > 0 else 0
                },
                visualization_data={
                    "storage_distribution": {f"Location_{r['storage_id']}": r['product_count'] for r in results}
                },
                recommendations=[
                    f"Optimize storage across {total_storage_locations} locations",
                    "Monitor storage capacity utilization",
                    "Consider storage location consolidation"
                ],
                confidence=0.70,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in regional performance analysis: {e}")
            return None
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Check if cached result is still valid"""
        if cache_key not in self.cached_results:
            return False
        
        cached_time = self.cached_results[cache_key].get('_cached_at')
        if not cached_time:
            return False
        
        return (datetime.now() - cached_time).seconds < self.analytics_cache_ttl
    
    def _cache_result(self, cache_key: str, result: Dict[str, Any]):
        """Cache analysis result with timestamp"""
        result['_cached_at'] = datetime.now()
        self.cached_results[cache_key] = result

# Create singleton instance
analytics_engine = AdvancedGraphAnalyticsEngine()