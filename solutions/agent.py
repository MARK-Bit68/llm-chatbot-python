from llm import get_llm
from graph import graph
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

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, answer questions about SKUs, and provide insights about inventory, demand, and financial data. Always provide detailed, accurate responses based on the available data."),
        ("human", "{input}"),
        ("assistant", "{agent_scratchpad}")
    ]
)

# Define tools
tools = [
    Tool(
        name="Enhanced Database Query",
        func=enhanced_cypher_qa,
        description=f"Execute dynamic database queries to get precise information. Use this for questions about: specific {DOMAIN_CONFIG['entity_plural']} (e.g., 'Tell me about [{DOMAIN_CONFIG['entity_id_field']}]'), all {DOMAIN_CONFIG['entity_plural']}, price ranges, categories, countries, or any structured data queries. This tool can generate custom Cypher queries based on the question and is PREFERRED for specific {DOMAIN_CONFIG['entity_singular']} queries."
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

def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, inventory, demand, and financial data, answer questions about SKUs, and provide insights about inventory, demand, and financial data. Always provide detailed, accurate responses based on the available data.

CRITICAL TOOL SELECTION RULES:
1. For SPECIFIC SKU queries (e.g., "Tell me about [sku_id]", "What is the category of [sku_id]"):
   - ALWAYS use "Enhanced Database Query" FIRST - it generates precise Cypher queries
   - This tool can create exact matches like MATCH (sku:SKU {{sku_id: '[sku_id]'}})
   - DO NOT use "Entity Information Search" for specific SKU queries

2. For GENERAL queries (e.g., "What categories do we have?", "Show me products with highest [metric]"):
   - Use "Enhanced Database Query" - it handles complex analytical queries

3. For SEMANTIC SEARCH queries (e.g., "Find products similar to [category]", "What products are like [sku_id]"):
   - Use "Entity Information Search" as a fallback for similarity-based searches

4. For DATA PARSING (after getting SKU data):
   - Use "Entity Data Parser" to extract structured information from raw data

TOOL USAGE GUIDELINES:
- "Enhanced Database Query": PREFERRED for specific SKU queries and analytical questions
- "Entity Information Search": Use only for semantic similarity searches
- "Entity Data Parser": Use for extracting structured data from SKU plot text
- "General Chat": Use for general FMCG supply chain questions

SPECIFIC INSTRUCTIONS:
- When the user asks about a specific SKU (e.g., "Tell me about [sku_id]"), use "Enhanced Database Query"
- When the user asks about all SKUs, categories, or analytical questions, use "Enhanced Database Query"
- When the user asks for similar products or semantic searches, use "Entity Information Search"
- Always provide complete, detailed information in your Final Answer
- Never say "I don't know" if you have data from the tools

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
Final Answer: [your complete detailed response here]
```

Begin!

New input: {input}
{agent_scratchpad}
""")

agent = create_react_agent(get_llm(), tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
    early_stopping_method="generate"
    )

chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

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

    try:
        # Use the agent executor directly for more control
        response = agent_executor.invoke({"input": user_input})
    except Exception as e:
        # Handle parsing errors more gracefully
        error_msg = str(e)
        if "OUTPUT_PARSING_FAILURE" in error_msg or "Parsing LLM output" in error_msg:
            return "I encountered an error while processing your request. Please try rephrasing your question or ask for specific information about a SKU."
        return f"Error: {error_msg}"

    # Debug: Print the response structure
    print(f"DEBUG: Response type: {type(response)}")
    print(f"DEBUG: Response content: {response}")

    # Handle different response structures
    if isinstance(response, dict):
        if 'output' in response:
            output = response['output']
        elif 'result' in response:
            output = response['result']
        else:
            # Return the entire response as a string for debugging
            output = str(response)
    else:
        output = str(response)
    
    # Clean up the response - remove trailing backticks and extra whitespace
    output = output.strip()
    if output.endswith('```'):
        output = output[:-3].strip()
    
    # If the response contains "Final Answer:", extract everything after it
    if "Final Answer:" in output:
        # Find the last occurrence of "Final Answer:" and get everything after it
        final_answer_index = output.rfind("Final Answer:")
        if final_answer_index != -1:
            output = output[final_answer_index + len("Final Answer:"):].strip()
            # Remove any trailing backticks or extra formatting
            output = output.replace('```', '').strip()
    
    # Use LLM to intelligently format the response
    formatted_output = format_response_with_llm(output)
    
    # Debug: Print the final output
    print(f"DEBUG: Final response to display: '{formatted_output}'")
    print(f"DEBUG: Response type: {type(formatted_output)}")
    print(f"DEBUG: Response length: {len(formatted_output) if formatted_output else 0}")
    
    return formatted_output.strip()
