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

IMPORTANT: Always end your response with "Final Answer:" followed by your actual answer. Include ALL relevant details in your response.

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
""")

agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
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

    response = chat_agent.invoke(
        {"input": user_input},
        {"configurable": {"session_id": get_session_id()}},)

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
    
    return output
