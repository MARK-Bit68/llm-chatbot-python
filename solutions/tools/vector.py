import streamlit as st
from llm import get_llm, get_embeddings
from solutions.graph import get_graph

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

print("🔍 DEBUG: solutions/tools/vector.py imported successfully")

# Initialize as None - will be created when needed
neo4jvector = None
retriever = None
plot_retriever = None

# tag::vector[]
def get_neo4j_vector():
    """Get Neo4j vector index, creating it if it doesn't exist"""
    global neo4jvector, retriever, plot_retriever
    print("🔍 DEBUG: get_neo4j_vector() called")
    
    if neo4jvector is None:
        print("🔍 DEBUG: Creating new vector index...")
        try:
            print("🔍 DEBUG: Getting embeddings...")
            embeddings_instance = get_embeddings()
            print(f"🔍 DEBUG: Embeddings created: {embeddings_instance is not None}")
            
            if not embeddings_instance:
                print("⚠️ DEBUG: Embeddings not available")
                return None
                
            print("🔍 DEBUG: Getting graph instance...")
            graph_instance = get_graph()
            print(f"🔍 DEBUG: Graph instance created: {graph_instance is not None}")
            
            print("🔍 DEBUG: Creating Neo4jVector...")
            # Try to get existing index, create if it doesn't exist
            try:
                neo4jvector = Neo4jVector.from_existing_index(
                    embeddings_instance,                      # <1>
                    graph=graph_instance,                             # <2>
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
                print("🔍 DEBUG: Using existing vector index")
            except ValueError as e:
                if "does not exist" in str(e):
                    print("⚠️ DEBUG: Vector index does not exist, creating new one...")
                    # Create new index
                    neo4jvector = Neo4jVector.from_texts(
                        texts=["placeholder"],  # Will be replaced by actual data
                        embedding=embeddings_instance,
                        graph=graph_instance,
                        index_name="skuPlots",
                        node_label="SKU",
                        text_node_property="plot",
                        embedding_node_property="plotEmbedding",
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
                    print("🔍 DEBUG: Created new vector index")
                else:
                    raise e
            print("🔍 DEBUG: Neo4jVector created successfully")
            
            # Create retriever and chain
            print("🔍 DEBUG: Creating retriever...")
            retriever = neo4jvector.as_retriever() if neo4jvector else None
            print(f"🔍 DEBUG: Retriever created: {retriever is not None}")
            
            # tag::prompt[]
            print("🔍 DEBUG: Creating prompt...")
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
            print("🔍 DEBUG: Prompt created successfully")
            # end::prompt[]

            # tag::chain[]
            print("🔍 DEBUG: Creating question_answer_chain...")
            question_answer_chain = create_stuff_documents_chain(get_llm(), prompt)
            print("🔍 DEBUG: question_answer_chain created successfully")
            
            print("🔍 DEBUG: Creating plot_retriever...")
            plot_retriever = create_retrieval_chain(
                retriever, 
                question_answer_chain
            ) if retriever else None
            print(f"🔍 DEBUG: plot_retriever created: {plot_retriever is not None}")
            # end::chain[]
            
        except ValueError as e:
            if "does not exist" in str(e):
                print("⚠️ DEBUG: Vector index does not exist")
                return None
            else:
                print(f"❌ DEBUG: ValueError in vector creation: {e}")
                raise e
        except Exception as e:
            print(f"❌ DEBUG: Error creating vector index: {e}")
            raise e
    else:
        print("🔍 DEBUG: Using existing vector index")
    
    return neo4jvector

# tag::get_sku_data[]
def get_sku_data(input):
    print(f"🔍 DEBUG: get_sku_data() called with input: {input[:50]}...")
    
    # Ensure vector index is created
    print("🔍 DEBUG: Ensuring vector index is created...")
    get_neo4j_vector()
    
    print(f"🔍 DEBUG: neo4jvector: {neo4jvector is not None}")
    print(f"🔍 DEBUG: retriever: {retriever is not None}")
    print(f"🔍 DEBUG: plot_retriever: {plot_retriever is not None}")
    
    if not neo4jvector or not retriever or not plot_retriever:
        print("⚠️ DEBUG: Vector index not available")
        return "Vector index not available. Please load data and create the vector index first."
    
    try:
        print("🔍 DEBUG: Invoking plot_retriever...")
        result = plot_retriever.invoke({"input": input})
        print("🔍 DEBUG: plot_retriever invoked successfully")
        return result
    except Exception as e:
        print(f"❌ DEBUG: Error accessing vector index: {e}")
        return f"Error accessing vector index: {str(e)}"
# end::get_sku_data[]
