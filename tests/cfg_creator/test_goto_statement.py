from tests.utils import *
import networkx as nx

def test_label_simple():
    cfg = parse_and_create_cfg("""int main()
{
    int x = 0;
end:
    x = 10;
    return x;
}
""")
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 5)
    assert nx.is_directed_acyclic_graph(cfg)

    FUNC_ENTRY_node = get_node_by_label(cfg, "FUNC_ENTRY")
    x_10_node = get_node_by_code(cfg, "x = 10;")
    assert len(list(nx.all_simple_paths(cfg, FUNC_ENTRY_node, x_10_node))) > 0


def test_goto_label_simple():
    cfg = parse_and_create_cfg("""int main()
{
    int x = 0;
    goto end;
end:
    x = 10;
    return x;
}
""")
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (7, 6)
    assert nx.is_directed_acyclic_graph(cfg)

    FUNC_ENTRY_node = get_node_by_label(cfg, "FUNC_ENTRY")
    goto_node = get_node_by_code(cfg, "goto end;")
    label_node = get_node_by_code(cfg, "end:")
    x_10_node = get_node_by_code(cfg, "x = 10;")
    assert get_adj_label(cfg, goto_node, label_node) == "goto"
    assert len(list(nx.all_simple_paths(cfg, FUNC_ENTRY_node, x_10_node))) > 0


def test_goto_():
    cfg = parse_and_create_cfg("""int main()
{
    int x = 0;
    goto end;
    x = 20;
end:
    x = 10;
    return x;
}
""")
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (8, 7)
    assert nx.is_directed_acyclic_graph(cfg)

    FUNC_ENTRY_node = get_node_by_label(cfg, "FUNC_ENTRY")
    goto_node = get_node_by_code(cfg, "goto end;")
    x_20_node = get_node_by_code(cfg, "x = 20;")
    x_10_node = get_node_by_code(cfg, "x = 10;")
    assert not any(x_20_node in p for p in nx.all_simple_paths(cfg, goto_node, x_10_node))
    assert list(nx.all_simple_paths(cfg, FUNC_ENTRY_node, x_20_node)) == []
