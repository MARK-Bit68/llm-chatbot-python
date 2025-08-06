#!/usr/bin/env python3
"""
Supervisor Layer for Robust Error Handling and Result Validation
Uses the nano model to sanity-check results and handle edge cases gracefully.
"""

import re
import json
from typing import Dict, Any, Optional, Tuple
from llm import get_llm

class ResponseSupervisor:
    """
    Supervisor layer that validates and enhances responses using the nano model.
    Acts as an intelligent overseer to handle edge cases and improve user experience.
    """
    
    def __init__(self):
        self.llm = get_llm()
        self.max_retries = 3
        self.quality_threshold = 0.7
        
    def supervise_response(self, user_input: str, agent_response: str, query_type: str) -> str:
        """
        Supervise and enhance the agent response using the nano model.
        
        Args:
            user_input: Original user query
            agent_response: Response from the agent
            query_type: Type of query (SKU_SPECIFIC, ANALYTICAL, etc.)
            
        Returns:
            Enhanced response or fallback
        """
        print(f"🔍 SUPERVISOR: Analyzing response for query type: {query_type}")
        
        # Step 1: Validate response quality
        quality_score = self._assess_response_quality(user_input, agent_response, query_type)
        print(f"🔍 SUPERVISOR: Quality score: {quality_score}")
        
        if quality_score >= self.quality_threshold:
            print("🔍 SUPERVISOR: Response quality acceptable")
            return agent_response
        
        # Step 2: Try to enhance the response
        enhanced_response = self._enhance_response(user_input, agent_response, query_type)
        if enhanced_response:
            print("🔍 SUPERVISOR: Response enhanced successfully")
            return enhanced_response
        
        # Step 3: Generate intelligent fallback
        fallback_response = self._generate_intelligent_fallback(user_input, query_type)
        print("🔍 SUPERVISOR: Using intelligent fallback")
        return fallback_response
    
    def _assess_response_quality(self, user_input: str, response: str, query_type: str) -> float:
        """
        Assess the quality of the response using the nano model.
        """
        try:
            prompt = f"""
            Assess the quality of this response to the user query.
            
            User Query: "{user_input}"
            Query Type: {query_type}
            Response: "{response}"
            
            Rate the response quality from 0.0 to 1.0 based on:
            - Relevance to the query
            - Completeness of information
            - Clarity and usefulness
            - Technical accuracy
            
            Consider the query type:
            - SKU_SPECIFIC: Should contain detailed SKU information
            - ANALYTICAL: Should contain analysis and insights
            - GENERAL_DATA: Should contain comprehensive data overview
            - CONVERSATIONAL: Should be helpful and friendly
            
            IMPORTANT: If the response is relevant and helpful, give it a score of 0.7 or higher.
            Only give low scores (0.0-0.3) if the response is completely irrelevant or contains errors.
            
            Return only a number between 0.0 and 1.0:
            """
            
            result = self.llm.invoke(prompt)
            # Handle different response types
            if hasattr(result, 'content'):
                result_text = result.content
            elif hasattr(result, 'strip'):
                result_text = result.strip()
            else:
                result_text = str(result)
            
            try:
                score = float(result_text.strip())
                return max(0.0, min(1.0, score))
            except ValueError:
                return 0.7  # More lenient default score
                
        except Exception as e:
            print(f"🔍 SUPERVISOR: Quality assessment failed: {e}")
            return 0.7  # More lenient default score
    
    def _enhance_response(self, user_input: str, response: str, query_type: str) -> Optional[str]:
        """
        Try to enhance the response using the nano model.
        """
        try:
            prompt = f"""
            Enhance this response to make it more helpful and complete.
            
            User Query: "{user_input}"
            Query Type: {query_type}
            Current Response: "{response}"
            
            IMPORTANT: Only enhance if the response needs improvement.
            If the response is already good and helpful, return "NO_ENHANCEMENT_NEEDED".
            
            Enhance the response by:
            1. Adding missing context if needed
            2. Clarifying unclear information
            3. Making it more user-friendly
            4. Adding helpful suggestions if appropriate
            
            Keep the core information but make it more complete and useful.
            Return only the enhanced response or "NO_ENHANCEMENT_NEEDED":
            """
            
            enhanced = self.llm.invoke(prompt)
            # Handle different response types
            if hasattr(enhanced, 'content'):
                enhanced_text = enhanced.content
            elif hasattr(enhanced, 'strip'):
                enhanced_text = enhanced.strip()
            else:
                enhanced_text = str(enhanced)
            
            if "NO_ENHANCEMENT_NEEDED" in enhanced_text.upper():
                return None
            
            if enhanced_text and len(enhanced_text.strip()) > 10:
                return enhanced_text.strip()
            return None
            
        except Exception as e:
            print(f"🔍 SUPERVISOR: Response enhancement failed: {e}")
            return None
    
    def _generate_intelligent_fallback(self, user_input: str, query_type: str) -> str:
        """
        Generate an intelligent fallback response based on query type.
        """
        try:
            prompt = f"""
            Generate a helpful response for this user query when the system encountered an issue.
            
            User Query: "{user_input}"
            Query Type: {query_type}
            
            Create a response that:
            1. Acknowledges the issue gracefully
            2. Provides helpful alternatives
            3. Suggests rephrasing if needed
            4. Maintains a professional, helpful tone
            
            For different query types:
            - SKU_SPECIFIC: Suggest specific SKU queries
            - ANALYTICAL: Suggest analytical approaches
            - GENERAL_DATA: Suggest data exploration
            - CONVERSATIONAL: Be friendly and helpful
            
            Return only the response:
            """
            
            fallback = self.llm.invoke(prompt)
            # Handle different response types
            if hasattr(fallback, 'content'):
                fallback_text = fallback.content
            elif hasattr(fallback, 'strip'):
                fallback_text = fallback.strip()
            else:
                fallback_text = str(fallback)
            
            if fallback_text and len(fallback_text.strip()) > 10:
                return fallback_text.strip()
            
        except Exception as e:
            print(f"🔍 SUPERVISOR: Fallback generation failed: {e}")
        
        # Default fallbacks if LLM fails
        return self._get_default_fallback(user_input, query_type)
    
    def _get_default_fallback(self, user_input: str, query_type: str) -> str:
        """
        Get default fallback responses when LLM enhancement fails.
        """
        if query_type == "SKU_SPECIFIC":
            return f"I'm having trouble accessing specific SKU information right now. Please try:\n\n" + \
                   "• 'Tell me about SKU001' (for a specific SKU)\n" + \
                   "• 'Show me all SKUs' (for general data)\n" + \
                   "• 'Which SKUs are most profitable?' (for analysis)"
        
        elif query_type == "ANALYTICAL":
            return f"I'm having trouble analyzing that right now. Please try:\n\n" + \
                   "• 'Show me SKUs with low inventory' (for inventory issues)\n" + \
                   "• 'Which SKUs have supply shortages?' (for supply issues)\n" + \
                   "• 'Show me demand vs supply analysis' (for mismatches)"
        
        elif query_type == "GENERAL_DATA":
            return f"I'm having trouble retrieving the data right now. Please try:\n\n" + \
                   "• 'Show me all SKUs' (for complete list)\n" + \
                   "• 'Tell me about SKU001' (for specific SKU)\n" + \
                   "• 'Which categories do we have?' (for categories)"
        
        else:
            return f"I'm having trouble processing your request right now. Please try:\n\n" + \
                   "• 'Tell me about SKU001' (for specific SKU information)\n" + \
                   "• 'Show me all SKUs' (for general data)\n" + \
                   "• 'Show me supply chain gaps' (for analysis)\n" + \
                   "• 'Which SKUs are most profitable?' (for financial analysis)\n\n" + \
                   "If the problem persists, please try rephrasing your question."
    
    def detect_and_fix_common_issues(self, user_input: str, response: str) -> str:
        """
        Detect and fix common issues in responses.
        """
        # Check for common error patterns
        error_patterns = [
            r"Error:.*",
            r"system error.*",
            r"failed to use.*tools.*",
            r"agent.*failed.*",
            r"invalid.*format.*",
            r"parsing.*error.*"
        ]
        
        for pattern in error_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                print(f"🔍 SUPERVISOR: Detected error pattern: {pattern}")
                return self._generate_intelligent_fallback(user_input, "UNKNOWN")
        
        # Check for empty or very short responses
        if len(response.strip()) < 10:
            print("🔍 SUPERVISOR: Detected very short response")
            return self._generate_intelligent_fallback(user_input, "UNKNOWN")
        
        # Use LLM to detect generic responses instead of hard-coded patterns
        try:
            prompt = f"""
            Analyze this response to determine if it's too generic or unhelpful.
            
            Response: "{response}"
            
            A response is too generic if it:
            - Only offers general help without specific information
            - Doesn't address the user's actual question
            - Is overly vague or non-committal
            - Contains only boilerplate text
            
            Return "GENERIC" if the response is too generic, or "GOOD" if it's helpful and specific.
            """
            
            result = self.llm.invoke(prompt)
            if hasattr(result, 'content'):
                result_text = result.content
            elif hasattr(result, 'strip'):
                result_text = result.strip()
            else:
                result_text = str(result)
            
            if "GENERIC" in result_text.upper():
                print(f"🔍 SUPERVISOR: LLM detected generic response")
                fallback = self._generate_intelligent_fallback(user_input, "UNKNOWN")
                return fallback if fallback else response  # Return original if fallback fails
            
            # If LLM says it's good, return the original response
            return response
                
        except Exception as e:
            print(f"🔍 SUPERVISOR: Generic response detection failed: {e}")
            # Fall back to length-based check if LLM fails
            if len(response.strip()) < 20:
                print(f"🔍 SUPERVISOR: Detected very short response")
                fallback = self._generate_intelligent_fallback(user_input, "UNKNOWN")
                return fallback if fallback else response  # Return original if fallback fails
        
        return response
    
    def suggest_query_improvements(self, user_input: str) -> Optional[str]:
        """
        Suggest improvements to the user's query if it seems unclear.
        """
        try:
            prompt = f"""
            Analyze this user query and suggest improvements if needed.
            
            User Query: "{user_input}"
            
            If the query is unclear, vague, or could be improved, suggest:
            1. More specific wording
            2. Alternative phrasings
            3. Related queries that might be more helpful
            
            If the query is clear and specific, return "CLEAR".
            Otherwise, return helpful suggestions.
            """
            
            suggestion = self.llm.invoke(prompt)
            # Handle different response types
            if hasattr(suggestion, 'content'):
                suggestion_text = suggestion.content
            elif hasattr(suggestion, 'strip'):
                suggestion_text = suggestion.strip()
            else:
                suggestion_text = str(suggestion)
            
            if suggestion_text and "CLEAR" not in suggestion_text.upper():
                return suggestion_text.strip()
            return None
            
        except Exception as e:
            print(f"🔍 SUPERVISOR: Query improvement suggestion failed: {e}")
            return None

# Global supervisor instance
supervisor = ResponseSupervisor() 