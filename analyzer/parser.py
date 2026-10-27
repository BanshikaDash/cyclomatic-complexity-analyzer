import re
from typing import Any


CONTROL_KEYWORDS = {
    "if", "for", "while", "switch", "catch"
}


def remove_comments_and_literals(source: str) -> str:
    pattern = re.compile(
        r'//[^\n]*'
        r'|/\*[\s\S]*?\*/'
        r'|R"([^ ()\\\t\r\n]{0,16})\([\s\S]*?\)\1"'
        r'|"(?:\\.|[^"\\])*"'
        r"|'(?:\\.|[^'\\])*'",
        re.MULTILINE,
    )

    def replace(match: re.Match) -> str:
        return re.sub(r'[^\n]', ' ', match.group(0))

    return pattern.sub(replace, source)


def find_functions(source: str) -> list[dict[str, Any]]:
    clean_source = remove_comments_and_literals(source)

    function_pattern = re.compile(
        r'(?P<signature>'
        r'(?:[A-Za-z_]\w*(?:\s*<[^;{}]*>)?[\s*&:<>]*\s+)+'
        r'[A-Za-z_]\w*\s*'
        r'\([^;{}]*\)\s*'
        r'(?:const\s*)?(?:noexcept\s*)?'
        r'(?:->\s*[\w:<>*&\s]+)?'
        r')\{',
        re.MULTILINE,
    )

    functions = []

    for match in function_pattern.finditer(clean_source):
        brace_start = match.end() - 1
        depth = 0
        brace_end = None

        for index in range(brace_start, len(clean_source)):
            if clean_source[index] == '{':
                depth += 1
            elif clean_source[index] == '}':
                depth -= 1

                if depth == 0:
                    brace_end = index
                    break

        if brace_end is None:
            continue

        signature = match.group("signature").strip()
        name_match = re.search(r'([A-Za-z_]\w*)\s*\([^()]*\)\s*(?:const\b)?', signature)

        if not name_match:
            continue

        name = name_match.group(1)

        if name in CONTROL_KEYWORDS or name in {"switch", "catch"}:
            continue

        body = clean_source[brace_start + 1:brace_end]

        functions.append({
            "name": name,
            "signature": signature,
            "start_line": clean_source.count("\n", 0, match.start()) + 1,
            "end_line": clean_source.count("\n", 0, brace_end) + 1,
            "body": body,
        })

    return functions


def analyze_source(source: str) -> dict[str, Any]:
    clean_source = remove_comments_and_literals(source)
    functions = find_functions(source)

    decisions = []

    for keyword in ("if", "for", "while", "case", "catch"):
        for match in re.finditer(r'\b' + keyword + r'\b', clean_source):
            decisions.append({
                "type": keyword,
                "line": clean_source.count("\n", 0, match.start()) + 1,
            })

    logical_operators = []

    for match in re.finditer(r'&&|\|\|', clean_source):
        logical_operators.append({
            "operator": match.group(0),
            "line": clean_source.count("\n", 0, match.start()) + 1,
        })

    return {
        "functions": functions,
        "decisions": decisions,
        "logical_operators": logical_operators,
        "function_count": len(functions),
        "decision_count": len(decisions),
        "logical_operator_count": len(logical_operators),
    }
