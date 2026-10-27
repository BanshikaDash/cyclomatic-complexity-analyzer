from analyzer.parser import analyze_source, remove_comments_and_literals


def test_comments_are_removed():
    source = """
    int main() {
        // if (fake_condition) {}
        /* while (fake_condition) {} */
        return 0;
    }
    """
    cleaned = remove_comments_and_literals(source)
    assert "fake_condition" not in cleaned


def test_string_literals_are_removed():
    source = 'int main() { const char* s = "if (x)"; return 0; }'
    cleaned = remove_comments_and_literals(source)
    assert "if (x)" not in cleaned


def test_detects_decisions():
    source = """
    int main() {
        if (x > 0) {
            return 1;
        }
        return 0;
    }
    """
    result = analyze_source(source)
    assert result["decision_count"] == 1


def test_detects_logical_operators():
    source = """
    int main() {
        if (x > 0 && y > 0 || z > 0) {
            return 1;
        }
        return 0;
    }
    """
    result = analyze_source(source)
    assert result["logical_operator_count"] == 2


def test_detects_function():
    source = """
    int calculate(int value) {
        if (value > 10) {
            return 1;
        }
        return 0;
    }
    """
    result = analyze_source(source)
    names = [function["name"] for function in result["functions"]]
    assert "calculate" in names


def test_empty_source():
    result = analyze_source("")
    assert result["function_count"] == 0
    assert result["decision_count"] == 0
    assert result["logical_operator_count"] == 0
