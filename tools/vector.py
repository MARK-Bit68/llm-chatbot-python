"""Compatibility layer forwarding to the production vector tools.

This preserves existing imports in tests and external scripts:
    from tools.vector import get_sku_data
"""

from solutions.tools.vector import get_sku_data, get_neo4j_vector  # noqa: F401

__all__ = [
    "get_sku_data",
    "get_neo4j_vector",
]