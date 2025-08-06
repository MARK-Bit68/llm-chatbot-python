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
        Try to enhance the response using the nano model with personality.
        """
        try:
            prompt = f"""
            You are a helpful FMCG supply chain expert. Enhance this response to make it more helpful, complete, and personable.
            
            User Query: "{user_input}"
            Query Type: {query_type}
            Current Response: "{response}"
            
            IMPORTANT: Only enhance if the response needs improvement.
            If the response is already good and helpful, return "NO_ENHANCEMENT_NEEDED".
            
            Enhance the response by:
            1. Adding missing context if needed
            2. Clarifying unclear information
            3. Making it more user-friendly and personable
            4. Adding helpful suggestions if appropriate
            5. Adding a touch of personality while maintaining professionalism
            
            Keep the core information but make it more complete, useful, and engaging.
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
        Generate an intelligent fallback response with personality using LLM.
        """
        try:
            prompt = f"""
            You are a helpful, knowledgeable FMCG supply chain expert with a warm, professional personality.
            The user is having trouble with their query and needs your assistance.
            
            User Query: "{user_input}"
            Query Type: {query_type}
            
            Create a response that:
            1. Shows empathy and understanding
            2. Demonstrates expertise in supply chain and FMCG
            3. Provides specific, actionable alternatives
            4. Uses a warm, professional tone with personality
            5. Shows you care about their success
            
            Personality traits to convey:
            - Knowledgeable but approachable
            - Patient and helpful
            - Confident in your expertise
            - Caring about the user's needs
            - Professional but friendly
            
            For different query types:
            - SKU_SPECIFIC: Help them find specific SKU information
            - ANALYTICAL: Guide them through analytical approaches
            - GENERAL_DATA: Help them explore data effectively
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
        Returns user-friendly suggestions only when helpful.
        """
        try:
            prompt = f"""
            Analyze this user query and determine if it needs improvement.
            
            User Query: "{user_input}"
            
            A query needs improvement if it is:
            - Too vague (e.g., "stuff", "what", "help")
            - Too broad (e.g., "show me everything")
            - Unclear about what information is needed
            - Missing specific details that would help get better results
            
            A query is GOOD and doesn't need improvement if it:
            - Is specific and clear (e.g., "tell me about SKU001", "show me all SKUs")
            - Asks for specific information (e.g., "which SKUs have negative profit?")
            - Is conversational but clear (e.g., "hello", "thanks")
            
            If the query is already good and clear, return "NO_SUGGESTIONS_NEEDED".
            If the query is vague or could be improved, provide 1-2 specific, actionable suggestions in a user-friendly format.
            
            Examples of good suggestions:
            - "You might also want to know: 'What are the current inventory levels for SKU001?'"
            - "Another useful question would be: 'Show me the financial performance of SKU001'"
            
            IMPORTANT: Make suggestions sound natural and helpful, not like internal analysis.
            Avoid phrases like "Consider:", "Try asking:", or "You could also ask:".
            Instead, use natural language like "You might also want to know:" or "Another useful question would be:".
            
            Return only the suggestions or "NO_SUGGESTIONS_NEEDED":
            """
            
            result = self.llm.invoke(prompt)
            if hasattr(result, 'content'):
                result_text = result.content
            elif hasattr(result, 'strip'):
                result_text = result.strip()
            else:
                result_text = str(result)
            
            if "NO_SUGGESTIONS_NEEDED" in result_text.upper():
                return None
            
            # Clean up the suggestion to make it user-friendly
            suggestion = result_text.strip()
            
            # Only return if it's a reasonable suggestion (not internal analysis)
            if len(suggestion) > 20 and len(suggestion) < 200:
                # Check for internal analysis indicators
                internal_indicators = [
                    'consider:', 'try asking:', 'you could also ask:', 'internal', 'analysis',
                    'user query', 'this user query', 'query analysis', 'debug',
                    'the user query', 'somewhat vague', 'assumes the user', 'does not specify',
                    'suggestions for improvement', 'more specific wording', 'alternative phrasings',
                    'related queries that might', 'clarifying what specific information'
                ]
                
                has_internal_indicators = any(indicator in suggestion.lower() for indicator in internal_indicators)
                
                if not has_internal_indicators:
                    return suggestion
                else:
                    print(f"🔍 SUPERVISOR: Filtered out internal analysis: {suggestion[:50]}...")
                    return None
            
            return None
            
        except Exception as e:
            print(f"🔍 SUPERVISOR: Query suggestion failed: {e}")
            return None

# Global supervisor instance
supervisor = ResponseSupervisor() 