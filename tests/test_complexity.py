import pytest

from analyzer.complexity import (
    calculate_complexity,
    calculate_from_decisions,
)


def test_linear_graph_complexity():
    assert calculate_complexity(nodes=2, edges=1, components=1) == 1


def test_decision_graph_complexity():
    assert calculate_complexity(nodes=4, edges=5, components=1) == 3


def test_multiple_components():
    assert calculate_complexity(nodes=4, edges=2, components=2) == 2


def test_empty_graph():
    assert calculate_complexity(nodes=0, edges=0, components=1) == 0


def test_decision_count_estimate():
    assert calculate_from_decisions(0) == 1
    assert calculate_from_decisions(3) == 4


def test_negative_decision_count():
    with pytest.raises(ValueError):
        calculate_from_decisions(-1)


def test_negative_nodes():
    with pytest.raises(ValueError):
        calculate_complexity(nodes=-1, edges=0)


def test_invalid_components():
    with pytest.raises(ValueError):
        calculate_complexity(nodes=2, edges=1, components=0)
