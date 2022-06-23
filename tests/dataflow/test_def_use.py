from tree_sitter_cfg.dataflow.def_use import get_def_use_chain
from tree_sitter_cfg.tree_sitter_utils import c_parser
from tree_sitter_cfg.cfg_creator import CFGCreator
import matplotlib.pyplot as plt
import networkx as nx
from tests.utils import draw

def test_get_def_use_chain():
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
    duc = get_def_use_chain(cfg)

    assignment_0_node = next(n for n, attr in duc.nodes(data=True) if "x = 0" in attr["label"])
    true_node = next(n for n, attr in duc.nodes(data=True) if "true" in attr["label"])
    plus_assignment_5_node = next(n for n, attr in duc.nodes(data=True) if "x += 5" in attr["label"])
    assignment_10_node = next(n for n, attr in duc.nodes(data=True) if "x = 10" in attr["label"])
    printf_node = next(n for n, attr in duc.nodes(data=True) if "printf" in attr["label"])
    return_node = next(n for n, attr in duc.nodes(data=True) if "return" in attr["label"])
    assert not any(set(duc.predecessors(assignment_0_node)))  # first assignment to x
    assert not any(set(duc.predecessors(true_node)))
    assert set(duc.predecessors(printf_node)) == {plus_assignment_5_node, assignment_0_node}  # printf can print x defined by "x = 0" or "x += 5"
    assert set(duc.predecessors(return_node)) == {assignment_10_node}  # return is dominated by "x = 10"
    assert set(duc.predecessors(plus_assignment_5_node)) == {plus_assignment_5_node, assignment_0_node}  # TODO: += should take into account its predecessor x

    _, ax = plt.subplots(2)
    pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog='dot')
    nx.draw(duc, pos=pos, labels={n: attr["label"] for n, attr in duc.nodes(data=True)}, with_labels = True, ax=ax[0])
    draw(cfg, ax=ax[1])
