import re
from collections import Counter
from typing import Any

import networkx as nx
import tree_sitter_cpp
from tree_sitter import Language, Parser

from analyzer.cfg import build_function_graph
from analyzer.complexity import calculate_complexity, risk_level

_PARSER = Parser(Language(tree_sitter_cpp.language()))


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_function_declarator(declarator):
    """Walk through pointer / reference / parenthesized wrappers."""
    while declarator is not None:
        if declarator.type == "function_declarator":
            inner = declarator.child_by_field_name("declarator")
            if inner is not None and inner.type in (
                "parenthesized_declarator",
                "pointer_declarator",
                "reference_declarator",
            ):
                declarator = inner
                continue
            return declarator
        inner = declarator.child_by_field_name("declarator")
        if inner is None and declarator.named_children:
            inner = declarator.named_children[0]
        declarator = inner
    return None


def _function_name(node) -> str:
    declarator = _find_function_declarator(node.child_by_field_name("declarator"))
    if declarator is None:
        return "(unknown)"
    name = declarator.child_by_field_name("declarator")
    return _collapse(name.text.decode("utf-8", errors="replace")) if name else "(unknown)"


def _signature(node, body) -> str:
    end = body.start_byte
    for child in node.children:
        if child.type == "field_initializer_list":
            end = child.start_byte
    raw = node.text[: end - node.start_byte].decode("utf-8", errors="replace")
    return _collapse(raw)


def _function_nodes(root):
    """All function definitions, in source order (methods, templates, namespaces)."""
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type == "function_definition":
            yield node
        stack.extend(reversed(node.children))


def analyze_source(source: str) -> dict[str, Any]:
    """Parse C++ source and return complexity and a control flow graph per function."""
    tree = _PARSER.parse(source.encode("utf-8"))

    functions = []
    for node in _function_nodes(tree.root_node):
        body = node.child_by_field_name("body")
        if body is None or body.type not in ("compound_statement", "try_statement"):
            continue  # "= default", "= delete" and similar have no body

        graph, decisions = build_function_graph(body)
        complexity = calculate_complexity(
            graph.number_of_nodes(),
            graph.number_of_edges(),
            nx.number_weakly_connected_components(graph),
        )

        functions.append(
            {
                "name": _function_name(node),
                "signature": _signature(node, body),
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "complexity": complexity,
                "risk": risk_level(complexity),
                "decisions": decisions,
                "decision_counts": dict(Counter(d["type"] for d in decisions)),
                "graph": graph,
            }
        )

    scores = [function["complexity"] for function in functions]
    return {
        "functions": functions,
        "function_count": len(functions),
        "max_complexity": max(scores) if scores else 0,
        "average_complexity": round(sum(scores) / len(scores), 1) if scores else 0,
        "has_syntax_errors": tree.root_node.has_error,
    }
