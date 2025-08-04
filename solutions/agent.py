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

# Define tools
# 1. Update tool descriptions
# Enhanced Database Query: For ANY question about a specific SKU (e.g., 'Tell me about SKU001'), you MUST use this tool. For ALL SKUs, you MUST use this tool. For categories, analytics, etc., use this tool.
tools = [
    Tool(
        name="Enhanced Database Query",
        func=enhanced_cypher_qa,
        description="For ANY question about a specific SKU (e.g., 'Tell me about SKU001'), you MUST use this tool. For ALL SKUs (e.g., 'What SKUs are in the Master Data?'), you MUST use this tool. For questions about categories, analytics, or general data, use this tool. This tool generates Cypher queries and returns detailed data. DO NOT use any other tool for specific SKU or all SKU queries."
    ),
    Tool(
        name="Entity Information Search",
        func=get_sku_data,
        description="Use ONLY for semantic similarity or fuzzy search when the Enhanced Database Query does not provide sufficient information. NEVER use for specific SKU or all SKU queries."
    ),
    Tool(
        name="Entity Data Parser",
        func=parse_sku_data,
        description="Use ONLY to extract structured data from raw SKU data after using Enhanced Database Query."
    ),
    Tool(
        name="General Chat",
        func=lambda x: f"I can help you with {DOMAIN_CONFIG['domain_name']} questions. Please ask about specific {DOMAIN_CONFIG['entity_plural']}, categories, pricing, inventory, or supply chain operations.",
        description=f"General conversation and guidance about {DOMAIN_CONFIG['domain_name']} topics. NEVER use for SKU queries."
    )
]

print(f"🔍 DEBUG: {len(tools)} tools created")

def get_memory(session_id):
    print(f"🔍 DEBUG: Creating memory for session {session_id}")
    return Neo4jChatMessageHistory(session_id=session_id, graph=get_graph())

# 2. Add concrete prompt examples for both all SKUs and single SKU queries
agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, answer questions about SKUs, and provide insights about inventory, demand, and financial data. Always provide detailed, accurate responses based on the available data.

CRITICAL: For ANY question about SKUs (including "Tell me about SKU001", "What SKUs are in the Master Data?", etc.), you MUST use the Enhanced Database Query tool. You CANNOT give a generic response without using a tool.

MANDATORY: You MUST use a tool for EVERY question. You are NOT allowed to give generic responses or greetings. You MUST follow the ReAct format exactly.

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

IMPORTANT: When you receive an Observation from a tool that contains detailed data (like tables, lists, or structured information), you MUST copy the entire content of the last Observation exactly, with no changes, into your Final Answer. Do not summarize, rewrite, or omit any part of it. If the Observation contains tables, lists, or formatted data, include all of it exactly as provided.

EXAMPLES:
User: What SKUs are in the Master Data?

```
Thought: Do I need to use a tool? Yes
Action: Enhanced Database Query
Action Input: What SKUs are in the Master Data?
Observation: | SKU ID | Name | Category |
|--------|------|----------|
| SKU001 | ...  | Legumes  |
| SKU002 | ...  | Nuts     |
... (table continues) ...

Thought: Do I need to use a tool? No
Final Answer: | SKU ID | Name | Category |
|--------|------|----------|
| SKU001 | ...  | Legumes  |
| SKU002 | ...  | Nuts     |
... (table continues) ...
```

User: Tell me about SKU001

```
Thought: Do I need to use a tool? Yes
Action: Enhanced Database Query
Action Input: Tell me about SKU001
Observation: | SKU ID | Name | Category | ... (all details) ... |
|--------|------|----------| ... |
| SKU001 | ...  | Legumes  | ... |

Thought: Do I need to use a tool? No
Final Answer: | SKU ID | Name | Category | ... (all details) ... |
|--------|------|----------| ... |
| SKU001 | ...  | Legumes  | ... |
```

If you do not follow this exactly, your answer will be rejected.

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
            
            agent = create_react_agent(llm, tools, agent_prompt)
            print(f"🔍 DEBUG: Agent created: {agent is not None}")
            
            agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
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

    try:
        agent_executor = get_agent()
        response = agent_executor.invoke({"input": user_input})
    except Exception as e:
        error_msg = str(e)
        print(f"❌ DEBUG: Error in generate_response: {error_msg}")
        
        if "Agent stopped due to iteration limit" in error_msg or "Invalid Format" in error_msg:
            reset_agent()
            try:
                agent_executor = get_agent()
                response = agent_executor.invoke({"input": user_input})
            except Exception as e2:
                print(f"❌ DEBUG: Agent retry failed: {e2}")
                return "I encountered an error while processing your request. Please try rephrasing your question."
        
        if "OUTPUT_PARSING_FAILURE" in error_msg or "Parsing LLM output" in error_msg:
            return "I encountered an error while processing your request. Please try rephrasing your question or ask for specific information about a SKU."
        return f"Error: {error_msg}"

    # Log tool selection and agent behavior
    if isinstance(response, dict) and 'intermediate_steps' in response:
        steps = response['intermediate_steps']
        print(f"🔍 DEBUG: Agent intermediate steps: {steps}")
        for step in steps:
            if isinstance(step, tuple) and len(step) == 2 and step[0] == 'Action':
                print(f"🔍 DEBUG: Tool selected: {step[1]}")
            elif isinstance(step, tuple) and len(step) == 2 and step[0] == 'Action Input':
                print(f"🔍 DEBUG: Action input: {step[1]}")
            elif isinstance(step, tuple) and len(step) == 2 and step[0] == 'Observation':
                print(f"🔍 DEBUG: Observation preview: {str(step[1])[:200]}...")
    else:
        print(f"🔍 DEBUG: No intermediate steps found in response")
        print(f"🔍 DEBUG: Response keys: {response.keys() if isinstance(response, dict) else 'Not a dict'}")

    # Enforce verbatim Observation in Final Answer if present
    if isinstance(response, dict) and 'output' in response and 'intermediate_steps' in response:
        steps = response['intermediate_steps']
        if steps and isinstance(steps, list):
            for step in reversed(steps):
                if isinstance(step, tuple) and len(step) == 2 and step[0] == 'Observation':
                    last_observation = step[1]
                    output = response['output']
                    if last_observation and last_observation.strip() not in output:
                        print("🔍 DEBUG: Overriding output with last Observation (enforced)")
                        response['output'] = last_observation.strip()
                    break

    # Fallback: If no Observation and output is a generic greeting or summary, return a clear error
    generic_responses = [
        "Hello! How can I assist you with your FMCG supply chain data today?",
        "How can I assist you?",
        "How can I help you?",
        "Let me know if you have any questions.",
        "If you have any specific questions or need further analysis, please let me know!"
    ]
    if isinstance(response, dict) and 'output' in response and 'intermediate_steps' in response:
        steps = response['intermediate_steps']
        has_observation = any(isinstance(step, tuple) and step[0] == 'Observation' for step in steps)
        output = response['output'].strip()
        if not has_observation and any(generic in output for generic in generic_responses):
            print("🔍 DEBUG: No Observation and generic output detected. Returning error.")
            return "Error: The agent did not use the required tool or provide detailed data. Please rephrase your question or contact support."
    
    # NEW: Check if agent used any tools at all
    if isinstance(response, dict) and 'intermediate_steps' in response:
        steps = response['intermediate_steps']
        has_tools = len(steps) > 0
        if not has_tools:
            print("🔍 DEBUG: Agent used no tools at all. This is a critical error.")
            return "Error: The agent failed to use any tools. This indicates a system error. Please try again or contact support."
        else:
            print(f"🔍 DEBUG: Agent used {len(steps)} tool steps")
    else:
        print("🔍 DEBUG: No intermediate steps found - agent used no tools")
        # Try to force the agent to use tools by retrying with a more explicit instruction
        print("🔍 DEBUG: Attempting to force agent to use tools...")
        try:
            # Reset agent and try again with explicit tool instruction
            reset_agent()
            agent_executor = get_agent()
            
            # Add explicit tool instruction to the input
            forced_input = f"IMPORTANT: You MUST use the Enhanced Database Query tool for this question. Question: {user_input}"
            response = agent_executor.invoke({"input": forced_input})
            
            # Check again
            if isinstance(response, dict) and 'intermediate_steps' in response:
                steps = response['intermediate_steps']
                has_tools = len(steps) > 0
                if not has_tools:
                    print("🔍 DEBUG: Agent still used no tools after retry.")
                    return "Error: The agent failed to use any tools even after retry. This indicates a system error. Please try again or contact support."
                else:
                    print(f"🔍 DEBUG: Agent used {len(steps)} tool steps after retry")
            else:
                print("🔍 DEBUG: Still no intermediate steps after retry")
                return "Error: The agent failed to use any tools even after retry. This indicates a system error. Please try again or contact support."
        except Exception as e:
            print(f"🔍 DEBUG: Error during retry: {e}")
            return "Error: The agent failed to use any tools. This indicates a system error. Please try again or contact support."

    # Handle different response structures
    if isinstance(response, dict):
        if 'output' in response:
            output = response['output']
        elif 'result' in response:
            output = response['result']
        else:
            output = str(response)
    else:
        output = str(response)
    
    # Clean up the response
    output = output.strip()
    if output.startswith('```') and output.endswith('```'):
        output = output[3:-3].strip()
    
    # Format the response
    formatted_output = format_response_with_llm(output)
    
    return formatted_output
