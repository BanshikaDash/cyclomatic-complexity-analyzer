import pytest

from analyzer.complexity import calculate_complexity, calculate_from_decisions
from analyzer.parser import analyze_source


def score(source: str) -> int:
    functions = analyze_source(source)["functions"]
    assert len(functions) == 1
    return functions[0]["complexity"]


@pytest.mark.parametrize(
    "body, expected",
    [
        ("return 1;", 1),
        ("if (a) return 1; return 0;", 2),
        ("if (a) return 1; else if (b) return 2; else return 3;", 3),
        ("if (a && b) return 1; return 0;", 3),
        ("if (a || b || c) return 1; return 0;", 4),
        ("if (!(a && b)) return 1; return 0;", 3),
        ("return a ? 1 : 0;", 2),
        ("return a && b;", 2),
        ("for (int i = 0; i < n; i++) { s += i; } return s;", 2),
        ("for (;;) { if (a) return 1; }", 3),
        ("for (auto x : v) { s += x; } return s;", 2),
        ("while (a) { a--; } return a;", 2),
        ("do { a--; } while (a > 0); return a;", 2),
        ("while (a) { if (b) continue; if (c) break; a--; } return a;", 4),
        ("switch (a) { case 1: break; case 2: break; default: break; } return 0;", 3),
        ("switch (a) { case 1: case 2: f(); break; } return 0;", 3),
        ("try { f(); } catch (int e) { } catch (...) { } return 0;", 3),
        ("return 1; if (a) return 2;", 1),  # unreachable code is ignored
        ("if (a) {} return 0;", 2),  # empty branch still counts
    ],
)
def test_function_complexity(body, expected):
    assert score("int f(int a, int b, int c, int n, int s, std::vector<int> v) {" + body + "}") == expected


def test_comments_and_strings_are_ignored():
    source = '''
    int f(int a) {
        // if (x) while (y) && ||
        /* for (;;) */
        const char* s = "if (a) && || while";
        return a;
    }'''
    assert score(source) == 1


def test_each_function_is_scored_separately():
    source = """
    int a(int x) { if (x) return 1; return 0; }
    int b(int x) { if (x) return 1; if (!x) return 2; return 0; }
    int c() { return 1; }
    """
    result = analyze_source(source)
    assert [f["name"] for f in result["functions"]] == ["a", "b", "c"]
    assert [f["complexity"] for f in result["functions"]] == [2, 3, 1]
    assert result["max_complexity"] == 3


def test_methods_templates_and_constructors_are_found():
    source = """
    class Box {
    public:
        Box(int v) : value(v) { if (v < 0) value = 0; }
        int get() const { return value; }
        Box() = default;
    private:
        int value;
    };
    namespace n { template <typename T> T id(T v) { return v; } }
    int Box::other() { return 1; }
    """
    names = [f["name"] for f in analyze_source(source)["functions"]]
    assert names == ["Box", "get", "id", "Box::other"]


def test_lambda_is_not_counted_in_enclosing_function():
    source = "int f() { auto g = [](int x) { if (x) return 1; return 0; }; return g(1); }"
    assert score(source) == 1


def test_graph_matches_decision_count():
    source = """
    int f(int a, int b) {
        for (int i = 0; i < a; i++) { if (i && b) continue; }
        switch (b) { case 1: return a > 1 ? 1 : 2; default: break; }
        try { g(); } catch (...) { }
        return 0;
    }"""
    function = analyze_source(source)["functions"][0]
    assert function["complexity"] == 1 + len(function["decisions"])


def test_syntax_errors_are_reported():
    assert analyze_source("int f( { if }")["has_syntax_errors"] is True
    assert analyze_source("int f() { return 1; }")["has_syntax_errors"] is False


def test_no_functions():
    assert analyze_source("int x = 3;")["function_count"] == 0


def test_formula_helpers():
    assert calculate_complexity(nodes=6, edges=7) == 3
    assert calculate_complexity(0, 0) == 0
    assert calculate_from_decisions(4) == 5
    with pytest.raises(ValueError):
        calculate_complexity(-1, 0)
    with pytest.raises(ValueError):
        calculate_from_decisions(-1)
