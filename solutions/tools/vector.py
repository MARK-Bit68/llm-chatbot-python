import streamlit as st
from llm import llm, embeddings
from graph import graph

# tag::import_vector[]
from langchain_neo4j import Neo4jVector
# end::import_vector[]
# tag::import_chain[]
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
# end::import_chain[]

# tag::import_chat_prompt[]
from langchain_core.prompts import ChatPromptTemplate
# end::import_chat_prompt[]


# tag::vector[]
def get_neo4j_vector():
    """Get Neo4j vector index, creating it if it doesn't exist"""
    try:
        # Try to get existing index
        neo4jvector = Neo4jVector.from_existing_index(
            embeddings,                              # <1>
            graph=graph,                             # <2>
            index_name="skuPlots",                   # <3>
            node_label="SKU",                        # <4>
            text_node_property="plot",               # <5>
            embedding_node_property="plotEmbedding", # <6>
            retrieval_query="""
RETURN
    node.plot AS text,
    score,
    {
        title: node.name,
        sku_id: node.sku_id,
        tmdbId: node.sku_id,
        data_type: node.data_type
    } AS metadata
"""
        )
        return neo4jvector
    except ValueError as e:
        if "does not exist" in str(e):
            # Index doesn't exist, return None
            return None
        else:
            # Other error, re-raise
            raise e

# Initialize vector index (will be None if index doesn't exist)
neo4jvector = get_neo4j_vector()

# tag::retriever[]
retriever = neo4jvector.as_retriever() if neo4jvector else None
# end::retriever[]

# tag::prompt[]
instructions = (
    "You are a helpful FMCG supply chain assistant. Use the given context to answer questions about FMCG supply chain data. "
    "Always provide detailed information from the context when available. "
    "If the context contains relevant information, use it to provide a comprehensive answer. "
    "Only say you don't know if the context truly doesn't contain any relevant information. "
    "Context: {context}"
)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", instructions),
        ("human", "{input}"),
    ]
)
# end::prompt[]

# tag::chain[]
question_answer_chain = create_stuff_documents_chain(llm, prompt)
plot_retriever = create_retrieval_chain(
    retriever, 
    question_answer_chain
) if retriever else None
# end::chain[]

# tag::get_sku_data[]
def get_sku_data(input):
    if not neo4jvector or not retriever or not plot_retriever:
        return "Vector index not available. Please load data and create the vector index first."
    
    try:
        return plot_retriever.invoke({"input": input})
    except Exception as e:
        return f"Error accessing vector index: {str(e)}"
# end::get_sku_data[]
