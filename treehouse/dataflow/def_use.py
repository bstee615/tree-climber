from matplotlib import pyplot as plt
import networkx as nx
from treehouse.dataflow.reaching_def import ReachingDefinitionSolver
from tests.utils import draw
from treehouse.tree_sitter_utils import c_parser
from treehouse.ast_creator import ASTCreator
from treehouse.cfg_creator import CFGCreator

def get_uses(cfg, solver, n):
    """return the set of variables used in n"""
    q = [cfg.nodes[n]["n"]]
    used_ids = set()
    while q:
        n = q.pop(0)
        if n.type == "identifier":
            _id = n.text.decode()
            if _id in solver.id2def.keys():
                used_ids.add(_id)
        q.extend(n.children)
    return used_ids

def make_duc(cfg, verbose=0):
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
    duc = nx.DiGraph()
    duc.add_nodes_from([(n, dict(cfg_node=n, **attr)) for n, attr in cfg.nodes(data=True)])
    solver = ReachingDefinitionSolver(cfg, verbose=verbose)
    solution_in, solution_out = solver.solve()
    solution = solution_in
    for n in cfg.nodes():
        incoming_defs = solution[n]
        if len(incoming_defs) > 0:
            use_node = n

            def_ids = set(map(solver.def2id.__getitem__, incoming_defs))
            used_ids = get_uses(cfg, solver, use_node)
            used_def_ids = def_ids & used_ids
            if len(used_def_ids) > 0:
                used_defs = set.union(*map(solver.id2def.__getitem__, used_def_ids))
                used_incoming_defs = used_defs & incoming_defs
                
                def_nodes = set(map(solver.def2node.__getitem__, used_incoming_defs))
                for def_node in def_nodes:
                    duc.add_edge(def_node, use_node, label=str(solver.def2id[solver.node2def[def_node]]))
    # TODO remove FUNC_ENTRY and FUNC_EXIT
    return duc

def test():
    code = """int main()
    {
        int i = 0;
        int x = 0;
        for (; true; ) {
            x += 5;
        }
        printf("%d %d\\n", x, i);
        x = 10;
        return x;
    }
    """
    tree = c_parser.parse(bytes(code, "utf8"))
    ast = ASTCreator.make_ast(tree.root_node)
    cfg = CFGCreator.make_cfg(ast)
    duc = make_duc(cfg)
    print(duc.nodes(data=True))

    _, ax = plt.subplots(2)
    pos = nx.drawing.nx_agraph.graphviz_layout(duc, prog='dot')
    nx.draw(duc, pos=pos, labels={n: attr["label"] for n, attr in duc.nodes(data=True)}, with_labels = True, ax=ax[0])
    nx.draw_networkx_edge_labels(duc, pos=pos, edge_labels={(u, v): attr.get("label", "") for u, v, attr in duc.edges(data=True)}, ax=ax[0])
    draw(cfg, ax=ax[1])
