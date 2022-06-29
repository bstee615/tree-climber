from tests.utils import *
import networkx as nx

def test_switch_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        switch(true) {
            case 0:
                return 0;
            default:
                return 1;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert nx.is_directed_acyclic_graph(cfg)

def test_switch_complex():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        switch(x) {
            case 0:
                return 0;
            case 1:
                return 1;
            case 2:
                x ++;
            default:
                x = -1;
                break;
        }
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (10, 12)
    assert nx.is_directed_acyclic_graph(cfg)

    cond_node = next(n for n, attr in cfg.nodes(data=True) if "`x`" in attr["label"])
    return_0_node = next(n for n, attr in cfg.nodes(data=True) if "return 0" in attr["label"])
    return_1_node = next(n for n, attr in cfg.nodes(data=True) if "return 1" in attr["label"])
    x_plus_node = next(n for n, attr in cfg.nodes(data=True) if "x ++" in attr["label"])
    x_minus_node = next(n for n, attr in cfg.nodes(data=True) if "x = -1" in attr["label"])
    break_node = next(n for n, attr in cfg.nodes(data=True) if "break" in attr["label"])
    return_x_node = next(n for n, attr in cfg.nodes(data=True) if "return x" in attr["label"])

    assert cfg.edges[(cond_node, return_0_node)].get("label", "<NO LABEL>") == "case 0:"
    assert cfg.edges[(cond_node, return_1_node)].get("label", "<NO LABEL>") == "case 1:"
    assert cfg.edges[(cond_node, x_plus_node)].get("label", "<NO LABEL>") == "case 2:"
    assert cfg.edges[(cond_node, x_minus_node)].get("label", "<NO LABEL>") == "default:"
    assert cfg.edges[(break_node, return_x_node)].get("label", "<NO LABEL>") == "break"

def test_switch_nodefault():
    cfg = parse_and_create_cfg("""int main()
    {
        switch(-1) {
            case 0:
                return 0;
            case 1:
                return 1;
        }
        return 5;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 7)
    assert nx.is_directed_acyclic_graph(cfg)

    cond_node = next(n for n, attr in cfg.nodes(data=True) if "-1" in attr["label"])
    return_0_node = next(n for n, attr in cfg.nodes(data=True) if "return 0" in attr["label"])
    return_1_node = next(n for n, attr in cfg.nodes(data=True) if "return 1" in attr["label"])
    return_5_node = next(n for n, attr in cfg.nodes(data=True) if "return 5" in attr["label"])

    assert cfg.edges[(cond_node, return_0_node)].get("label", "<NO LABEL>") == "case 0:"
    assert cfg.edges[(cond_node, return_1_node)].get("label", "<NO LABEL>") == "case 1:"
    assert cfg.edges[(cond_node, return_5_node)].get("label", "<NO LABEL>") == "default:"
