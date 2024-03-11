import networkx as nx

def detect_npd(cpg):
    """
    Detect Null-Pointer Dereference bugs using reaching definitions
    """

    # Extract AST and DUC from CPG for manipulation
    ast = nx.edge_subgraph(
        cpg,
        [
            (u, v, k)
            for u, v, k, attr in cpg.edges(data=True, keys=True)
            if attr["graph_type"] == "AST"
        ],
    )
    duc = nx.edge_subgraph(
        cpg,
        [
            (u, v, k)
            for u, v, k, attr in cpg.edges(data=True, keys=True)
            if attr["graph_type"] == "DUC"
        ],
    )

    # Get all NULL assignments
    null_assignment = [
        n
        for n, attr in cpg.nodes(data=True)
        if attr.get("node_type", "<NO TYPE>")
        in ("expression_statement", "init_declarator")
        and any(
            ast.nodes[m].get("node_type", "<NO TYPE>") == "null"
            for m in nx.descendants(ast, n)
        )
    ]

    def succ(n, typ):
        """Return the next successor with a given node type."""
        return next(
            (
                ch
                for ch in ast.adj[n]
                if cpg.nodes[ch]["node_type"] == typ
            ),
            None,
        )

    # Starting from NULL assignments...
    for ass in null_assignment:
        # Find usages...
        for usage in duc.adj.get(ass, []):
            usage_attr = cpg.nodes[usage]
            call_expr = succ(usage, "call_expression")
            # Which are calls...
            if call_expr is not None:
                id_expr = succ(call_expr, "identifier")
                if id_expr is not None:
                    id_expr_attr = cpg.nodes[id_expr]
                    # To printf...
                    if id_expr_attr["code"] == "printf":
                        print(
                            f"""possible npd of {next(attr["label"] for u, v, k, attr in duc.edges(data=True, keys=True) if u == ass and v == usage)} at line {id_expr_attr["start"][0]+1} column {id_expr_attr["start"][1]+1}: {usage_attr["code"]}"""
                        )
