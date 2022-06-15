from tests.utils import *
import networkx as nx

def test_if_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        if (true) {
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(cfg)

def test_if_nocompound():
    cfg = parse_and_create_cfg("""int main()
    {
        if (true)
            x += 5;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(cfg)

def test_if_empty():
    cfg = parse_and_create_cfg("""int main()
    {
        if (true) {
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (3, 2)
    assert nx.is_directed_acyclic_graph(cfg)

def test_if_noelse():
    cfg = parse_and_create_cfg("""int main()
    {
        if (x > 1) {
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert nx.is_directed_acyclic_graph(cfg)

def test_if_else():
    cfg = parse_and_create_cfg("""int main()
    {
        if (x > 1) {
            x += 5;
        }
        else {
            x += 50;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert nx.is_directed_acyclic_graph(cfg)

def test_if_nested():
    cfg = parse_and_create_cfg("""int main()
    {
        if (true) {
            if (false) {
                x += 5;
            }
            else {

            }
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 6)
    assert nx.is_directed_acyclic_graph(cfg)