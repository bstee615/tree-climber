import copy
import networkx as nx
import matplotlib.pyplot as plt


def escape_labels(graph):
    graph = copy.deepcopy(graph)
    for n, d in graph.nodes(data=True):
        for k in list(d.keys()):
            if k == "label":
                if ":" in graph.nodes[n][k]:
                    graph.nodes[n][k] = f'"{graph.nodes[n][k]}"'
            else:
                del graph.nodes[n][k]
    return graph


def draw_ast(ast):
    # ast = escape_labels(ast)
    pos = nx.drawing.nx_agraph.graphviz_layout(ast, prog="dot")
    nx.draw(
        ast,
        pos=pos,
        labels={n: attr["label"] for n, attr in ast.nodes(data=True)},
        with_labels=True,
    )
    plt.show()


def draw_cfg(cfg, entry=None):
    # cfg = escape_labels(cfg)
    if cfg.number_of_nodes() > 1000 or cfg.number_of_edges() > 1000:
        print("fuck man I'm not drawing that!")
        return
    pos = nx.spring_layout(cfg, seed=0)
    nx.draw(cfg, pos=pos)
    nx.draw_networkx_labels(
        cfg,
        pos=pos,
        labels={n: attr.get("label", "<NO LABEL>") for n, attr in cfg.nodes(data=True)},
    )
    if entry is not None:
        plt.title(cfg.nodes[entry]["n"].text)
    plt.show()


def draw_duc(duc):
    # duc = escape_labels(duc)
    pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog="dot")
    nx.draw(
        duc,
        pos=pos,
        labels={n: attr["label"] for n, attr in duc.nodes(data=True)},
        with_labels=True,
    )
    nx.draw_networkx_edge_labels(
        duc,
        pos=pos,
        edge_labels={
            (u, v): attr.get("label", "") for u, v, attr in duc.edges(data=True)
        },
    )
    plt.show()


def draw_cpg(cpg):
    for (n, d) in cpg.nodes(data=True):
        for k in list(d.keys()):
            if k != "label":
                del d[k]
    pos = nx.nx_pydot.graphviz_layout(cpg, prog="dot")
    nx.draw(cpg, pos=pos)
    nx.draw_networkx_labels(
        cpg,
        pos=pos,
        labels={n: attr.get("label", "<NO LABEL>") for n, attr in cpg.nodes(data=True)},
    )
    for graph_type, color in {
        "AST": "black",
        "CFG": "blue",
        "DUC": "red",
    }.items():
        nx.draw_networkx_edges(
            cpg,
            pos=pos,
            edge_color=color,
            edgelist=[
                (u, v)
                for u, v, k, attr in cpg.edges(keys=True, data=True)
                if attr["graph_type"] == graph_type
            ],
        )
    nx.draw_networkx_edge_labels(
        cpg,
        pos=pos,
        edge_labels={
            (u, v): attr.get("label", "")
            for u, v, k, attr in cpg.edges(keys=True, data=True)
        },
    )
    plt.show()
