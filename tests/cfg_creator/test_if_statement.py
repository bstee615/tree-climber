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
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (3, 3)
    assert nx.is_directed_acyclic_graph(cfg)

    true_node = next(n for n, attr in cfg.nodes(data=True) if "true" in attr["label"])
    func_exit_node = next(n for n, attr in cfg.nodes(data=True) if "FUNC_EXIT" in attr["label"])
    edges_between = cfg.adj[true_node][func_exit_node]
    assert set(e.get("label", "<NO LABEL>") for e in edges_between.values()) == set(("True", "False"))

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