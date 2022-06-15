from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser
import networkx as nx

def test_for_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10; i ++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_simple():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10; i ++)
            x = 0;
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinit():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; i < 10; i ++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nocond():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; ; i++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; i < 10;) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinitincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; i < 10;) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_noinitcond():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; ; i++) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nocondincr():
    tree = c_parser.parse(bytes("""int main()
    {
        for (int i = 0; ; ) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(v.cfg))) == 1

def test_for_nothing():
    tree = c_parser.parse(bytes("""int main()
    {
        for (; ; ) {
            x = 0;
        }
    }
    """, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    assert (v.cfg.number_of_nodes(), v.cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(v.cfg))) == 1
