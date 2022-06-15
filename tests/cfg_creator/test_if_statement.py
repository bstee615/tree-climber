from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx

def test_if_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true) {
            x += 5;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_nocompound():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true)
            x += 5;
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_empty():
    tree = c_parser.parse(bytes("""int main()
    {
        if (true) {
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (3, 2)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_noelse():
    tree = c_parser.parse(bytes("""int main()
    {
        if (x > 1) {
            x += 5;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(v.cfg)

def test_if_else():
    tree = c_parser.parse(bytes("""int main()
    {
        if (x > 1) {
            x += 5;
        }
        else {
            x += 50;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert nx.is_directed_acyclic_graph(v.cfg)