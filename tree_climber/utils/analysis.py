"""
Utilities for analysis of C programs.
"""


def get_method_reference(n, typ, ast):
    """
    Return a (n, <method name>) tuple if n is a method reference, otherwise None.
    """
    if typ == "call_expression":
        return n, next(
            ast.nodes[s]["text"]
            for s in ast.successors(n)
            if ast.nodes[s]["type"] == "identifier"
        )
    elif typ == "function_declarator" and not any(
        ast.nodes[a]["type"] == "function_definition" for a in ast.predecessors(n)
    ):
        return n, next(
            ast.nodes[s]["text"]
            for s in ast.successors(n)
            if ast.nodes[s]["type"] == "identifier"
        )


def get_method_definition(n, typ, ast):
    """
    Return a (n, <method name>) tuple if n is a method definition, otherwise None.
    """
    if typ == "function_definition":
        declarator = next(
            s
            for s in ast.successors(n)
            if ast.nodes[s]["type"] == "function_declarator"
        )
        return n, next(
            ast.nodes[s]["text"]
            for s in ast.successors(declarator)
            if ast.nodes[s]["type"] == "identifier"
        )
