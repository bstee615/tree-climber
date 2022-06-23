import networkx as nx
from tree_sitter_cfg.tree_sitter_utils import c_parser
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.dataflow.reaching_def import ReachingDefinitionSolver
import matplotlib.pyplot as plt
from tests.utils import draw

def get_def_use(cfg):
    dug = nx.DiGraph()
    dug.add_nodes_from(cfg.nodes(data=True))
    solver = ReachingDefinitionSolver(cfg, verbose=1)
    solution_in, solution_out = solver.solve()
    solution = solution_in
    for n in cfg.nodes():
        incoming_defs = solution[n]
        if any(incoming_defs):
            use_node = n
            def_nodes = map(solver.def2node.__getitem__, incoming_defs)
            for def_node in def_nodes:
                # TODO: detect if this variable is used in this node
                dug.add_edge(def_node, use_node)
    return dug


def test():
    code = """int main()
    {
        int x = 0;
        for (; true; ) {
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
    dug = get_def_use(cfg)

    assignment_0_node = next(n for n, attr in dug.nodes(data=True) if "x = 0" in attr["label"])
    plus_assignment_5_node = next(n for n, attr in dug.nodes(data=True) if "x += 5" in attr["label"])
    assignment_10_node = next(n for n, attr in dug.nodes(data=True) if "x = 10" in attr["label"])
    printf_node = next(n for n, attr in dug.nodes(data=True) if "printf" in attr["label"])
    return_node = next(n for n, attr in dug.nodes(data=True) if "return" in attr["label"])
    assert not any(dug.predecessors(assignment_0_node))  # first assignment to x
    assert set(dug.predecessors(printf_node)) == {plus_assignment_5_node, assignment_0_node}  # printf can print x defined by "x = 0" or "x += 5"
    assert set(dug.predecessors(return_node)) == {assignment_10_node}  # return is dominated by "x = 10"
    assert set(dug.predecessors(plus_assignment_5_node)) == {plus_assignment_5_node, assignment_0_node}  # TODO: += should take into account its predecessor x

    _, ax = plt.subplots(2)
    nx.draw(dug, labels={n: attr["label"] for n, attr in dug.nodes(data=True)}, with_labels = True, ax=ax[0])
    draw(cfg, ax=ax[1])

