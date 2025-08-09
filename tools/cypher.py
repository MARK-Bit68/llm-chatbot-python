"""Compatibility layer forwarding to the production cypher tools.

This preserves existing imports in tests and external scripts:
    from tools.cypher import cypher_qa
"""

from solutions.tools.cypher import cypher_qa, enhanced_cypher_qa  # noqa: F401

__all__ = [
    "cypher_qa",
    "enhanced_cypher_qa",
]