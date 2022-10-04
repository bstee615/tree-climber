"""
Utilities for manipulating/traversing networkx graphs.
"""


def subgraph(graph, edge_types):
    """
    Return a subgraph induced by the edge types.
    """
    return graph.edge_subgraph(
        [
            (u, v, k)
            for u, v, k, attr in graph.edges(data=True, keys=True)
            if attr["graph_type"] in edge_types
        ]
    )
