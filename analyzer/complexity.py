def calculate_complexity(
    nodes: int,
    edges: int,
    components: int = 1,
) -> int:
    """McCabe's formula: M = E - N + 2P."""
    if nodes < 0 or edges < 0 or components < 0:
        raise ValueError("Nodes, edges, and components cannot be negative.")

    if nodes == 0 and edges == 0:
        return 0

    if components < 1:
        raise ValueError("A non-empty graph must have at least one component.")

    return edges - nodes + 2 * components


def calculate_from_decisions(decision_count: int) -> int:
    """Shortcut form: M = 1 + number of decision points."""
    if decision_count < 0:
        raise ValueError("Decision count cannot be negative.")

    return decision_count + 1


def risk_level(complexity: int) -> str:
    """Commonly used bands for how hard a function is to test and maintain."""
    if complexity <= 10:
        return "Low"
    if complexity <= 20:
        return "Moderate"
    if complexity <= 50:
        return "High"
    return "Very high"
