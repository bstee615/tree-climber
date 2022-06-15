from tests.utils import *
import networkx as nx

def test_return_exclude():
    cfg = parse_and_create_cfg("""int main()
    {
        return;
        x += 5;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (3, 2)
    assert nx.is_directed_acyclic_graph(cfg)
    assert not any(n for n, attr in cfg.nodes(data=True) if "x" in attr["label"])

def test_continue_exclude():
    cfg = parse_and_create_cfg("""int main()
    {
        for (;;) {
            continue;
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1
    assert not any(n for n, attr in cfg.nodes(data=True) if "x" in attr["label"])

def test_break_exclude():
    cfg = parse_and_create_cfg("""int main()
    {
        for (;;) {
            break;
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 0
    assert not any(n for n, attr in cfg.nodes(data=True) if "x" in attr["label"])
