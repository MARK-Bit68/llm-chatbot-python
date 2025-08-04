import streamlit as st
from llm import get_llm
from graph import get_graph_instance
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

# Define tools
tools = [
    Tool(
        name="Enhanced Database Query",
        func=enhanced_cypher_qa,
        description=f"Execute dynamic database queries to get precise information. Use this for questions about: ALL {DOMAIN_CONFIG['entity_plural']} (e.g., 'What {DOMAIN_CONFIG['entity_plural']} are in the Master Data?', 'Show me all {DOMAIN_CONFIG['entity_plural']}'), specific {DOMAIN_CONFIG['entity_plural']} (e.g., 'Tell me about [{DOMAIN_CONFIG['entity_id_field']}]'), categories, countries, price ranges, or any structured data queries. This tool can generate custom Cypher queries based on the question and is PREFERRED for queries about multiple {DOMAIN_CONFIG['entity_plural']} or general data exploration."
    ),
    Tool(
        name="Entity Information Search",
        func=get_sku_data,
        description=f"Search for {DOMAIN_CONFIG['entity_singular']} information using vector similarity. Use this for questions about general product information, categories, or when you need semantic similarity search. Use this as a FALLBACK when the Enhanced Database Query doesn't provide sufficient information."
    ),
    Tool(
        name="Entity Data Parser",
        func=parse_sku_data,
        description=f"Parse and structure {DOMAIN_CONFIG['entity_singular']} data for detailed analysis. Use this when you need to extract specific financial, demand, or inventory data from {DOMAIN_CONFIG['entity_singular']} information."
    ),
    Tool(
        name="General Chat",
        func=lambda x: f"I can help you with {DOMAIN_CONFIG['domain_name']} questions. Please ask about specific {DOMAIN_CONFIG['entity_plural']}, categories, pricing, inventory, or supply chain operations.",
        description=f"General conversation and guidance about {DOMAIN_CONFIG['domain_name']} topics."
    )
]

print(f"🔍 DEBUG: {len(tools)} tools created")

def get_memory(session_id):
    print(f"🔍 DEBUG: Creating memory for session {session_id}")
    return Neo4jChatMessageHistory(session_id=session_id, graph=get_graph_instance())

agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, inventory, demand, and financial data, answer questions about SKUs, and provide insights about inventory, demand, and financial data. Always provide detailed, accurate responses based on the available data.

CRITICAL TOOL SELECTION RULES:
1. For QUESTIONS ABOUT ALL SKUs (e.g., "What SKUs are in the Master Data?", "Show me all SKUs", "List all products"):
   - ALWAYS use "Enhanced Database Query" - it can query ALL SKUs in the database
   - Use queries like MATCH (sku:SKU) RETURN sku.sku_id, sku.name, sku.plot LIMIT 10

2. For SPECIFIC SKU queries (e.g., "Tell me about [sku_id]", "What is the category of [sku_id]"):
   - ALWAYS use "Enhanced Database Query" FIRST - it generates precise Cypher queries
   - This tool can create exact matches like MATCH (sku:SKU {{sku_id: '[sku_id]'}})

3. For GENERAL queries (e.g., "What categories do we have?", "Show me products with highest [metric]"):
   - Use "Enhanced Database Query" - it handles complex analytical queries

4. For SEMANTIC SEARCH queries (e.g., "Find products similar to [category]", "What products are like [sku_id]"):
   - Use "Entity Information Search" as a fallback for similarity-based searches

5. For DATA PARSING (after getting SKU data):
   - Use "Entity Data Parser" to extract structured information from raw data

TOOL USAGE GUIDELINES:
- "Enhanced Database Query": PREFERRED for ALL queries about SKUs, including "all SKUs" questions
- "Entity Information Search": Use only for semantic similarity searches
- "Entity Data Parser": Use for extracting structured data from SKU plot text
- "General Chat": Use for general FMCG supply chain questions

SPECIFIC INSTRUCTIONS:
- When the user asks about ALL SKUs (e.g., "What SKUs are in the Master Data?"), use "Enhanced Database Query" with a query that returns ALL SKUs
- When the user asks about a specific SKU (e.g., "Tell me about [sku_id]"), use "Enhanced Database Query"
- When the user asks about categories, countries, or analytical questions, use "Enhanced Database Query"
- Always provide complete, detailed information in your Final Answer
- Never say "I don't know" if you have data from the tools
- NEVER hallucinate SKU IDs - only use the actual data from the database

TOOLS:
------

You have access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

{agent_scratchpad}
""")

print("🔍 DEBUG: agent_prompt created with {tools} variable")

# Initialize agent as None - will be created when needed
agent = None
agent_executor = None
chat_agent = None

def get_agent():
    """Get agent, creating it if needed"""
    global agent, agent_executor, chat_agent
    print("🔍 DEBUG: get_agent() called")
    
    if agent is None:
        print("🔍 DEBUG: Creating new agent...")
        try:
            llm = get_llm()
            print(f"🔍 DEBUG: LLM created: {llm is not None}")
            print(f"🔍 DEBUG: Tools count: {len(tools)}")
            print(f"🔍 DEBUG: Agent prompt variables: {agent_prompt.input_variables}")
            
            # Debug: Show what tools are being passed
            print("🔍 DEBUG: Tools being passed to agent:")
            for i, tool in enumerate(tools):
                print(f"  Tool {i+1}: {tool.name} - {tool.description[:100]}...")
                print(f"    Full description: {tool.description}")
            
            # Debug: Show the actual prompt template
            print("🔍 DEBUG: Agent prompt template:")
            print(agent_prompt.template)
            
            agent = create_react_agent(llm, tools, agent_prompt)
            print("🔍 DEBUG: Agent created successfully")
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="generate"
            )
            print("🔍 DEBUG: AgentExecutor created successfully")
            
            chat_agent = RunnableWithMessageHistory(
                agent_executor,
                get_memory,
                input_messages_key="input",
                history_messages_key="chat_history",
            )
            print("🔍 DEBUG: ChatAgent created successfully")
        except Exception as e:
            print(f"❌ DEBUG: Error creating agent: {e}")
            raise e
    else:
        print("🔍 DEBUG: Using existing agent")
    
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
        return response.content.strip()
    except Exception as e:
        print(f"Error formatting text: {e}")
        return text

def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """
    print(f"🔍 DEBUG: generate_response() called with input: {user_input[:50]}...")

    try:
        # Use the agent executor directly for more control
        print("🔍 DEBUG: Getting agent...")
        agent_executor = get_agent()
        print("🔍 DEBUG: Agent obtained successfully")
        
        # Debug: Show what the agent will receive
        print(f"🔍 DEBUG: Agent will receive input: '{user_input}'")
        print(f"🔍 DEBUG: Agent has {len(agent_executor.tools)} tools available")
        
        print("🔍 DEBUG: Invoking agent...")
        response = agent_executor.invoke({"input": user_input})
        print("🔍 DEBUG: Agent invoked successfully")
    except Exception as e:
        # Handle parsing errors more gracefully
        error_msg = str(e)
        print(f"❌ DEBUG: Error in generate_response: {error_msg}")
        if "OUTPUT_PARSING_FAILURE" in error_msg or "Parsing LLM output" in error_msg:
            return "I encountered an error while processing your request. Please try rephrasing your question or ask for specific information about a SKU."
        return f"Error: {error_msg}"

    # Debug: Print the response structure
    print(f"🔍 DEBUG: Response type: {type(response)}")
    print(f"🔍 DEBUG: Response content: {response}")

    # Handle different response structures
    if isinstance(response, dict):
        if 'output' in response:
            output = response['output']
            print("🔍 DEBUG: Using 'output' from response")
        elif 'result' in response:
            output = response['result']
            print("🔍 DEBUG: Using 'result' from response")
        else:
            # Return the entire response as a string for debugging
            output = str(response)
            print("🔍 DEBUG: Using entire response as string")
    else:
        output = str(response)
        print("🔍 DEBUG: Using response as string")
    
    # Clean up the response - remove trailing backticks and extra whitespace
    output = output.strip()
    if output.startswith('```') and output.endswith('```'):
        output = output[3:-3].strip()
    
    print(f"🔍 DEBUG: Cleaned output: {output[:100]}...")
    
    # Use LLM to format the response intelligently
    print("🔍 DEBUG: Formatting response with LLM...")
    formatted_output = format_response_with_llm(output)
    print(f"🔍 DEBUG: Formatted output: {formatted_output[:100]}...")
    
    return formatted_output
