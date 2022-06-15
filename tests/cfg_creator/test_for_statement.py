from tests.utils import *
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

def test_for_nocompound():
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

def test_for_nested():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            for (int j = 0; j < 10; j ++) {
                x += j;
            }
            x -= i;
        }
        return x;
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (12, 13)
    assert len(list(nx.simple_cycles(cfg))) == 2

def test_for_break():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            if (x > 5) {
                x = 0;
                break;
            }
            x = 10;
            if (i < 5) {
                return -1;
            }
            x += 5;
        }
        x = 10;
        return x;
    }
    """, draw_cfg=True)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (13, 15)
    assert len(list(nx.simple_cycles(cfg))) == 1

def test_for_continue():
    cfg = parse_and_create_cfg("""int main()
    {
        int x = 0;
        for (int i = 0; i < 10; i ++) {
            if (x > 5) {
                x = 0;
                continue;
            }
            x = 10;
            if (i < 5) {
                continue;
            }
            x += 5;
        }
    }
    """)
    assert (cfg.number_of_nodes(), cfg.number_of_edges()) == (13, 15)
    assert len(list(nx.simple_cycles(cfg))) == 3
