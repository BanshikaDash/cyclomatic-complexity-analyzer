import textwrap

import networkx as nx
from matplotlib.figure import Figure

NODE_COLORS = {
    "terminal": "#bbf7d0",
    "decision": "#fde68a",
    "stmt": "#e5e7eb",
}


def _find_back_edges(graph: nx.DiGraph, root) -> set:
    """Edges that jump back to an earlier node (loops)."""
    back_edges, on_path = set(), set()
    for source, target, kind in nx.dfs_labeled_edges(graph, source=root):
        if kind == "forward":
            on_path.add(target)
        elif kind == "reverse":
            on_path.discard(target)
        elif kind == "nontree" and target in on_path:
            back_edges.add((source, target))
    return back_edges


def _layout(graph: nx.DiGraph, back_edges: set) -> dict:
    """Top-to-bottom layered layout (loops drawn as curved back edges)."""
    forward = graph.copy()
    forward.remove_edges_from(back_edges)

    layer = {}
    for node in nx.topological_sort(forward):
        parents = list(forward.predecessors(node))
        layer[node] = 1 + max(layer[p] for p in parents) if parents else 0

    exit_nodes = [n for n, d in graph.nodes(data=True) if d["label"] == "Exit"]
    if exit_nodes:
        layer[exit_nodes[0]] = max(layer.values())

    rows = {}
    for node, depth in layer.items():
        rows.setdefault(depth, []).append(node)

    x_of = {}
    for depth in sorted(rows):
        nodes = rows[depth]

        def centre(node):
            parents = [x_of[p] for p in forward.predecessors(node) if p in x_of]
            return sum(parents) / len(parents) if parents else 0

        nodes.sort(key=lambda n: (centre(n), n))
        for index, node in enumerate(nodes):
            x_of[node] = (index - (len(nodes) - 1) / 2) * 1.6 + 0.0

    return {node: (x_of[node], -layer[node]) for node in graph.nodes}


def draw_graph(graph: nx.DiGraph, title: str = "Control flow graph") -> Figure:
    back_edges = _find_back_edges(graph, root=0)
    positions = _layout(graph, back_edges)

    layers = len({y for _, y in positions.values()})
    widest = max(
        sum(1 for _, y in positions.values() if y == row)
        for row in {y for _, y in positions.values()}
    )
    figure = Figure(
        figsize=(min(max(6, 2.2 * widest + 1), 24), min(max(3.5, 0.9 * layers + 1), 60)),
        facecolor="white",
    )
    axis = figure.subplots()

    straight = [e for e in graph.edges if e not in back_edges]
    curved = [e for e in graph.edges if e in back_edges]
    edge_style = dict(
        ax=axis, node_size=1700, arrows=True, arrowstyle="-|>",
        arrowsize=11, edge_color="#555555", width=1.1,
    )
    nx.draw_networkx_edges(graph, positions, edgelist=straight, **edge_style)
    nx.draw_networkx_edges(
        graph, positions, edgelist=curved,
        connectionstyle="arc3,rad=0.45", **edge_style,
    )

    for edges, style in ((straight, "arc3"), (curved, "arc3,rad=0.45")):
        labels = {
            (u, v): graph.edges[u, v]["label"]
            for u, v in edges
            if graph.edges[u, v].get("label")
        }
        if labels:
            nx.draw_networkx_edge_labels(
                graph, positions, edge_labels=labels, ax=axis,
                font_size=7, label_pos=0.35, connectionstyle=style,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85),
            )

    joins = [n for n, d in graph.nodes(data=True) if d["kind"] == "join"]
    if joins:
        nx.draw_networkx_nodes(
            graph, positions, nodelist=joins, node_size=40,
            node_color="#888888", ax=axis,
        )

    for kind, color in NODE_COLORS.items():
        labels = {
            n: textwrap.fill(d["label"], 20, max_lines=2, placeholder="...")
            for n, d in graph.nodes(data=True)
            if d["kind"] == kind
        }
        if labels:
            nx.draw_networkx_labels(
                graph, positions, labels=labels, ax=axis, font_size=7.5,
                font_color="#111111",
                bbox=dict(boxstyle="round,pad=0.35", fc=color, ec="#555555", lw=0.8),
            )

    axis.set_title(title, fontsize=11)
    xs = [x for x, _ in positions.values()]
    ys = [y for _, y in positions.values()]
    axis.set_xlim(min(xs) - 1.2, max(xs) + 1.2)
    axis.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
    axis.axis("off")
    figure.tight_layout()
    return figure
