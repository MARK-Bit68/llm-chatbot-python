#!/usr/bin/env python3
"""
Test chat interface with AI Enhanced SOP dataset via API calls
"""

import requests
import json
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatInterfaceTester:
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_queries = [
            "How many products are there?",
            "Show me product categories",
            "What are the top revenue products?",
            "Show me Electronics products",
            "Analyze brand performance",
            "Show me dashboard overview",
            "What products have high risk ratings?",
            "Compare category performance",
            "Show me ABC classification summary",
            "Analyze profitability patterns"
        ]
    
    def test_health_endpoint(self):
        """Test the health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                logger.info(f"✅ Health check passed: {health_data.get('status', 'unknown')}")
                return True
            else:
                logger.error(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False
    
    def test_dashboard_endpoint(self):
        """Test the dashboard endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/dashboard", timeout=10)
            if response.status_code == 200:
                dashboard_data = response.json()
                logger.info(f"✅ Dashboard endpoint working: {len(dashboard_data)} items")
                return True
            else:
                logger.error(f"❌ Dashboard endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Dashboard endpoint error: {e}")
            return False
    
    def test_chat_endpoint(self):
        """Test the chat endpoint with sample queries"""
        successful_queries = 0
        total_queries = len(self.test_queries)
        
        for i, query in enumerate(self.test_queries):
            try:
                logger.info(f"🔍 Testing query {i+1}/{total_queries}: '{query}'")
                
                payload = {
                    "message": query,
                    "session_id": f"test_session_{i}"
                }
                
                response = requests.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    chat_response = response.json()
                    status = chat_response.get('status', 'unknown')
                    response_text = chat_response.get('response', '')
                    
                    if status == 'success' and len(response_text) > 100:
                        logger.info(f"   ✅ Success: {len(response_text)} chars")
                        successful_queries += 1
                    else:
                        logger.warning(f"   ⚠️ Partial success: status={status}, length={len(response_text)}")
                else:
                    logger.error(f"   ❌ Failed: {response.status_code}")
                
                # Small delay between requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"   ❌ Query error: {e}")
        
        success_rate = (successful_queries / total_queries) * 100
        logger.info(f"📊 Chat test summary: {successful_queries}/{total_queries} successful ({success_rate:.1f}%)")
        
        return success_rate >= 70  # Consider 70%+ as passing
    
    def test_analytics_endpoint(self):
        """Test the analytics endpoint"""
        try:
            # Test overview analytics
            payload = {
                "analysis_type": "overview",
                "parameters": {}
            }
            
            response = requests.post(
                f"{self.base_url}/api/analytics/insights",
                json=payload,
                timeout=20
            )
            
            if response.status_code == 200:
                analytics_data = response.json()
                insights_count = len(analytics_data.get('insights', []))
                logger.info(f"✅ Analytics endpoint working: {insights_count} insights")
                return True
            else:
                logger.error(f"❌ Analytics endpoint failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Analytics endpoint error: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        logger.info(f"🚀 Starting comprehensive chat interface test against {self.base_url}")
        
        results = {
            'health': self.test_health_endpoint(),
            'dashboard': self.test_dashboard_endpoint(),
            'analytics': self.test_analytics_endpoint(),
            'chat': self.test_chat_endpoint()
        }
        
        passed_tests = sum(results.values())
        total_tests = len(results)
        
        logger.info(f"\n📋 Test Results Summary:")
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {test_name.capitalize()}: {status}")
        
        overall_success = passed_tests >= 3  # At least 3/4 tests should pass
        
        if overall_success:
            logger.info(f"\n🎉 Overall: PASS ({passed_tests}/{total_tests} tests passed)")
            logger.info("✅ Chat interface is working with AI Enhanced SOP dataset!")
        else:
            logger.error(f"\n❌ Overall: FAIL ({passed_tests}/{total_tests} tests passed)")
            logger.error("🔧 Chat interface needs attention")
        
        return overall_success

def main():
    """Main test function"""
    
    # Try to determine the correct URL
    import os
    
    # Check if we're running on Railway (has RAILWAY_ENVIRONMENT)
    if os.getenv('RAILWAY_ENVIRONMENT'):
        # Running on Railway, use localhost
        base_url = "http://localhost:8000"
        logger.info("🚂 Detected Railway environment, using localhost")
    else:
        # Running locally, might need to use a different URL
        base_url = "http://localhost:8000"
        logger.info("💻 Using localhost for testing")
    
    tester = ChatInterfaceTester(base_url)
    success = tester.run_comprehensive_test()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)