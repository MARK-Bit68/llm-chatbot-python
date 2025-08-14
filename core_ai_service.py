# Core AI Service - Extracted from Streamlit
# This contains all your AI logic without Streamlit dependencies

import os
from datetime import datetime
from typing import Dict, List, Optional, Any

class FMCGAIService:
    """
    Core AI service containing all your business logic
    Can be used by Streamlit, FastAPI, or any other interface
    """
    
    def __init__(self):
        self.graph = None
        self.agent = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Neo4j and AI services"""
        try:
            from solutions.graph import get_graph
            from solutions.agent import get_agent
            
            self.graph = get_graph()
            self.agent = get_agent()
            
        except Exception as e:
            print(f"Error initializing services: {e}")
    
    def chat_with_ai(self, message: str) -> Dict[str, Any]:
        """
        Chat with AI assistant - extracted from your bot.py logic
        """
        try:
            from solutions.agent import generate_response
            
            response = generate_response(message)
            
            return {
                "response": response,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "source": "neo4j_ai"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get dashboard data - extracted from your dashboard logic
        """
        try:
            if not self.graph:
                raise Exception("Database not available")
            
            # Get SKU count
            sku_result = self.graph.query("MATCH (sku:SKU) RETURN count(sku) as count")
            total_skus = sku_result[0]['count'] if sku_result else 0
            
            # Get categories
            cat_result = self.graph.query("MATCH (sku:SKU) RETURN DISTINCT sku.category as category")
            categories = [r['category'] for r in cat_result if r['category']]
            
            # Get top SKU by profit
            profit_result = self.graph.query("""
                MATCH (sku:SKU) 
                WHERE sku.unit_price IS NOT NULL AND sku.unit_cost IS NOT NULL
                RETURN sku.sku_id as id, 
                       (sku.unit_price - sku.unit_cost) as profit
                ORDER BY profit DESC LIMIT 1
            """)
            
            top_profit_sku = None
            if profit_result:
                top_profit_sku = {
                    "sku_id": profit_result[0]['id'],
                    "profit": profit_result[0]['profit']
                }
            
            return {
                "totalSKUs": total_skus,
                "totalCategories": len(categories),
                "categories": categories,
                "topProfitSKU": top_profit_sku,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "source": "neo4j"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def get_sku_data(self, sku_id: Optional[str] = None, 
                     category: Optional[str] = None,
                     limit: int = 20) -> Dict[str, Any]:
        """
        Get SKU data with filtering
        """
        try:
            if not self.graph:
                raise Exception("Database not available")
            
            # Build query based on filters
            query = "MATCH (sku:SKU)"
            params = {}
            
            if sku_id:
                query += " WHERE sku.sku_id = $sku_id"
                params["sku_id"] = sku_id
            elif category:
                query += " WHERE sku.category = $category"
                params["category"] = category
            
            query += " RETURN sku LIMIT $limit"
            params["limit"] = limit
            
            results = self.graph.query(query, params)
            
            skus = []
            for record in results:
                sku = record['sku']
                skus.append({
                    "sku_id": sku.get('sku_id'),
                    "category": sku.get('category'),
                    "unit_price": sku.get('unit_price'),
                    "unit_cost": sku.get('unit_cost'),
                    "country": sku.get('country'),
                    "lead_time_days": sku.get('lead_time_days')
                })
            
            return {
                "skus": skus,
                "count": len(skus),
                "timestamp": datetime.now().isoformat(),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Health check for all services
        """
        try:
            neo4j_healthy = self.graph is not None
            
            if neo4j_healthy:
                # Test database with simple query
                test_result = self.graph.query("MATCH (n) RETURN count(n) as count LIMIT 1")
                data_available = len(test_result) > 0
            else:
                data_available = False
            
            return {
                "status": "healthy" if neo4j_healthy and data_available else "degraded",
                "services": {
                    "neo4j": neo4j_healthy,
                    "data": data_available,
                    "ai_agent": self.agent is not None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Create singleton instance
ai_service = FMCGAIService()