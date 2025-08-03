from llm import llm
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

from solutions.tools.vector import get_movie_plot
from solutions.tools.cypher import cypher_qa
from solutions.tools.data_parser import parse_sku_data

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, SKUs, categories, demand plans, supply plans, and inventory information."),
        ("human", "{input}"),
    ]
)

fmcg_chat = chat_prompt | llm | StrOutputParser()

tools = [
    Tool.from_function(
        name="General Chat",
        description="For general FMCG supply chain chat not covered by other tools",
        func=fmcg_chat.invoke,
    ), 
    Tool.from_function(
        name="SKU Information Search",  
        description="Use this tool to find SKU data by passing the full user question. This tool searches for SKU information and returns plot text that contains all the SKU data.",
        func=get_movie_plot, 
    ),
    Tool.from_function(
        name="FMCG Data Query",
        description="Use this tool for complex Cypher queries and structured data retrieval from the FMCG database",
        func = cypher_qa
    ),
    Tool.from_function(
        name="SKU Data Parser",
        description="Use this tool to extract structured data from SKU plot text. This tool parses financial data, demand data, and can perform 'what-if' analysis with multipliers. Input should be the plot text from SKU Information Search.",
        func = parse_sku_data
    )
]

def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, SKUs, categories, demand plans, supply plans, and inventory information.

CRITICAL WORKFLOW RULES:
1. For ANY SKU question, you MUST follow this EXACT sequence:
   - Step 1: Use "SKU Information Search" ONCE to get the SKU data
   - Step 2: Use "SKU Data Parser" ONCE to extract structured information
   - Step 3: Provide "Final Answer" with the parsed data
   - STOP - Do not repeat any tool calls

2. NEVER repeat the same tool call - this causes infinite loops
3. NEVER call "SKU Information Search" more than once per question
4. ALWAYS use "SKU Data Parser" after getting data from "SKU Information Search"
5. You have a maximum of 3 tool calls per question

TOOL USAGE GUIDELINES:
- "SKU Information Search": Use for finding SKU data by passing the full user question
- "SKU Data Parser": Use for extracting structured data from SKU plot text
- "FMCG Data Query": Use for complex Cypher queries
- "General Chat": Use for general FMCG questions

SPECIFIC INSTRUCTIONS:
- When the user asks about inventory plans, demand data, or specific SKU information, use the Search → Parse → Answer workflow
- When the user asks "what-if" scenarios (like cost impact of demand changes), use the Search → Parse → Answer workflow
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

agent = create_react_agent(llm, tools, agent_prompt)
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
    
    # Debug: Print the final output
    print(f"DEBUG: Final response to display: '{output}'")
    print(f"DEBUG: Response type: {type(output)}")
    print(f"DEBUG: Response length: {len(output) if output else 0}")
    
    # Simplify: Return the raw output without additional processing
    return output.strip()
