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
from pyvis.network import Network

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
            
            metrics = {
                "density": nx.density(G),
                "number_of_components": nx.number_connected_components(G),
                "average_clustering": nx.average_clustering(G),
                "transitivity": nx.transitivity(G),
                "diameter": None,
                "average_shortest_path": None,
                "centrality_metrics": {}
            }
            
            # Calculate diameter and average shortest path for largest component
            if nx.is_connected(G):
                metrics["diameter"] = nx.diameter(G)
                metrics["average_shortest_path"] = nx.average_shortest_path_length(G)
            else:
                # Use largest connected component
                largest_cc = max(nx.connected_components(G), key=len)
                subgraph = G.subgraph(largest_cc)
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
                n.sku_id as source_sku,
                id(m) as target_id,
                labels(m) as target_labels,
                m.sku_id as target_sku,
                type(r) as relationship_type,
                properties(r) as rel_props
            LIMIT 10000
            """
            
            results = self.neo4j_graph.query(query)
            
            # Create NetworkX graph
            G = nx.DiGraph()
            
            for record in results:
                source = record['source_sku'] or record['source_id']
                target = record['target_sku'] or record['target_id']
                
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
            # SKU clustering analysis
            clustering_insight = await self._analyze_sku_clusters()
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
    
    async def _analyze_sku_clusters(self) -> Optional[GraphInsight]:
        """Analyze SKU clusters using machine learning"""
        try:
            # Get SKU data for clustering
            query = """
            MATCH (sku:SKU)
            WHERE sku.unit_price IS NOT NULL 
              AND sku.unit_cost IS NOT NULL
              AND sku.lead_time_days IS NOT NULL
            RETURN 
                sku.sku_id as sku_id,
                sku.unit_price as unit_price,
                sku.unit_cost as unit_cost,
                sku.lead_time_days as lead_time,
                sku.category as category,
                sku.country as country,
                (sku.unit_price - sku.unit_cost) as gross_profit
            """
            
            results = self.neo4j_graph.query(query)
            
            if len(results) < 10:  # Need minimum data for clustering
                return None
            
            # Create DataFrame
            df = pd.DataFrame(results)
            
            # Prepare features for clustering
            features = ['unit_price', 'unit_cost', 'lead_time', 'gross_profit']
            X = df[features].fillna(0)
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # K-means clustering
            n_clusters = min(5, len(df) // 10)  # Reasonable number of clusters
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(X_scaled)
            
            df['cluster'] = clusters
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in range(n_clusters):
                cluster_data = df[df['cluster'] == cluster_id]
                
                cluster_analysis[f"cluster_{cluster_id}"] = {
                    "size": len(cluster_data),
                    "avg_price": float(cluster_data['unit_price'].mean()),
                    "avg_cost": float(cluster_data['unit_cost'].mean()),
                    "avg_lead_time": float(cluster_data['lead_time'].mean()),
                    "avg_profit": float(cluster_data['gross_profit'].mean()),
                    "dominant_category": cluster_data['category'].mode().iloc[0] if not cluster_data['category'].mode().empty else "Unknown",
                    "sku_count": len(cluster_data)
                }
            
            # Calculate silhouette score
            silhouette_avg = silhouette_score(X_scaled, clusters)
            
            # Generate recommendations
            recommendations = []
            
            # Find high-profit cluster
            high_profit_cluster = max(cluster_analysis.keys(), 
                                    key=lambda k: cluster_analysis[k]['avg_profit'])
            recommendations.append(f"Focus on {high_profit_cluster} - highest profit margin cluster")
            
            # Find high lead time cluster
            high_leadtime_cluster = max(cluster_analysis.keys(), 
                                      key=lambda k: cluster_analysis[k]['avg_lead_time'])
            recommendations.append(f"Optimize supply chain for {high_leadtime_cluster} - longest lead times")
            
            return GraphInsight(
                insight_type="clustering",
                title="SKU Performance Clusters",
                description=f"Identified {n_clusters} distinct SKU performance clusters using machine learning",
                metrics={
                    "cluster_count": n_clusters,
                    "silhouette_score": float(silhouette_avg),
                    "total_skus_analyzed": len(df),
                    "cluster_analysis": cluster_analysis
                },
                visualization_data={
                    "cluster_data": df.to_dict('records'),
                    "feature_importance": features
                },
                recommendations=recommendations,
                confidence=float(silhouette_avg),
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in SKU clustering analysis: {e}")
            return None
    
    async def _analyze_inventory_risks(self) -> Optional[GraphInsight]:
        """Analyze inventory risks and opportunities"""
        try:
            query = """
            MATCH (sku:SKU)
            WHERE sku.unit_price IS NOT NULL AND sku.lead_time_days IS NOT NULL
            RETURN 
                sku.sku_id as sku_id,
                sku.category as category,
                sku.country as country,
                sku.unit_price as unit_price,
                sku.unit_cost as unit_cost,
                sku.lead_time_days as lead_time,
                (sku.unit_price - sku.unit_cost) as gross_profit,
                CASE 
                    WHEN sku.lead_time_days > 30 THEN 'HIGH_RISK'
                    WHEN sku.lead_time_days > 15 THEN 'MEDIUM_RISK'
                    ELSE 'LOW_RISK'
                END as risk_category
            """
            
            results = self.neo4j_graph.query(query)
            df = pd.DataFrame(results)
            
            if df.empty:
                return None
            
            # Risk analysis
            risk_distribution = df['risk_category'].value_counts()
            high_risk_skus = df[df['risk_category'] == 'HIGH_RISK']
            
            # Category risk analysis
            category_risks = df.groupby('category').agg({
                'lead_time': 'mean',
                'gross_profit': 'mean',
                'risk_category': lambda x: (x == 'HIGH_RISK').sum()
            }).round(2)
            
            recommendations = []
            
            if len(high_risk_skus) > 0:
                worst_category = high_risk_skus.groupby('category').size().idxmax()
                recommendations.append(f"Priority: Review supply chain for {worst_category} category")
                
                # Find high-value high-risk SKUs
                high_value_risk = high_risk_skus[high_risk_skus['gross_profit'] > high_risk_skus['gross_profit'].quantile(0.75)]
                if len(high_value_risk) > 0:
                    recommendations.append(f"Critical: {len(high_value_risk)} high-profit SKUs have high lead time risk")
            
            recommendations.append("Consider supplier diversification for high-risk categories")
            recommendations.append("Implement safety stock strategies for medium and high-risk SKUs")
            
            return GraphInsight(
                insight_type="inventory_risk",
                title="Inventory Risk Analysis",
                description="Analysis of lead time risks and inventory vulnerabilities across SKU portfolio",
                metrics={
                    "total_skus": len(df),
                    "high_risk_count": int(risk_distribution.get('HIGH_RISK', 0)),
                    "medium_risk_count": int(risk_distribution.get('MEDIUM_RISK', 0)),
                    "low_risk_count": int(risk_distribution.get('LOW_RISK', 0)),
                    "average_lead_time": float(df['lead_time'].mean()),
                    "category_risk_analysis": category_risks.to_dict()
                },
                visualization_data={
                    "risk_distribution": risk_distribution.to_dict(),
                    "category_risks": category_risks.to_dict(),
                    "sku_risk_data": df.to_dict('records')
                },
                recommendations=recommendations,
                confidence=0.85,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in inventory risk analysis: {e}")
            return None
    
    async def _analyze_profitability_patterns(self) -> Optional[GraphInsight]:
        """Analyze profitability patterns and trends"""
        try:
            query = """
            MATCH (sku:SKU)
            WHERE sku.unit_price IS NOT NULL 
              AND sku.unit_cost IS NOT NULL
              AND sku.category IS NOT NULL
            WITH sku, (sku.unit_price - sku.unit_cost) as gross_profit,
                 (sku.unit_price - sku.unit_cost) / sku.unit_price as profit_margin
            RETURN 
                sku.sku_id as sku_id,
                sku.category as category,
                sku.country as country,
                sku.unit_price as unit_price,
                sku.unit_cost as unit_cost,
                gross_profit,
                profit_margin * 100 as profit_margin_pct
            ORDER BY gross_profit DESC
            """
            
            results = self.neo4j_graph.query(query)
            df = pd.DataFrame(results)
            
            if df.empty:
                return None
            
            # Profitability analysis
            total_profit = df['gross_profit'].sum()
            avg_margin = df['profit_margin_pct'].mean()
            
            # Category profitability
            category_profit = df.groupby('category').agg({
                'gross_profit': ['sum', 'mean', 'count'],
                'profit_margin_pct': 'mean'
            }).round(2)
            
            # Top performers
            top_skus = df.nlargest(10, 'gross_profit')[['sku_id', 'category', 'gross_profit', 'profit_margin_pct']]
            bottom_skus = df.nsmallest(10, 'gross_profit')[['sku_id', 'category', 'gross_profit', 'profit_margin_pct']]
            
            # Profit concentration (Pareto analysis)
            df_sorted = df.sort_values('gross_profit', ascending=False)
            df_sorted['cumulative_profit'] = df_sorted['gross_profit'].cumsum()
            df_sorted['cumulative_profit_pct'] = (df_sorted['cumulative_profit'] / total_profit) * 100
            
            # Find 80% of profit concentration
            pareto_80_count = len(df_sorted[df_sorted['cumulative_profit_pct'] <= 80])
            pareto_80_pct = (pareto_80_count / len(df_sorted)) * 100
            
            recommendations = []
            
            # Best performing category
            best_category = category_profit[('gross_profit', 'sum')].idxmax()
            recommendations.append(f"Expand {best_category} category - highest total profit contributor")
            
            # Worst performing category
            worst_category = category_profit[('gross_profit', 'mean')].idxmin()
            recommendations.append(f"Review pricing strategy for {worst_category} category - lowest average profit")
            
            # Pareto insight
            recommendations.append(f"Focus on top {pareto_80_count} SKUs - they generate 80% of profits")
            
            if len(bottom_skus[bottom_skus['gross_profit'] < 0]) > 0:
                loss_making_count = len(bottom_skus[bottom_skus['gross_profit'] < 0])
                recommendations.append(f"Critical: Review {loss_making_count} loss-making SKUs")
            
            return GraphInsight(
                insight_type="profitability",
                title="Profitability Pattern Analysis",
                description="Deep analysis of profit patterns, margins, and performance across SKU portfolio",
                metrics={
                    "total_gross_profit": float(total_profit),
                    "average_profit_margin": float(avg_margin),
                    "total_skus_analyzed": len(df),
                    "profitable_skus": int((df['gross_profit'] > 0).sum()),
                    "loss_making_skus": int((df['gross_profit'] < 0).sum()),
                    "pareto_80_sku_count": pareto_80_count,
                    "pareto_80_percentage": float(pareto_80_pct),
                    "category_performance": category_profit.to_dict()
                },
                visualization_data={
                    "top_performers": top_skus.to_dict('records'),
                    "bottom_performers": bottom_skus.to_dict('records'),
                    "category_profit_data": category_profit.to_dict(),
                    "pareto_data": df_sorted[['sku_id', 'gross_profit', 'cumulative_profit_pct']].to_dict('records')
                },
                recommendations=recommendations,
                confidence=0.90,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error in profitability analysis: {e}")
            return None
    
    async def _analyze_regional_performance(self) -> Optional[GraphInsight]:
        """Analyze regional performance patterns"""
        try:
            query = """
            MATCH (sku:SKU)
            WHERE sku.country IS NOT NULL 
              AND sku.unit_price IS NOT NULL 
              AND sku.unit_cost IS NOT NULL
            WITH sku, (sku.unit_price - sku.unit_cost) as gross_profit
            RETURN 
                sku.country as country,
                sku.category as category,
                count(sku) as sku_count,
                avg(sku.unit_price) as avg_price,
                avg(sku.unit_cost) as avg_cost,
                avg(gross_profit) as avg_profit,
                sum(gross_profit) as total_profit,
                avg(sku.lead_time_days) as avg_lead_time
            ORDER BY total_profit DESC
            """
            
            results = self.neo4j_graph.query(query)
            df = pd.DataFrame(results)
            
            if df.empty:
                return None
            
            # Regional performance metrics
            total_countries = df['country'].nunique()
            best_country = df.loc[df['total_profit'].idxmax(), 'country']
            worst_country = df.loc[df['total_profit'].idxmin(), 'country']
            
            # Calculate performance scores (normalized)
            df['profit_score'] = (df['total_profit'] - df['total_profit'].min()) / (df['total_profit'].max() - df['total_profit'].min())
            df['efficiency_score'] = 1 - ((df['avg_lead_time'] - df['avg_lead_time'].min()) / (df['avg_lead_time'].max() - df['avg_lead_time'].min()))
            df['overall_score'] = (df['profit_score'] + df['efficiency_score']) / 2
            
            # Top and bottom performers
            top_regions = df.nlargest(5, 'overall_score')
            bottom_regions = df.nsmallest(3, 'overall_score')
            
            recommendations = []
            
            recommendations.append(f"Strengthen operations in {best_country} - top profit generator")
            recommendations.append(f"Investigate challenges in {worst_country} - needs improvement")
            
            # Lead time insights
            high_leadtime_country = df.loc[df['avg_lead_time'].idxmax(), 'country']
            recommendations.append(f"Optimize supply chain in {high_leadtime_country} - longest lead times")
            
            # Portfolio insights
            thin_portfolio_countries = df[df['sku_count'] < df['sku_count'].quantile(0.25)]
            if len(thin_portfolio_countries) > 0:
                recommendations.append(f"Expand SKU portfolio in {len(thin_portfolio_countries)} countries with limited offerings")
            
            return GraphInsight(
                insight_type="regional_performance",
                title="Regional Performance Analysis",
                description="Comprehensive analysis of regional performance, efficiency, and opportunities",
                metrics={
                    "total_countries": total_countries,
                    "best_performing_country": best_country,
                    "worst_performing_country": worst_country,
                    "average_skus_per_country": float(df['sku_count'].mean()),
                    "total_portfolio_profit": float(df['total_profit'].sum()),
                    "regional_performance_variance": float(df['overall_score'].std())
                },
                visualization_data={
                    "regional_data": df.to_dict('records'),
                    "top_performers": top_regions[['country', 'total_profit', 'overall_score']].to_dict('records'),
                    "bottom_performers": bottom_regions[['country', 'total_profit', 'overall_score']].to_dict('records')
                },
                recommendations=recommendations,
                confidence=0.88,
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