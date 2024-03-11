import networkx as nx

class Counter:
    """Utility class to keep track of an incrementable counter."""
    def __init__(self):
        self._id = 0
    
    def get(self):
        return self._id
    
    def get_and_increment(self):
        _id = self.get()
        self._id += 1
        return _id

def extract_subgraph(G, edge_type):
    """Extract an edge subgraph with a given type."""
    return nx.edge_subgraph(
        G,
        [
            (u, v, k)
            for u, v, k, attr in G.edges(data=True, keys=True)
            if attr["graph_type"] == edge_type
        ],
    )
