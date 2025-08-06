import streamlit as st
from llm import get_llm
from solutions.graph import get_graph
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain.schema import StrOutputParser
from langchain.tools import Tool
from langchain_neo4j import Neo4jChatMessageHistory
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from utils import get_session_id

from solutions.tools.vector import get_sku_data
from solutions.tools.cypher import enhanced_cypher_qa
from solutions.tools.data_parser import parse_sku_data

# Remove extraneous debug statements, keep only essential ones for logic flow debugging
print("🔍 DEBUG: solutions/agent.py imported successfully")

# Domain configuration - can be easily changed for different domains
DOMAIN_CONFIG = {
    "domain_name": "FMCG (Fast Moving Consumer Goods) supply chain",
    "entity_type": "SKU",
    "entity_label": "SKU",
    "entity_id_field": "sku_id",
    "domain_expertise": "supply chain data, inventory, demand, and financial data",
    "entity_plural": "SKUs",
    "entity_singular": "SKU"
}

print("🔍 DEBUG: DOMAIN_CONFIG created")

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, answer questions about SKUs, and provide insights about inventory, demand, and financial data. Always provide detailed, accurate responses based on the available data."),
        ("human", "{input}"),
        ("assistant", "{agent_scratchpad}")
    ]
)

print("🔍 DEBUG: chat_prompt created")

# Define tools with clear, simple names and descriptions
tools = [
    Tool(
        name="Enhanced Database Query",
        func=enhanced_cypher_qa,
        description="Use this tool for ANY question about SKUs, supply chain analysis, or data queries. Input: the question (e.g., 'Tell me about SKU001', 'Show me supply chain gaps', 'What SKUs are in the master data?', 'Show me all SKUs', 'Which SKUs have inventory shortages?', 'Show me demand vs supply analysis', 'Which SKUs are most profitable?', 'Show me SKUs with low inventory'). This tool queries the database and returns comprehensive executive-level information with detailed analysis. CRITICAL: When you receive this data, you MUST present the ENTIRE executive dashboard EXACTLY as provided, including ALL sections: Product Overview, Financial Performance, Inventory Management, Monthly Analysis, Strategic Insights, and Executive Recommendations. NEVER summarize, condense, or rephrase this data - present the COMPLETE dashboard with all tables, metrics, and insights exactly as received. IMPORTANT: If you see '# 📊 Executive Dashboard:' or '# 📊 Executive Summary:' in the response, return that EXACT data without any changes. CRITICAL: DO NOT SUMMARIZE EXECUTIVE DASHBOARD DATA - RETURN IT EXACTLY AS RECEIVED."
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
        name="General Chat",
        func=lambda x: f"I can help you with {DOMAIN_CONFIG['domain_name']} questions. Please ask about specific {DOMAIN_CONFIG['entity_plural']}, categories, pricing, inventory, or supply chain operations.",
        description=f"General conversation about {DOMAIN_CONFIG['domain_name']} topics. Input: general questions. NEVER use for SKU queries."
    )
]

print(f"🔍 DEBUG: {len(tools)} tools created")

def get_memory(session_id):
    print(f"🔍 DEBUG: Creating memory for session {session_id}")
    return Neo4jChatMessageHistory(session_id=session_id, graph=get_graph())

# 2. Add concrete prompt examples for both all SKUs and single SKU queries
agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, answer questions about SKUs, and provide insights about inventory, demand, and financial data.

You have access to the following tools:
{tools}

CRITICAL RULES FOR TOOL USAGE:
1. For ANY data queries about SKUs, supply chain, analytics, or business intelligence, you MUST use the Enhanced Database Query tool
2. For greetings, casual conversation, or non-data requests, respond directly with "Final Answer:"
3. ALWAYS use proper ReAct format: "Action:" then tool name, then "Action Input:" then your query
4. For direct responses: "Final Answer:" then your response
5. NEVER include "Invalid Format" or error messages in your response
6. NEVER loop or repeat the same action multiple times
7. If a tool fails, try a different approach or provide a helpful response
8. For supply chain analysis, inventory questions, or SKU-specific queries, ALWAYS use the Enhanced Database Query tool
9. For general data requests like "show me all SKUs" or "list products", use the Enhanced Database Query tool
10. For analytical queries like "gaps", "shortages", "profitability", use the Enhanced Database Query tool

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

Remember: You are delivering executive dashboard reports, not answering simple questions. When you receive rich data, present it exactly as received. NEVER summarize executive dashboard data. COPY AND PASTE THE ENTIRE EXECUTIVE DASHBOARD RESPONSE.

Begin!

{agent_scratchpad}
""")

print("🔍 DEBUG: agent_prompt created with {tools} variable")

# Initialize agent as None - will be created when needed
agent = None
agent_executor = None
chat_agent = None

def reset_agent():
    """Reset the agent to force recreation"""
    global agent, agent_executor, chat_agent
    print("🔍 DEBUG: Resetting agent...")
    agent = None
    agent_executor = None
    chat_agent = None

def get_agent():
    """Get agent, creating it if needed"""
    global agent, agent_executor, chat_agent
    
    if agent is None:
        try:
            llm = get_llm()
            print(f"🔍 DEBUG: Creating agent with LLM: {llm is not None}")
            print(f"🔍 DEBUG: Tools available: {len(tools)}")
            for i, tool in enumerate(tools):
                print(f"🔍 DEBUG: Tool {i+1}: {tool.name}")
            
            # Create tool names string for the prompt
            tool_names = ", ".join([tool.name for tool in tools])
            print(f"🔍 DEBUG: Tool names: {tool_names}")

            # Use the standard LangChain hub prompt with better error handling
            from langchain import hub
            prompt = hub.pull("hwchase17/react")
            
            # Create agent with the standard hub prompt
            agent = create_react_agent(llm, tools, prompt)
            
            # Add comprehensive response instruction to the prompt
            def enhance_prompt_with_executive_instructions(prompt):
                """Enhance the prompt to encourage comprehensive executive responses"""
                if hasattr(prompt, 'messages') and prompt.messages:
                    # Find the system message and enhance it
                    for message in prompt.messages:
                        if message.type == "system":
                            message.content += """

CRITICAL EXECUTIVE RESPONSE REQUIREMENTS:
1. When you receive comprehensive SKU data with executive dashboard format, PRESENT THE ENTIRE DASHBOARD AS-IS
2. NEVER summarize, condense, or rephrase the executive dashboard data
3. If the data includes sections like "📊 Executive Summary", "💰 Financial Performance", "📦 Inventory Management", "📈 Monthly Demand Analysis", "🎯 Strategic Insights", and "💡 Executive Recommendations" - PRESENT ALL OF THEM
4. Include ALL tables, metrics, and detailed analysis exactly as provided
5. For inventory questions, show the complete monthly demand analysis table with all 18 months
6. For financial questions, include all revenue, cost, margin, and profitability calculations
7. Present the data in the exact same professional format with all markdown formatting
8. If charts or visualizations are included, present them as well
9. The goal is to provide COMPLETE executive-level business intelligence, not summaries
10. Only add brief contextual analysis if the question specifically asks for interpretation
11. IMPORTANT: If you receive a comprehensive executive dashboard response from a tool, RETURN THAT EXACT RESPONSE without any modification or summary
12. CRITICAL: When you receive data starting with "# 📊 Executive Summary:", return that EXACT data without any changes, summaries, or modifications
13. CRITICAL: If you see "# 📊 Executive Summary:" in the tool response, copy and paste that ENTIRE response without any changes
14. CRITICAL: DO NOT SUMMARIZE - PRESENT THE COMPLETE EXECUTIVE DASHBOARD

Remember: You are delivering executive dashboard reports, not answering simple questions. When you receive rich data, present it exactly as received. NEVER summarize executive dashboard data. COPY AND PASTE THE ENTIRE EXECUTIVE DASHBOARD RESPONSE."""
                return prompt
            
            # Apply the enhanced prompt
            agent = create_react_agent(llm, tools, enhance_prompt_with_executive_instructions(prompt))
            print(f"🔍 DEBUG: Agent created: {agent is not None}")
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,  # Increased from 5 to 10 for complex queries
                return_intermediate_steps=True
            )
            print(f"🔍 DEBUG: AgentExecutor created: {agent_executor is not None}")
            
            chat_agent = RunnableWithMessageHistory(
                agent_executor,
                get_memory,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            print(f"🔍 DEBUG: ChatAgent created: {chat_agent is not None}")
        except Exception as e:
            print(f"❌ DEBUG: Error creating agent: {e}")
            raise e
    
    return agent_executor

def format_response_with_llm(text):
    """
    Use LLM to intelligently format and clean text response with robust concatenation fixing
    """
    # Single-stage intelligent formatting that handles both concatenation and general formatting
    formatting_prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a text formatting expert. Your task is to clean and format text responses to make them more readable while preserving all important information.

CRITICAL RULES:
1. **Detect and fix concatenated words**: Look for words that are stuck together without spaces and separate them intelligently
   - Examples: "indicatesapotential" → "indicates a potential", "unitcost" → "unit cost", "profitmargin" → "profit margin"
   - Use your understanding of English to determine where words should be separated
   - Don't separate proper nouns, codes, or numbers (e.g., "SKU001", "$10.90", "CountryB")

2. **Add proper spacing around codes and identifiers**:
   - "SKU001" → "SKU 001"
   - "WH1" → "WH 1"
   - "Product123" → "Product 123"

3. **Preserve all markdown formatting**:
   - Keep bold formatting (**text**)
   - Keep bullet points (- item)
   - Keep line breaks and structure
   - Keep tables and formatting

4. **Maintain readability**:
   - Ensure consistent spacing
   - Remove excessive line breaks
   - Keep the original meaning and structure intact

5. **Be intelligent about context**:
   - Don't change domain-specific terms that are intentionally concatenated
   - Don't change numbers, currency, or codes
   - Focus on making text more readable while preserving accuracy

Return the cleaned and formatted text:"""),
        ("human", "{text}")
    ])
    
    try:
        chain = formatting_prompt | get_llm()
        response = chain.invoke({"text": text})
        formatted_text = response.content.strip()
        return formatted_text
    except Exception as e:
        print(f"Error formatting text: {e}")
        return text

# 3. Add a fallback in code: if no Observation and output is a generic greeting or summary, return a clear error message
# 4. Log tool selection if possible

def generate_response(user_input):
    print(f"🔍 DEBUG: generate_response() called with input: {user_input[:50]}...")

    # ROBUST OUTER EDGE ERROR HANDLING SYSTEM WITH SUPERVISOR
    try:
        # STEP 1: Pre-process the input to detect query type
        query_type = analyze_query_type(user_input)
        print(f"🔍 DEBUG: Detected query type: {query_type}")
        
        # STEP 2: Try the primary agent approach
        agent_executor = get_agent()
        response = agent_executor.invoke({"input": user_input})
        
        # STEP 3: Validate the response and apply robust error handling
        validated_response = validate_and_fix_response(response, user_input, query_type)
        
        if validated_response:
            # STEP 4: SUPERVISOR LAYER - Sanity check and enhance response
            from solutions.supervisor import supervisor
            supervised_response = supervisor.supervise_response(user_input, validated_response, query_type)
            
            # STEP 5: Only apply issue detection if supervisor didn't already handle it
            if supervised_response == validated_response:
                # Supervisor didn't change the response, so it's likely good
                return supervised_response
            else:
                # Supervisor modified the response, apply final checks
                final_response = supervisor.detect_and_fix_common_issues(user_input, supervised_response)
                return final_response
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ DEBUG: Primary agent failed: {error_msg}")
        
        # STEP 6: Apply intelligent fallback based on query type
        fallback_response = apply_intelligent_fallback(user_input, query_type, error_msg)
        if fallback_response:
            # Apply supervisor to fallback as well
            from solutions.supervisor import supervisor
            supervised_fallback = supervisor.supervise_response(user_input, fallback_response, query_type)
            return supervisor.detect_and_fix_common_issues(user_input, supervised_fallback)
            
        # STEP 7: Final fallback - never show ugly errors to user
        final_error_response = create_user_friendly_error(user_input, error_msg)
        from solutions.supervisor import supervisor
        return supervisor.detect_and_fix_common_issues(user_input, final_error_response)

def analyze_query_type(user_input):
    """Analyze the type of query using LLM instead of hard-coded patterns"""
    try:
        from llm import get_llm
        llm = get_llm()
        
        prompt = f"""
        Analyze this user query and classify it into one of these categories:
        
        - SKU_SPECIFIC: Queries about specific SKUs, products, or individual items
        - ANALYTICAL: Queries about analysis, trends, patterns, gaps, shortages, financial performance
        - GENERAL_DATA: Queries asking for lists, overviews, summaries, or general data
        - CONVERSATIONAL: Greetings, thanks, casual conversation, or help requests
        - UNKNOWN: Queries that don't fit the above categories
        
        User Query: "{user_input}"
        
        Return only the category name (SKU_SPECIFIC, ANALYTICAL, GENERAL_DATA, CONVERSATIONAL, or UNKNOWN):
        """
        
        result = llm.invoke(prompt)
        if hasattr(result, 'content'):
            result_text = result.content
        elif hasattr(result, 'strip'):
            result_text = result.strip()
    else:
            result_text = str(result)
        
        # Clean up the response
        category = result_text.strip().upper()
        valid_categories = ["SKU_SPECIFIC", "ANALYTICAL", "GENERAL_DATA", "CONVERSATIONAL", "UNKNOWN"]
        
        if category in valid_categories:
            return category
        else:
            return "UNKNOWN"
            
    except Exception as e:
        print(f"🔍 DEBUG: Query type analysis failed: {e}")
        return "UNKNOWN"

def validate_and_fix_response(response, user_input, query_type):
    """Validate the agent response and apply fixes if needed"""
    
    # Check if response has the expected structure
    if not isinstance(response, dict):
        print("🔍 DEBUG: Response is not a dict, attempting to fix...")
        return None
    
    if 'intermediate_steps' not in response:
        print("🔍 DEBUG: No intermediate steps found, agent failed to use tools")
        return None
    
        steps = response['intermediate_steps']
    
    # Check if agent used any tools
    if len(steps) == 0:
        print("🔍 DEBUG: Agent used no tools - checking if this is acceptable")
        # For conversational queries, it's okay to not use tools
        if query_type == "CONVERSATIONAL":
            print("🔍 DEBUG: Conversational query - no tools needed")
            if 'output' in response:
                return response['output']
            return None
        else:
            print("🔍 DEBUG: Non-conversational query with no tools - critical failure")
            return None
    
    # Check if we got a valid observation
    has_valid_observation = False
    for step in steps:
        if isinstance(step, tuple) and len(step) == 2 and step[0] == 'Observation':
            observation = step[1]
            if observation and len(str(observation).strip()) > 10:  # Meaningful response
                has_valid_observation = True
                break
    
    # Also check if we have a valid output even without observation
    if 'output' in response:
        output = response['output']
        if output and len(str(output).strip()) > 10:
            has_valid_observation = True
    
    if not has_valid_observation:
        print("🔍 DEBUG: No valid observation found")
        return None
    
    # Check output quality
    if 'output' in response:
        output = response['output']
        
        # For now, skip generic response detection in validation to avoid conflicts with supervisor
        # The supervisor will handle this more intelligently
    
    # Response looks good
    return response.get('output', str(response))

def apply_intelligent_fallback(user_input, query_type, error_msg):
    """Apply intelligent fallback based on query type"""
    
    print(f"🔍 DEBUG: Applying intelligent fallback for query type: {query_type}")
    
    try:
        if query_type == "SKU_SPECIFIC":
            # Try direct database query for SKU information
            return handle_sku_fallback(user_input)
            
        elif query_type == "ANALYTICAL":
            # Try analytical query fallback
            return handle_analytical_fallback(user_input)
            
        elif query_type == "GENERAL_DATA":
            # Try general data query fallback
            return handle_general_data_fallback(user_input)
            
        elif query_type == "CONVERSATIONAL":
            # Handle conversational queries
            return handle_conversational_fallback(user_input)
            
        else:
            # Unknown query type - try general approach
            return handle_unknown_query_fallback(user_input)
            
    except Exception as e:
        print(f"❌ DEBUG: Fallback failed: {e}")
        return None

def handle_sku_fallback(user_input):
    """Handle SKU-specific queries when agent fails"""
    try:
        from solutions.tools.cypher import enhanced_cypher_qa
        result = enhanced_cypher_qa(user_input)
        if result and not result.startswith("Error"):
            return result
    except Exception as e:
        print(f"❌ DEBUG: SKU fallback failed: {e}")
    return None

def handle_analytical_fallback(user_input):
    """Handle analytical queries when agent fails"""
    try:
        # For supply chain gaps, try a specific analytical query
        if 'gap' in user_input.lower() or 'supply chain' in user_input.lower():
            from solutions.tools.cypher import enhanced_cypher_qa
            analytical_query = "Show me SKUs with supply chain gaps, inventory shortages, or demand-supply mismatches"
            result = enhanced_cypher_qa(analytical_query)
            if result and not result.startswith("Error"):
                return f"Based on your query about supply chain gaps, here's the analysis:\n\n{result}"
    except Exception as e:
        print(f"❌ DEBUG: Analytical fallback failed: {e}")
    return None

def handle_general_data_fallback(user_input):
    """Handle general data queries when agent fails"""
    try:
        from solutions.tools.cypher import enhanced_cypher_qa
        # Try to get general SKU information
        result = enhanced_cypher_qa("Show me all SKUs in the database")
        if result and not result.startswith("Error"):
            return f"Here's the general data you requested:\n\n{result}"
    except Exception as e:
        print(f"❌ DEBUG: General data fallback failed: {e}")
    return None

def handle_conversational_fallback(user_input):
    """Handle conversational queries"""
    user_input_lower = user_input.lower()
    
    if 'hello' in user_input_lower or 'hi' in user_input_lower:
        return "Hello! I'm your FMCG supply chain assistant. I can help you with:\n\n" + \
               "• SKU-specific information (e.g., 'Tell me about SKU001')\n" + \
               "• Supply chain analysis (e.g., 'Show me supply chain gaps')\n" + \
               "• General data queries (e.g., 'Show me all SKUs')\n" + \
               "• Financial analysis (e.g., 'Which SKUs are most profitable?')\n\n" + \
               "What would you like to know?"
    
    elif 'help' in user_input_lower:
        return "I'm here to help! Here are some things I can do:\n\n" + \
               "• **SKU Information**: 'Tell me about SKU001'\n" + \
               "• **Supply Chain Analysis**: 'Show me supply chain gaps'\n" + \
               "• **Data Queries**: 'Show me all SKUs'\n" + \
               "• **Financial Analysis**: 'Which SKUs are most profitable?'\n\n" + \
               "Just ask me anything about your FMCG supply chain data!"
    
    elif 'invalid' in user_input_lower:
        return "I'm sorry, but I couldn't understand your request. Please try:\n\n" + \
               "• 'Tell me about SKU001' (for specific SKU information)\n" + \
               "• 'Show me all SKUs' (for general data)\n" + \
               "• 'Show me supply chain gaps' (for analysis)\n" + \
               "• 'Which SKUs are most profitable?' (for financial analysis)"
    
    else:
        return "Hello! I'm your FMCG supply chain assistant. How can I help you today?"

def handle_unknown_query_fallback(user_input):
    """Handle unknown query types"""
    try:
        from solutions.tools.cypher import enhanced_cypher_qa
        # Try a general query to see if we can get any data
        result = enhanced_cypher_qa("Show me all SKUs")
        if result and not result.startswith("Error"):
            return f"I found some data that might be relevant to your query. Here's what I can show you:\n\n{result}"
    except Exception as e:
        print(f"❌ DEBUG: Unknown query fallback failed: {e}")
    return None

def create_user_friendly_error(user_input, error_msg):
    """Create a user-friendly error message that never shows technical details"""
    
    print(f"🔍 DEBUG: Creating user-friendly error for: {user_input}")
    print(f"🔍 DEBUG: Technical error: {error_msg}")
    
    # Provide helpful guidance based on the query
    if 'sku' in user_input.lower():
        return "I'm having trouble accessing specific SKU information right now. Please try:\n\n" + \
               "• 'Tell me about SKU001' (for a specific SKU)\n" + \
               "• 'Show me all SKUs' (for general data)\n" + \
               "• 'Which SKUs are most profitable?' (for analysis)"
    
    elif 'gap' in user_input.lower() or 'supply chain' in user_input.lower():
        return "I'm having trouble analyzing supply chain gaps right now. Please try:\n\n" + \
               "• 'Show me SKUs with low inventory' (for inventory issues)\n" + \
               "• 'Which SKUs have supply shortages?' (for supply issues)\n" + \
               "• 'Show me demand vs supply analysis' (for mismatches)"
    
    elif 'all' in user_input.lower() or 'list' in user_input.lower():
        return "I'm having trouble retrieving the full data list right now. Please try:\n\n" + \
               "• 'Show me all SKUs' (for complete list)\n" + \
               "• 'Tell me about SKU001' (for specific SKU)\n" + \
               "• 'Which categories do we have?' (for categories)"
    
    else:
        return "I'm having trouble processing your request right now. Please try:\n\n" + \
               "• 'Tell me about SKU001' (for specific SKU information)\n" + \
               "• 'Show me all SKUs' (for general data)\n" + \
               "• 'Show me supply chain gaps' (for analysis)\n" + \
               "• 'Which SKUs are most profitable?' (for financial analysis)\n\n" + \
               "If the problem persists, please try rephrasing your question or contact support."
