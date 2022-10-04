from tree_climber.dataflow.dataflow_solver import DataflowSolver
import networkx as nx


def get_definition(ast_node, ast):
    node_type = ast.nodes[ast_node]["type"]
    if node_type == "identifier":
        return ast.nodes[ast_node]["text"]
    elif node_type == "pointer_declarator":
        return get_definition(list(ast.successors(ast_node))[1], ast)
    elif node_type == "init_declarator":
        return get_definition(list(ast.successors(ast_node))[0], ast)
    elif node_type == "declaration":
        return get_definition(list(ast.successors(ast_node))[1], ast)
    elif node_type == "assignment_expression":
        return get_definition(list(ast.successors(ast_node))[0], ast)
    elif node_type == "update_expression":
        return get_definition(list(ast.successors(ast_node))[0], ast)
    elif node_type == "expression_statement":
        return get_definition(list(ast.successors(ast_node))[0], ast)
    return None


class ReachingDefinitionSolver(DataflowSolver):
    """
    reaching definition
    https://en.wikipedia.org/wiki/Reaching_definition
    """

    def __init__(self, ast, cfg, verbose=0):
        super().__init__(cfg, verbose)

        node2def = {}
        def2node = {}
        id2def = {}
        def2id = {}
        def2code = {}
        def_idx = 0
        for n in cfg.nodes():
            attr = cfg.nodes[n]
            if "ast_node" in attr:
                ast_node = attr["ast_node"]
                _id = get_definition(ast_node, ast)
                if _id is not None:
                    node2def[n] = def_idx
                    def2node[def_idx] = n

                    if _id not in id2def:
                        id2def[_id] = set()
                    id2def[_id].add(def_idx)
                    def2id[def_idx] = _id
                    def2code[def_idx] = ast.nodes[ast_node]["text"]

                    def_idx += 1
        if verbose >= 1:
            print("node2def", node2def)
            print("def2node", def2node)
            print("id2def", id2def)
            print("def2id", def2id)
            print("def2code", def2code)
        self.node2def = node2def
        self.def2node = def2node
        self.id2def = id2def
        self.def2id = def2id
        self.def2code = def2code

    def gen(self, n) -> set:
        if n in self.node2def:
            d = self.node2def[n]
            if self.verbose >= 2:
                print("gen", n, d)
            return {d}
        else:
            return set()

    def kill(self, n) -> set:
        if n in self.node2def:
            d = self.node2def[n]
            if d in self.def2id:
                i = self.def2id[d]
                if i in self.id2def:
                    if self.verbose >= 2:
                        print("kill", n, self.id2def[i])
                    return self.id2def[i]
        else:
            return set()
