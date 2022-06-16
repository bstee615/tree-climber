import networkx as nx
from tree_sitter_cfg.tree_sitter_utils import c_parser
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.dataflow.reaching_def import ReachingDefinitionSolver
import matplotlib.pyplot as plt
from tests.utils import draw

def get_def_use(cfg):
    G = nx.DiGraph()
    solver = ReachingDefinitionSolver(cfg, verbose=1)
    solution = solver.solve()
    print(solution)
    # assert solution[next(n for n, attr in cfg.nodes(data=True) if "return" in attr["label"])] == {2}
    # assert solution[next(n for n, attr in cfg.nodes(data=True) if "printf" in attr["label"])] == {0, 1}
    # draw(cfg, {n: sorted(set(map(solver.def2code.__getitem__, b))) for n, b in solution.items()})
    labeldict = {}
    for n, attr in cfg.nodes(data=True):
        if n in solver.node2def:
            use_node = n
            def_idx = solver.node2def[use_node]
            def_node = solver.def2id[def_idx]
            G.add_edge(use_node, def_node)
            labeldict[n] = attr["label"]
    # labeldict = nx.get_node_attributes(G, "label")
    print(labeldict)
    nx.draw(G, labels=labeldict, with_labels = True)
    plt.show()
    plt.close()
    draw(cfg)
    plt.show()


def test():
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
    cfg = v.generate_cfg(tree.root_node)
    get_def_use(cfg)

