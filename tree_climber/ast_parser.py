import warnings

from pathlib import Path
import networkx as nx
from tree_sitter import Node, Tree
from tree_sitter_languages import get_parser

from tree_climber.base_parser import BaseParser
from tree_climber.base_visitor import BaseVisitor
from tree_climber.util import Counter


def assert_boolean_expression(n):
    assert (
        n.type.endswith("_statement")
        or n.type.endswith("_expression")
        or n.type in ("true", "false", "identifier", "number_literal")  # TODO: handle ERROR (most often shows up as comma_expression in for loop conditional)
    ), (n, n.type, n.text.decode())


def check_ast_error_in_children(n):
    if any(c.type == "ERROR" for c in n.children):
        raise AstErrorException(n.text.decode())


class AstErrorException(Exception):
    pass


class ASTParser(BaseVisitor, BaseParser):
    """
    AST visitor which creates a CFG.
    After traversing the AST by calling visit() on the root, self.cfg has a complete CFG.
    """

    def __init__(self, strict):
        super(ASTParser).__init__()
        self.ast = nx.DiGraph()
        self.counter = Counter()
        self.strict = strict

    @staticmethod
    def parse(data, strict=True):
        if isinstance(data, Path):
            return ASTParser.parse(data.read_text())
        elif isinstance(data, str) or isinstance(data, bytes):
            parser = get_parser("c")
            if isinstance(data, str):
                data = data.encode("utf-8")
            root_node = parser.parse(data).root_node
        elif isinstance(data, Tree):
            root_node = data.root_node
        elif isinstance(data, Node):
            root_node = data
        else:
            raise NotImplementedError(type(data))
        visitor = ASTParser(strict=strict)
        visitor.visit(root_node, parent_id=None)
        visitor.ast.graph["graph_type"] = "AST"
        return visitor.ast

    def get_type(self, n):
        return n.type

    def get_children(self, n):
        return n.children

    def visit(self, n, **kwargs):
        if self.strict:
            if n.has_error or n.is_missing:
                raise AstErrorException(n.text.decode())
        else:
            warnings.warn("encountered ERROR in AST")

        return getattr(self, f"visit_{self.get_type(n)}", self.visit_default)(n=n, **kwargs)

    def visit_children(self, n, **kwargs):
        for i, c in enumerate(n.children):
            should_continue = self.visit(c, **kwargs)
            if should_continue == False:
                break

    def visit_for_statement(self, n, **kwargs):
        children = n.children
        check_ast_error_in_children(n)
        children = [c for c in children if c.type != "comment"]
        i = 0
        while children[i].type != "(":
            i += 1
        i += 1
        if children[i].type == "declaration":
            has_init = True
            i += 1
        elif children[i].type == ";":
            has_init = False
            i += 1
        else:
            assert children[i].type.endswith("_expression") or children[i].type in ("number_literal", "identifier"), (children[i], children[i].type)
            has_init = True
            i += 1
            assert children[i].type == ";"
            i += 1
        # pointing after semicolon
        if children[i].type == ";":
            has_cond = False
        else:
            assert_boolean_expression(children[i])
            has_cond = True
            i += 1
        # pointing at semicolon
        assert children[i].type == ";", (children[i], children[i].type, children[i].text.decode())
        i += 1
        if children[i].type == ")":
            has_incr = False
        else:
            assert children[i].type.endswith("_expression") or children[i].type in ("number_literal", "identifier"), (children[i], children[i].type)
            has_incr = True
        self.visit_default(
            n, has_init=has_init, has_cond=has_cond, has_incr=has_incr, **kwargs
        )

    def visit_case_statement(self, n, **kwargs):
        children = n.children
        check_ast_error_in_children(n)
        label_end = 0
        while children[label_end].type != ":":
            label_end += 1
        label_end -= 1
        body_begin = label_end + 2
        is_default = any(c for c in n.children if c.text.decode() == "default")
        self.visit_default(n, body_begin=body_begin, is_default=is_default, **kwargs)

    def visit_default(self, n, parent_id, **kwargs):
        code = n.text.decode()
        my_id = self.counter.get_and_increment()
        if parent_id is None:
            self.ast.graph["root_node"] = my_id
        if n.is_named and n.type != "comment":

            def attr_to_label(node_type, code):
                lines = code.splitlines()
                if len(lines) > 0:
                    code = lines[0]
                    max_len = 27
                    trimmed_code = code[:max_len]
                    if len(lines) > 1 or len(code) > max_len:
                        trimmed_code += "..."
                else:
                    trimmed_code = code
                return node_type + "\n" + trimmed_code

            self.ast.add_node(
                my_id,
                n=n,
                label=attr_to_label(n.type, code),
                code=code,
                node_type=n.type,
                start=n.start_point,
                end=n.end_point,
                **kwargs
            )
            if parent_id is not None:
                self.ast.add_edge(parent_id, my_id)
            self.visit_children(n, parent_id=my_id)
