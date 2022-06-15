"""
An instance of a dataflow problem includes:
- a CFG,
- a domain D of "dataflow facts",
- a dataflow fact "init" (the information true at the start of the program for forward problems, or at the end of the program for backward problems),
- an operator ⌈⌉ (used to combine incoming information from multiple predecessors),
- for each CFG node n, a dataflow function fn : D → D (that defines the effect of executing n). 
"""

from tests.utils import *

class DataflowProblem:
    """
    generic dataflow problem solver with worklist algorithm
    """
    def __init__(self, cfg, verbose):
        self.cfg = cfg
        self.verbose = verbose

    def solve(self):
        _in = {}
        out = {}
        for n in self.cfg.nodes():
            out[n] = set() # can optimize by OUT[n] = GEN[n];

        q = list(self.cfg.nodes())
        i = 0
        while q:
            n = q.pop(0)
            
            # TODO: generalize to backward problems
            _in[n] = set()
            for pred in self.cfg.predecessors(n):
                _in[n] |= out[pred]
            
            # TODO: generalize to backward problems
            new_out_n = self.gen(n).union(_in[n].difference(self.kill(n)))

            if self.verbose >= 2:
                print(f"{i=}, {n=}, {_in=}, {out=}, {new_out_n=}")

            if out[n] != new_out_n:
                if self.verbose >= 1:
                    print(f"{i=}, {n=} changed {out[n]} -> {new_out_n}")
                out[n] = new_out_n
                for succ in self.cfg.successors(n):
                    q.append(succ)
            i += 1
        
        return out

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

class ReachingDefinitionProblem(DataflowProblem):
    """
    reaching definition
    https://en.wikipedia.org/wiki/Reaching_definition
    """

    def __init__(self, cfg, verbose):
        super().__init__(cfg, verbose)

        node2def = {}
        id2def = {}
        def2id = {}
        def_idx = 0
        for n in nx.dfs_preorder_nodes(cfg, source=cfg.graph["entry"]):
            ast_node = cfg.nodes[n]["n"]
            _id = get_definition(ast_node)
            if _id is not None:
                node2def[n] = def_idx

                if _id not in id2def:
                    id2def[_id] = set()
                id2def[_id].add(def_idx)
                def2id[def_idx] = _id

                def_idx += 1
        if verbose >= 1:
            print("node2def", node2def)
            print("def2id", def2id)
        self.node2def = node2def
        self.id2def = id2def
        self.def2id = def2id

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
    solution = ReachingDefinitionProblem(cfg, verbose=1).solve()
    print(solution)
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "return" in attr["label"])] == {2}
    assert solution[next(n for n, attr in cfg.nodes(data=True) if "printf" in attr["label"])] == {0, 1}
    draw(cfg)
