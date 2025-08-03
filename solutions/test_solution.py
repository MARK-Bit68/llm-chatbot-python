import pytest
import streamlit as st
from llm import llm, embeddings
from graph import graph

def test_vector_tool():
    """Test the vector search tool"""
    from tools.vector import get_sku_data
    assert get_sku_data("Aliens land on earth") is not None

def test_cypher_tool():
    """Test the cypher query tool"""
    from tools.cypher import cypher_qa
    assert cypher_qa("What is the category of SKU001?") is not None

def test_vector_index():
    """Test that the vector index exists"""
    try:
        from langchain_neo4j import Neo4jVector
        neo4jvector = Neo4jVector.from_existing_index(
            embeddings,
            graph=graph,
            index_name="skuPlots",
            node_label="SKU",
            text_node_property="plot",
            embedding_node_property="plotEmbedding"
        )
        assert neo4jvector is not None
    except Exception as e:
        assert False, "The skuPlots index does not exist. Run the Cypher script to create it."

def test_agent():
    """Test the agent with a simple question"""
    from solutions.agent import generate_response
    question = "What is the category of SKU001?"
    response = generate_response(question)
    assert response is not None
    assert len(response) > 0