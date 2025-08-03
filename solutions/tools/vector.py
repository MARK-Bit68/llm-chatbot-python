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
# end::vector[]

# tag::retriever[]
retriever = neo4jvector.as_retriever()
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
)
# end::chain[]

# tag::get_sku_data[]
def get_sku_data(input):
    return plot_retriever.invoke({"input": input})
# end::get_sku_data[]
