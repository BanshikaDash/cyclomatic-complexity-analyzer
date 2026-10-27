"""Build a control flow graph (CFG) for one C++ function.

The graph is built from a tree-sitter syntax tree, so it follows the real
structure of the code: if/else, loops, switch, try/catch, return, break and
continue. Short-circuit operators (&&, ||) and the ?: operator each add their
own branch, so the usual formula  edges - nodes + 2  matches the standard
"1 + number of decisions" count.
"""

import re

import networkx as nx

LABEL_WIDTH = 34

# Operators that branch because the right side may be skipped.
SHORT_CIRCUIT = {"&&": "&&", "and": "&&", "||": "||", "or": "||"}


def _text(node) -> str:
    return re.sub(r"\s+", " ", node.text.decode("utf-8", errors="replace")).strip()


def _short(text: str, width: int = LABEL_WIDTH) -> str:
    return text if len(text) <= width else text[: width - 3] + "..."


def _header(node, body) -> str:
    """Text of a statement up to (not including) its body, e.g. 'catch (int e)'."""
    if body is None:
        return _text(node)
    size = body.start_byte - node.start_byte
    raw = node.text[:size].decode("utf-8", errors="replace")
    return re.sub(r"\s+", " ", raw).strip()


class CFGBuilder:
    """Walks the statements of one function and records nodes and edges.

    Most methods take `preds` (a list of (node, edge_label) pairs that should
    flow into the next node) and return the list of pairs that flow out.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.decisions = []
        self._returns = []
        self._targets = []
        self._next_id = 0
        self._handlers = {
            "compound_statement": self._compound,
            "if_statement": self._if,
            "while_statement": self._while,
            "for_statement": self._for,
            "for_range_loop": self._for_range,
            "do_statement": self._do,
            "switch_statement": self._switch,
            "try_statement": self._try,
            "return_statement": self._return,
            "co_return_statement": self._return,
            "throw_statement": self._return,
            "break_statement": self._break,
            "continue_statement": self._continue,
            "labeled_statement": self._labeled,
        }

    # ------------------------------------------------------------------
    # Building blocks
    # ------------------------------------------------------------------

    def build(self, body):
        entry = self._add("Entry", "terminal", None, [])
        exits = self.statement(body, [(entry, None)])
        pending = exits + self._returns
        if pending:
            self._add("Exit", "terminal", None, pending)
        decisions = sorted(self.decisions, key=lambda item: item["line"])
        return self.graph, decisions

    def _add(self, label, kind, node, preds):
        node_id = self._next_id
        self._next_id += 1
        line = node.start_point[0] + 1 if node is not None else None
        self.graph.add_node(node_id, label=label, kind=kind, line=line)
        for source, edge_label in preds:
            self._connect(source, node_id, edge_label)
        return node_id

    def _connect(self, source, target, label=None):
        if self.graph.has_edge(source, target):
            # A DiGraph holds one edge per pair, so route the second edge
            # through a pass-through node. This keeps the complexity correct.
            middle = self._add("", "join", None, [])
            self.graph.add_edge(source, middle, label=label)
            self.graph.add_edge(middle, target, label=None)
        else:
            self.graph.add_edge(source, target, label=label)

    def _record(self, kind, node):
        self.decisions.append({"type": kind, "line": node.start_point[0] + 1})

    def _push_target(self, allow_continue=True):
        target = {"break": [], "continue": [] if allow_continue else None}
        self._targets.append(target)
        return target

    # ------------------------------------------------------------------
    # Inline decisions: &&, || and ?: inside an ordinary expression
    # ------------------------------------------------------------------

    @staticmethod
    def _inline_decisions(expr):
        found = []
        stack = [expr]
        while stack:
            node = stack.pop()
            if node.type == "lambda_expression":
                continue
            if node.type == "conditional_expression":
                found.append(("?:", node))
            elif node.type == "binary_expression":
                operator = node.child_by_field_name("operator")
                if operator is not None:
                    symbol = SHORT_CIRCUIT.get(operator.text.decode())
                    if symbol:
                        found.append((symbol, node))
            stack.extend(node.children)
        found.sort(key=lambda item: item[1].start_byte)
        return found

    def _expand(self, items, preds):
        """Add a small diamond (decision, branch, join) for each inline decision."""
        for symbol, node in items:
            self._record(symbol, node)
            decision = self._add(symbol, "decision", node, preds)
            branch = self._add("", "join", node, [(decision, "T")])
            join = self._add("", "join", node, [(branch, None), (decision, "F")])
            preds = [(join, None)]
        return preds

    # ------------------------------------------------------------------
    # Conditions (if / while / for / do): && and || become separate nodes
    # ------------------------------------------------------------------

    @staticmethod
    def _unwrap(expr):
        while expr is not None and expr.type in (
            "parenthesized_expression",
            "condition_clause",
        ):
            if expr.type == "condition_clause":
                inner = expr.child_by_field_name("value")
            else:
                inner = expr.named_children[0] if expr.named_children else None
            if inner is None:
                break
            expr = inner
        return expr

    def condition(self, expr, preds):
        """Return (true_edges, false_edges) leaving the condition."""
        expr = self._unwrap(expr)

        if expr.type == "binary_expression":
            operator = expr.child_by_field_name("operator")
            symbol = SHORT_CIRCUIT.get(operator.text.decode()) if operator else None
            if symbol:
                self._record(symbol, expr)
                left_true, left_false = self.condition(
                    expr.child_by_field_name("left"), preds
                )
                if symbol == "&&":
                    right_true, right_false = self.condition(
                        expr.child_by_field_name("right"), left_true
                    )
                    return right_true, left_false + right_false
                right_true, right_false = self.condition(
                    expr.child_by_field_name("right"), left_false
                )
                return left_true + right_true, right_false

        if expr.type == "unary_expression":
            operator = expr.child_by_field_name("operator")
            if operator is not None and operator.text.decode() in ("!", "not"):
                true_edges, false_edges = self.condition(
                    expr.child_by_field_name("argument"), preds
                )
                return false_edges, true_edges

        preds = self._expand(self._inline_decisions(expr), preds)
        leaf = self._add(_short(_text(expr)), "decision", expr, preds)
        return [(leaf, "T")], [(leaf, "F")]

    # ------------------------------------------------------------------
    # Statements
    # ------------------------------------------------------------------

    def statement(self, node, preds):
        kind = node.type
        if kind in ("comment", "empty_statement"):
            return preds
        if kind.startswith("preproc_"):
            return self._preproc(node, preds)
        if not preds:
            return []  # unreachable code (after return, break, ...)
        if kind == "expression_statement" and self._is_throw(node):
            return self._return(node, preds)
        return self._handlers.get(kind, self._simple)(node, preds)

    def _sequence(self, nodes, preds):
        for child in nodes:
            preds = self.statement(child, preds)
        return preds

    def _compound(self, node, preds):
        return self._sequence(node.named_children, preds)

    def _preproc(self, node, preds):
        if node.type not in (
            "preproc_if",
            "preproc_ifdef",
            "preproc_elif",
            "preproc_elifdef",
            "preproc_else",
        ):
            return preds
        skip = {
            child.id
            for child in (
                node.child_by_field_name("condition"),
                node.child_by_field_name("name"),
            )
            if child is not None
        }
        children = [child for child in node.named_children if child.id not in skip]
        return self._sequence(children, preds)

    @staticmethod
    def _is_throw(node):
        children = node.named_children
        return bool(children) and children[0].type == "throw_expression"

    def _simple(self, node, preds):
        statement = self._add(_short(_text(node)), "stmt", node, preds)
        return self._expand(self._inline_decisions(node), [(statement, None)])

    def _labeled(self, node, preds):
        return self._sequence(node.named_children[1:], preds)

    def _if(self, node, preds):
        self._record("if", node)
        true_edges, false_edges = self.condition(
            node.child_by_field_name("condition"), preds
        )
        exits = self.statement(node.child_by_field_name("consequence"), true_edges)

        alternative = node.child_by_field_name("alternative")
        inner = (
            [child for child in alternative.named_children if child.type != "comment"]
            if alternative is not None
            else []
        )
        if inner:
            return exits + self.statement(inner[-1], false_edges)
        return exits + false_edges

    def _while(self, node, preds):
        self._record("while", node)
        entry = self._next_id
        true_edges, false_edges = self.condition(
            node.child_by_field_name("condition"), preds
        )
        target = self._push_target()
        body_exits = self.statement(node.child_by_field_name("body"), true_edges)
        self._targets.pop()
        for source, label in body_exits + target["continue"]:
            self._connect(source, entry, label)
        return false_edges + target["break"]

    def _for(self, node, preds):
        self._record("for", node)
        init = node.child_by_field_name("initializer")
        if init is not None and init.type != ";":
            start = self._add(_short(_text(init)), "stmt", init, preds)
            preds = [(start, None)]

        entry = self._next_id
        condition = node.child_by_field_name("condition")
        if condition is not None:
            true_edges, false_edges = self.condition(condition, preds)
        else:
            # No condition: treat it like "while (true)" so both count the same.
            head = self._add("for (;;)", "decision", node, preds)
            true_edges, false_edges = [(head, "T")], [(head, "F")]

        target = self._push_target()
        body_exits = self.statement(node.child_by_field_name("body"), true_edges)
        self._targets.pop()

        back_edges = body_exits + target["continue"]
        update = node.child_by_field_name("update")
        if update is not None and back_edges:
            step = self._add(_short(_text(update)), "stmt", update, back_edges)
            back_edges = [(step, None)]
        for source, label in back_edges:
            self._connect(source, entry, label)
        return false_edges + target["break"]

    def _for_range(self, node, preds):
        self._record("for", node)
        body = node.child_by_field_name("body")
        head = self._add(_short(_header(node, body)), "decision", node, preds)
        target = self._push_target()
        body_exits = self.statement(body, [(head, "T")])
        self._targets.pop()
        for source, label in body_exits + target["continue"]:
            self._connect(source, head, label)
        return [(head, "F")] + target["break"]

    def _do(self, node, preds):
        head = self._add("do", "stmt", node, preds)
        target = self._push_target()
        body_exits = self.statement(
            node.child_by_field_name("body"), [(head, None)]
        )
        self._targets.pop()

        check_edges = body_exits + target["continue"]
        if not check_edges:
            return target["break"]

        self._record("while", node)
        true_edges, false_edges = self.condition(
            node.child_by_field_name("condition"), check_edges
        )
        for source, label in true_edges:
            self._connect(source, head, label)
        return false_edges + target["break"]

    def _switch(self, node, preds):
        condition = node.child_by_field_name("condition")
        entry = self._add(
            _short("switch " + _text(condition)), "decision", node, preds
        )
        body = node.child_by_field_name("body")
        cases = (
            [child for child in body.named_children if child.type == "case_statement"]
            if body is not None
            else []
        )

        target = self._push_target(allow_continue=False)
        fallthrough = []
        has_default = False
        for case in cases:
            value = case.child_by_field_name("value")
            if value is None:
                has_default = True
                label = "default"
            else:
                self._record("case", case)
                label = _short("case " + _text(value))

            case_id = self._add(label, "stmt", case, [(entry, None)] + fallthrough)
            statements = [
                child
                for child in case.named_children
                if value is None or child.id != value.id
            ]
            fallthrough = self._sequence(statements, [(case_id, None)])
        self._targets.pop()

        exits = fallthrough + target["break"]
        if not has_default:
            exits.append((entry, "no match"))
        return exits

    def _try(self, node, preds):
        head = self._add("try", "stmt", node, preds)
        exits = self.statement(node.child_by_field_name("body"), [(head, None)])
        for clause in node.named_children:
            if clause.type != "catch_clause":
                continue
            self._record("catch", clause)
            body = clause.child_by_field_name("body")
            catch = self._add(
                _short(_header(clause, body)),
                "decision",
                clause,
                [(head, "exception")],
            )
            exits = exits + self.statement(body, [(catch, None)])
        return exits

    def _return(self, node, preds):
        statement = self._add(_short(_text(node)), "stmt", node, preds)
        self._returns.extend(
            self._expand(self._inline_decisions(node), [(statement, None)])
        )
        return []

    def _break(self, node, preds):
        if not self._targets:
            return self._simple(node, preds)
        statement = self._add("break", "stmt", node, preds)
        self._targets[-1]["break"].append((statement, None))
        return []

    def _continue(self, node, preds):
        for target in reversed(self._targets):
            if target["continue"] is not None:
                statement = self._add("continue", "stmt", node, preds)
                target["continue"].append((statement, None))
                return []
        return self._simple(node, preds)


def build_function_graph(body):
    """Return (graph, decisions) for a function body syntax node."""
    return CFGBuilder().build(body)
