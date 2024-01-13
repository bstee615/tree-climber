from tree_climber.dataflow.dataflow_solver import DataflowSolver
from tree_sitter import Node
from collections import defaultdict


def named_children(node):
    return [child for child in node.children if child.is_named and child.type != "comment"]


def get_definition(ast_node):
    if ast_node.type == "identifier":
        yield ast_node.text.decode()
    elif ast_node.type == "binary_expression":
        yield from get_definition(ast_node.child_by_field_name("left"))
        yield from get_definition(ast_node.child_by_field_name("right"))
    elif ast_node.type == "parenthesized_expression":
        yield from get_definition(named_children(ast_node)[0])
    elif ast_node.type == "pointer_declarator":
        yield from get_definition(named_children(ast_node)[1])
    elif ast_node.type == "init_declarator":
        yield from get_definition(named_children(ast_node)[0])
    elif ast_node.type == "declaration":
        yield from get_definition(named_children(ast_node)[1])
    elif ast_node.type == "assignment_expression":
        yield from get_definition(named_children(ast_node)[0])
    elif ast_node.type == "update_expression":
        yield from get_definition(named_children(ast_node)[0])
    elif ast_node.type == "expression_statement":
        yield from get_definition(named_children(ast_node)[0])
    return None


class ReachingDefinitionSolver(DataflowSolver):
    """
    reaching definition
    https://en.wikipedia.org/wiki/Reaching_definition
    """

    def __init__(self, cfg, verbose=0):
        super().__init__(cfg, verbose)

        node2defs = defaultdict(list)
        def2node = {}
        id2def = {}
        def2id = {}
        def2code = {}
        def_idx = 0
        for n in cfg.nodes():
            ast_node = n.ast_node
            if isinstance(ast_node, Node):
                _ids = get_definition(ast_node)
                for _id in _ids:
                    node2defs[n].append(def_idx)
                    def2node[def_idx] = n

                    if _id not in id2def:
                        id2def[_id] = set()
                    id2def[_id].add(def_idx)
                    def2id[def_idx] = _id
                    def2code[def_idx] = ast_node.text.decode()

                    def_idx += 1
        if verbose >= 1:
            print("node2defs", node2defs)
            print("def2node", def2node)
            print("id2def", id2def)
            print("def2id", def2id)
            print("def2code", def2code)
        self.node2defs = node2defs
        self.def2node = def2node
        self.id2def = id2def
        self.def2id = def2id
        self.def2code = def2code

    def gen(self, n) -> set:
        if n in self.node2defs:
            defs = self.node2defs[n]
            if self.verbose >= 2:
                print("gen", n, defs)
            return set(defs)
        else:
            return set()

    def kill(self, n) -> set:
        if n in self.node2defs:
            defs = self.node2defs[n]
            for d in defs:
                if d in self.def2id:
                    i = self.def2id[d]
                    if i in self.id2def:
                        if self.verbose >= 2:
                            print("kill", n, self.id2def[i])
                        return self.id2def[i]
        else:
            return set()
