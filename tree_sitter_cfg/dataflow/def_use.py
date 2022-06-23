import networkx as nx
from tree_sitter_cfg.tree_sitter_utils import c_parser
from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.dataflow.reaching_def import ReachingDefinitionSolver
import matplotlib.pyplot as plt
from tests.utils import draw

def get_uses(cfg, solver, n):
    """return the set of variables used in n"""
    q = [cfg.nodes[n]["n"]]
    used_ids = set()
    while q:
        n = q.pop(0)
        if n.type == "identifier":
            _id = n.text.decode()
            if _id in solver.id2def.keys():
                used_ids.add(_id)
        q.extend(n.children)
    return used_ids

def get_def_use(cfg):
    """return def-use chain"""
    dug = nx.DiGraph()
    dug.add_nodes_from(cfg.nodes(data=True))
    solver = ReachingDefinitionSolver(cfg, verbose=1)
    solution_in, solution_out = solver.solve()
    solution = solution_in
    for n in cfg.nodes():
        incoming_defs = solution[n]
        if any(incoming_defs):
            use_node = n

            def_ids = set(map(solver.def2id.__getitem__, incoming_defs))
            used_ids = get_uses(cfg, solver, use_node)
            used_def_ids = def_ids & used_ids
            print(f"{use_node=} {def_ids=} {used_ids=} {used_def_ids=}")
            if any(used_def_ids):
                used_defs = set.union(*map(solver.id2def.__getitem__, used_def_ids))
                used_incoming_defs = used_defs & incoming_defs
                
                def_nodes = set(map(solver.def2node.__getitem__, used_incoming_defs))
                for def_node in def_nodes:
                    dug.add_edge(def_node, use_node)
    return dug


def test_simple():
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
    true_node = next(n for n, attr in dug.nodes(data=True) if "true" in attr["label"])
    plus_assignment_5_node = next(n for n, attr in dug.nodes(data=True) if "x += 5" in attr["label"])
    assignment_10_node = next(n for n, attr in dug.nodes(data=True) if "x = 10" in attr["label"])
    printf_node = next(n for n, attr in dug.nodes(data=True) if "printf" in attr["label"])
    return_node = next(n for n, attr in dug.nodes(data=True) if "return" in attr["label"])
    assert not any(set(dug.predecessors(assignment_0_node)))  # first assignment to x
    assert not any(set(dug.predecessors(true_node)))
    assert set(dug.predecessors(printf_node)) == {plus_assignment_5_node, assignment_0_node}  # printf can print x defined by "x = 0" or "x += 5"
    assert set(dug.predecessors(return_node)) == {assignment_10_node}  # return is dominated by "x = 10"
    assert set(dug.predecessors(plus_assignment_5_node)) == {plus_assignment_5_node, assignment_0_node}  # TODO: += should take into account its predecessor x

    _, ax = plt.subplots(2)
    pos = nx.drawing.nx_agraph.graphviz_layout(dug, prog='dot')
    nx.draw(dug, pos=pos, labels={n: attr["label"] for n, attr in dug.nodes(data=True)}, with_labels = True, ax=ax[0])
    draw(cfg, ax=ax[1])

