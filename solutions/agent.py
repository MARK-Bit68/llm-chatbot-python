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
        description="For when you need to find information about SKUs and their properties",
        func=get_movie_plot, 
    ),
    Tool.from_function(
        name="FMCG Data Query",
        description="Provide information about FMCG data using Cypher queries",
        func = cypher_qa
    ),
    Tool.from_function(
        name="SKU Data Parser",
        description="Use this tool for 'what-if' scenarios, cost impact analysis, and demand calculations. Parse financial and demand data from SKU plot text for accurate numerical calculations. Input should be the plot text from a SKU node.",
        func = parse_sku_data
    )
]

def get_memory(session_id):
    return Neo4jChatMessageHistory(session_id=session_id, graph=graph)

agent_prompt = PromptTemplate.from_template("""
You are a helpful FMCG (Fast Moving Consumer Goods) supply chain assistant. You can help analyze supply chain data, SKUs, categories, demand plans, supply plans, and inventory information.

Be as helpful as possible and return as much information as possible.
Do not answer any questions that do not relate to FMCG supply chain data, SKUs, categories, or supply chain operations.

Do not answer any questions using your pre-trained knowledge, only use the information provided in the context.

IMPORTANT: When providing detailed information, include ALL the relevant data in your response. Do not just say "the information is provided above" - actually provide the detailed information in your response.

IMPORTANT: When using the SKU Information Search tool, pass the FULL user question as the input, not just the SKU code.

IMPORTANT: For basic SKU information requests (like "Tell me about SKU001"):
1. Use "SKU Information Search" to find the SKU and get its plot text
2. Use "SKU Data Parser" to extract and format the specific information requested
3. Provide a clear, structured response with the parsed data
4. ALWAYS include the complete extracted data in your Final Answer
5. NEVER say "I don't know" if you have data from the tools - use the data to provide a complete response
6. NEVER repeat the same tool call - move to the next step in the workflow

IMPORTANT: For "what-if" scenarios and cost impact analysis:
1. Use "SKU Information Search" to get the SKU's plot text
2. Use "SKU Data Parser" to extract data and apply the multiplier
3. Provide business analysis based on the parsed data
4. ALWAYS use the SKU Data Parser tool for volume/cost impact analysis - never do manual calculations
5. NEVER repeat the same tool call - follow the sequence: Search → Parse → Answer

IMPORTANT: Tool Selection Guidelines:
- Use "SKU Information Search" for general SKU information and similarity search
- Use "FMCG Data Query" for complex Cypher queries and structured data retrieval
- Use "SKU Data Parser" for data extraction and "what-if" scenarios
- Use "General Chat" for general FMCG supply chain questions

IMPORTANT: When you get data from SKU Information Search, ALWAYS use SKU Data Parser to extract structured information before providing your final answer.

CRITICAL WORKFLOW: For any SKU question, follow this exact sequence:
1. Use "SKU Information Search" (ONCE)
2. Use "SKU Data Parser" (ONCE) 
3. Provide "Final Answer" (ONCE)
4. STOP - Do not repeat any tool calls

IMPORTANT: For "what-if" questions about volume changes, cost impacts, or demand multipliers, you MUST use the SKU Data Parser tool with the plot text and multiplier as parameters.

CRITICAL: NEVER do manual calculations in your Final Answer. Always use the SKU Data Parser tool for any numerical analysis or "what-if" scenarios.

CRITICAL: When the user asks about a specific SKU (like SKU001), make sure to use that SKU's data, not any other SKU's data.

CRITICAL: After using SKU Information Search, you MUST use SKU Data Parser before providing your final answer. Do not repeat the same tool call.

CRITICAL: You have a maximum of 3 tool calls. Use them wisely: 1) SKU Information Search, 2) SKU Data Parser, 3) Final Answer.

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

IMPORTANT: Always end your response with "Final Answer:" followed by your actual answer. Include ALL relevant details in your response. NEVER say "I don't know" or "the information is not available" if you have data from the tools.

Begin!

New input: {input}
{agent_scratchpad}
""")

agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
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
