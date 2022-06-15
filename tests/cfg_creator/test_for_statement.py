from tests.utils import parse_and_create_cfg
import networkx as nx

def test_for_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10; i ++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_simple():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10; i ++)
            x = 0;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinit():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; i < 10; i ++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nocond():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; ; i++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (6, 6)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; i < 10;) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinitincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; i < 10;) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_noinitcond():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; ; i++) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nocondincr():
    cfg = parse_and_create_cfg("""int main()
    {
        for (int i = 0; ; ) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (5, 5)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_nothing():
    cfg = parse_and_create_cfg("""int main()
    {
        for (; ; ) {
            x = 0;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (4, 4)
    assert len(list(nx.simple_cycles(cfg))) == 1
