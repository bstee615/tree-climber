from tree_climber.ast_creator import ASTCreator
from tree_climber.dataflow.def_use import make_duc
from tree_climber.tree_sitter_utils import c_parser
from tree_climber.cfg_creator import CFGCreator
from tests.utils import *
import pytest


def test_get_def_use_chain():
    code = """int a = 3;
    
    int main()
    {
        int i = 0;
        int x = 0;
        end:
        x -= a;
        for (; true; ) {
            x += 5;
            if (x < 0) {
                goto end;
            }
        }
        printf("%d %d\\n", x, i);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)

    init_x_node = get_node_by_code(duc, "int x = 0;")
    init_i_node = get_node_by_code(duc, "int i = 0;")
    true_node = get_node_by_code(duc, "true")
    a_assign_3_node = get_node_by_code(duc, "int a = 3;")
    x_minus_assign_a_node = get_node_by_code(duc, "x -= a;")
    x_plus_assign_5_node = get_node_by_code(duc, "x += 5;")
    x_assign_10_node = get_node_by_code(duc, "x = 10;")
    printf_node = get_node_by_code(cfg, """printf("%d %d\\n", x, i);""")
    return_node = get_node_by_code(cfg, "return x;")
    assert len(list(duc.predecessors(init_x_node))) == 0  # first assignment to x
    assert len(list(duc.predecessors(true_node))) == 0
    assert set(duc.predecessors(printf_node)) == {
        x_plus_assign_5_node,
        x_minus_assign_a_node,
        init_i_node,
    }  # printf can print x defined by "x = 0" or "x += 5"
    assert set(duc.predecessors(return_node)) == {
        x_assign_10_node
    }  # return is dominated by "x = 10"
    assert set(duc.predecessors(x_plus_assign_5_node)) == {
        x_plus_assign_5_node,
        x_minus_assign_a_node,
    }  # += should take into account its predecessor x
    assert set(duc.predecessors(x_minus_assign_a_node)) == {
        x_plus_assign_5_node,
        init_x_node,
        a_assign_3_node,
    }  # x -= 3 uses x += 5 (later statement) because of goto

    assert (
        duc.edges[(x_plus_assign_5_node, x_plus_assign_5_node)].get(
            "label", "<NO LABEL>"
        )
        == "x"
    )
    assert (
        duc.edges[(x_minus_assign_a_node, x_plus_assign_5_node)].get(
            "label", "<NO LABEL>"
        )
        == "x"
    )
    assert (
        duc.edges[(x_minus_assign_a_node, printf_node)].get("label", "<NO LABEL>")
        == "x"
    )
    assert duc.edges[(init_i_node, printf_node)].get("label", "<NO LABEL>") == "i"
    assert (
        duc.edges[(x_plus_assign_5_node, printf_node)].get("label", "<NO LABEL>") == "x"
    )


@pytest.mark.slow
def test_debug():
    from tests.utils import draw

    code = """int main()
    {
        int i = 0;
        int x = 0;
        end:
        x -= 3;
        for (; true; ) {
            x += 5;
            if (x < 0) {
                goto end;
            }
        }
        printf("%d %d\\n", x, i);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)
    print(duc.nodes(data=True))

    _, ax = plt.subplots(2)
    pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog="dot")
    nx.draw(
        duc,
        pos=pos,
        labels={n: attr["label"] for n, attr in duc.nodes(data=True)},
        with_labels=True,
        ax=ax[0],
    )
    nx.draw_networkx_edge_labels(
        duc,
        pos=pos,
        edge_labels={
            (u, v): attr.get("label", "") for u, v, attr in duc.edges(data=True)
        },
        ax=ax[0],
    )
    draw(cfg, ax=ax[1])
