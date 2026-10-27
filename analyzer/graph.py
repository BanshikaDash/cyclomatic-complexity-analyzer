import matplotlib.pyplot as plt
import networkx as nx


def build_graph(decision_count: int) -> nx.DiGraph:
    if decision_count < 0:
        raise ValueError("Decision count cannot be negative.")

    graph = nx.DiGraph()

    graph.add_node("Entry", label="Entry")

    for index in range(1, decision_count + 1):
        graph.add_node(f"D{index}", label=f"Decision {index}")

    graph.add_node("Exit", label="Exit")

    nodes = list(graph.nodes)

    for source, target in zip(nodes, nodes[1:]):
        graph.add_edge(source, target)

    for index in range(1, decision_count + 1):
        graph.add_edge(f"D{index}", "Exit")

    return graph


def draw_graph(graph: nx.DiGraph):
    figure, axis = plt.subplots(figsize=(10, 5))

    positions = nx.spring_layout(graph, seed=42)

    nx.draw_networkx(
        graph,
        positions,
        ax=axis,
        with_labels=True,
        node_size=2200,
        font_size=9,
        arrows=True,
    )

    axis.set_title("Illustrative Control Flow Graph")
    axis.axis("off")
    figure.tight_layout()

    return figure
