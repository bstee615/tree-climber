from tree_climber.cfg_parser import CFGParser
from tree_climber.config import DRAW_CFG
import networkx as nx
import matplotlib.pyplot as plt

def draw(cfg, dataflow_solution=None, ax=None):
    pos = nx.nx_pydot.graphviz_layout(cfg, prog="dot")
    nx.draw_networkx_nodes(cfg, pos=pos, ax=ax)
    double_edges = [(u, v, attr.get("label", "")) for u, v, attr in cfg.edges(data=True) if u in cfg.successors(v) and v in cfg.successors(u)]
    single_edges = [(u, v, attr.get("label", "")) for u, v, attr in cfg.edges(data=True) if (u, v, attr.get("label", "")) not in double_edges]
    nx.draw_networkx_edges(cfg, pos=pos, edgelist=[(u, v) for u, v, label in single_edges], ax=ax)
    nx.draw_networkx_edge_labels(cfg, pos=pos, edge_labels={(u, v): label for u, v, label in single_edges})
    nx.draw_networkx_edges(cfg, pos=pos, edgelist=[(u, v) for u, v, label in double_edges], connectionstyle=f"arc3,rad=0.1")
    nx.draw_networkx_edge_labels(cfg, pos=pos, edge_labels={(u, v): label for u, v, label in double_edges})#, connectionstyle=f"arc3,rad=0.1")
    nx.draw_networkx_labels(cfg, pos=pos, labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)}, ax=ax)
    if dataflow_solution is not None:
        nx.draw_networkx_labels(cfg, pos=pos, font_color="r", labels={n: "\n\n\n{" + ", ".join(dataflow_solution[n]) + "}" if dataflow_solution[n] else "" for n in cfg.nodes()}, ax=ax)
    plt.show()


def parse_and_create_cfg(code, print_ast=False, draw_cfg=bool(DRAW_CFG)):
    return CFGParser(code)

def get_adj_label(cfg, u, v):
    """get label of first edge connecting u and v in cfg"""
    return list(cfg.adj[u][v].values())[0].get("label", "<NO LABEL>")

def get_node_by_code(cfg, code, get="first"):
    matches = (n for n, attr in cfg.nodes(data=True) if code == attr.get("code", "<NO CODE>"))
    if get == "first":
        return next(matches)
    elif get == "all":
        return list(matches)
    else:
        raise NotImplementedError(get)

def get_node_by_label(cfg, label):
    return next(n for n, attr in cfg.nodes(data=True) if label == attr.get("label", "<NO LABEL>"))
