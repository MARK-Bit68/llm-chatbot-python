#!/usr/bin/env python3
"""
Test the improved chatbot with better SKU prioritization
"""
import os
import pytest
from langchain_neo4j import Neo4jVector
from llm import embeddings
from graph import get_graph


def test_improved_chatbot():
    """Test improved chatbot functionality"""
    if not os.getenv("NEO4J_URI") or embeddings is None:
        pytest.skip("Neo4j or embeddings not configured")

    graph = get_graph()
    if graph is None:
        pytest.skip("Neo4j not available")

    neo4jvector = Neo4jVector.from_existing_index(
        embeddings,
        graph=graph,
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

    retriever = neo4jvector.as_retriever(search_kwargs={"k": 5})

    # Test query
    query = "What is the demand plan for SKU001?"
    results = retriever.invoke(query)

    assert results is not None