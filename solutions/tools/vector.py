import streamlit as st
from llm import get_llm, get_embeddings
from graph import get_graph_instance

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

# Initialize as None - will be created when needed
neo4jvector = None
retriever = None
plot_retriever = None

# tag::vector[]
def get_neo4j_vector():
    """Get Neo4j vector index, creating it if it doesn't exist"""
    global neo4jvector, retriever, plot_retriever
    
    if neo4jvector is None:
        embeddings_instance = get_embeddings()
        if not embeddings_instance:
            print("Warning: Embeddings not available")
            return None
            
        try:
            # Try to get existing index
            neo4jvector = Neo4jVector.from_existing_index(
                embeddings_instance,                      # <1>
                graph=get_graph_instance(),                             # <2>
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
            
            # Create retriever and chain
            retriever = neo4jvector.as_retriever() if neo4jvector else None
            
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
            question_answer_chain = create_stuff_documents_chain(get_llm(), prompt)
            plot_retriever = create_retrieval_chain(
                retriever, 
                question_answer_chain
            ) if retriever else None
            # end::chain[]
            
        except ValueError as e:
            if "does not exist" in str(e):
                # Index doesn't exist, return None
                return None
            else:
                # Other error, re-raise
                raise e
    
    return neo4jvector

# tag::get_sku_data[]
def get_sku_data(input):
    # Ensure vector index is created
    get_neo4j_vector()
    
    if not neo4jvector or not retriever or not plot_retriever:
        return "Vector index not available. Please load data and create the vector index first."
    
    try:
        return plot_retriever.invoke({"input": input})
    except Exception as e:
        return f"Error accessing vector index: {str(e)}"
# end::get_sku_data[]
