"""
An instance of a dataflow problem includes:
- a CFG,
- a domain D of "dataflow facts",
- a dataflow fact "init" (the information true at the start of the program for forward problems, or at the end of the program for backward problems),
- an operator ⌈⌉ (used to combine incoming information from multiple predecessors),
- for each CFG node n, a dataflow function fn : D → D (that defines the effect of executing n). 
"""

from tests.utils import *
from tree_sitter_cfg.base_visitor import BaseVisitor

def get_definition(ast_node):
    identifier = None
    if ast_node.type == "init_declarator":
        identifier = ast_node.children[0].text.decode()
        # rhs = ast_node.children[2].text
    elif ast_node.type == "expression_statement":
        assignment = ast_node.children[0]
        if assignment.type == "assignment_expression":
            identifier = assignment.children[0].text.decode()
            # rhs = assignment.children[2].text
    return identifier

def solve(cfg, verbose=0):
    """
    worklist algorithm
    https://en.wikipedia.org/wiki/Reaching_definition
    """

    def gen(n, node2def) -> set:
        if n in node2def:
            if verbose >= 2:
                print("gen", n, node2def[n])
            return set([node2def[n]])
        else:
            return set()

    def kill(n, node2def, id2def, def2id) -> set:
        if n in node2def:
            d = node2def[n]
            if d in def2id:
                i = def2id[d]
                if i in id2def:
                    if verbose >= 2:
                        print("kill", n, id2def[i])
                    return id2def[i]
        else:
            return set()

    node2def = {}
    def2node = {}
    id2def = {}
    def2id = {}
    def_idx = 0
    for n in nx.dfs_preorder_nodes(cfg, source=cfg.graph["entry"]):
        ast_node = cfg.nodes[n]["n"]
        _id = get_definition(ast_node)
        if _id is not None:
            node2def[n] = def_idx
            def2node[def_idx] = n

            if _id not in id2def:
                id2def[_id] = set()
            id2def[_id].add(def_idx)
            def2id[def_idx] = _id

            def_idx += 1
    if verbose >= 1:
        print("node2def", node2def)
        print("def2id", def2id)

    _in = {}
    out = {}
    for n in cfg.nodes():
        out[n] = set() # can optimize by OUT[n] = GEN[n];

    q = list(cfg.nodes())
    i = 0
    while q:
        n = q.pop(0)
        
        _in[n] = set()
        for pred in cfg.predecessors(n):
            _in[n] |= out[pred]
        
        new_out_n = gen(n, node2def).union(_in[n].difference(kill(n, node2def, id2def, def2id)))

        if verbose >= 2:
            print(f"{i=}, {n=}, {_in=}, {out=}, {new_out_n=}")

        if out[n] != new_out_n:
            if verbose >= 1:
                print(f"{i=}, {n=} changed {out[n]} -> {new_out_n}")
            out[n] = new_out_n
            for succ in cfg.successors(n):
                q.append(succ)
        i += 1
    
    return out

def test_solve():
    code = """int main()
    {
        int x = 0;
        if (true) {
            x += 5;
        }
        printf("%d\\n", x);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    cfg = v.cfg
    solution = solve(cfg, verbose=1)
    print(solution)
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "return" in attr["label"])] == {2}
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "printf" in attr["label"])] == {0, 1}
    draw(cfg)
