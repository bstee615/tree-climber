import networkx as nx

from tree_climber.base_parser import BaseParser
from tree_climber.cfg_parser import CFGParser
from tree_climber.dataflow.reaching_def import ReachingDefinitionSolver


def get_uses(cfg, solver, n):
    """return the set of variables used in n"""
    used_ids = set()
    attr = cfg.nodes[n]
    if "n" in attr:
        q = [attr["n"]]
        while q:
            n = q.pop(0)
            if n.type == "identifier":
                _id = n.text.decode()
                if _id in solver.id2def.keys():
                    used_ids.add(_id)
            q.extend(n.children)
    return used_ids

class DUCParser(BaseParser):
    @staticmethod
    def parse(data, verbose=0):
        """
        return def-use chain (DUC)

            https://textart.io/art/tag/duck/1
                                            ___
                                    ,-""   `.
                                    ,'  _   e )`-._
                                /  ,' `-._<.===-'
                                /  /
                                /  ;
                    _.--.__    /   ;
        (`._    _.-""       "--'    |
        <_  `-""                     |
        <`-                          :
        (__   <__.                  ;
            `-.   '-.__.      _.'    /
            |      `-.__,-'    _,'
                `._    ,    /__,-'
                ""._|__,'< <____
                        | |  `----.`.
                        | |        | `.
                        ; |___      |-``
                        |   --<
                        `.`.<
                        `-'
        """
        if isinstance(data, nx.Graph):
            assert data.graph["graph_type"] == "CFG"
            cfg = data
        else:
            cfg = CFGParser.parse(data)

        duc = nx.DiGraph()

        # Start with the CFG nodes
        duc.add_nodes_from(
            [(n, dict(cfg_node=n, **attr)) for n, attr in cfg.nodes(data=True)]
        )

        # Do dataflow analysis
        solver = ReachingDefinitionSolver(cfg, verbose=verbose)
        solution, _ = solver.solve()
        
        # Find all DUC edges.
        for n in cfg.nodes():
            incoming_defs = solution[n]
            if len(incoming_defs) > 0:
                use_node = n

                # TODO: Make utility methods
                def_ids = set(map(solver.def2id.__getitem__, incoming_defs))
                used_ids = get_uses(cfg, solver, use_node)
                used_def_ids = def_ids & used_ids
                if len(used_def_ids) > 0:
                    used_defs = set.union(*map(solver.id2def.__getitem__, used_def_ids))
                    used_incoming_defs = used_defs & incoming_defs

                    def_nodes = set(map(solver.def2node.__getitem__, used_incoming_defs))
                    for def_node in def_nodes:
                        duc.add_edge(
                            def_node,
                            use_node,
                            label=str(solver.def2id[solver.node2def[def_node]]),
                        )
        duc.remove_nodes_from(
            [
                n
                for n, attr in duc.nodes(data=True)
                if attr["label"] in ("FUNC_ENTRY", "FUNC_EXIT")
            ]
        )
        duc.graph["graph_type"] = "DUC"
        duc.graph["parents"] = {
            "CFG": cfg,
            **cfg.graph["parents"],
        }
        return duc
