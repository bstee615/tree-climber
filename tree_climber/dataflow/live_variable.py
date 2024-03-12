from tree_climber.dataflow.dataflow_solver import DataflowSolver


def get_definition(ast_node):
    # TODO: Refactor to common library of robust utilities for getting defs/uses
    if ast_node.type == "identifier":
        return ast_node.text.decode()
    elif ast_node.type == "pointer_declarator":
        return get_definition(ast_node.children[1])
    elif ast_node.type == "init_declarator":
        return get_definition(ast_node.children[0])
    elif ast_node.type == "declaration":
        return get_definition(ast_node.children[1])
    elif ast_node.type == "assignment_expression":
        return get_definition(ast_node.children[0])
    elif ast_node.type == "update_expression":
        return get_definition(ast_node.children[0])
    elif ast_node.type == "expression_statement":
        return get_definition(ast_node.children[0])
    return None

def get_uses(cfg, n):
    """return the set of variables used in n"""
    # TODO: Exclude functions that are called
    used_ids = set()
    attr = cfg.nodes[n]
    if "n" in attr:
        q = [attr["n"]]
        while q:
            n = q.pop(0)
            if n.type == "identifier":
                _id = n.text.decode()
                used_ids.add(_id)
            children = n.children
            if n.type == "declaration":
                init = n.child_by_field_name("init_declarator")
                if init is not None:
                    children = [init.child_by_field_name("value")]
                else:
                    children = []
                # print(init, children)
            if n.type == "assignment_expression":
                children = [n.child_by_field_name("right")]
            q.extend(children)
    return used_ids

class LiveVariableSolver(DataflowSolver):
    """
    live variables
    https://en.wikipedia.org/wiki/Live-variable_analysis
    """

    def __init__(self, cfg, verbose=0):
        super().__init__(cfg, verbose, "backward")

    def gen(self, n) -> set:
        uses = get_uses(self.cfg, n)
        if self.verbose >= 2: print("Gen", n, uses)
        return uses

    def kill(self, n) -> set:
        cfg_node = self.cfg.nodes[n]
        if "n" in cfg_node:
            ast_node = cfg_node["n"]
            defs = get_definition(ast_node)
            if defs is None:
                defs = set()
        else:
            defs = set()

        if self.verbose >= 2: print("Kill", n, defs)
        return defs

if __name__ == "__main__":
    from tree_climber.cfg_parser import CFGParser
    data = """int main()
{
    int x;
    int y;
    
    y = 10;
    
    x = 10;
    printf("%d\\n", x); // used once
    printf("===");      // still live since it will be used
    a = 20;             // even though another variable is used
    printf("%d\\n", x); // used again

    x = 0;              // overwritten - dead
    x = 5;              // last write - live now
    printf("%d\\n", x);
    printf("===");      // x is dead now -- no more uses of it
}
"""
    cfg = CFGParser.parse(data)
    solver = LiveVariableSolver(cfg, verbose=True)
    solution, sol_out = solver.solve()
    print("OUT:")
    for k, v in sorted(sol_out.items(), key=lambda p: p[0]):
        print(k, v)
