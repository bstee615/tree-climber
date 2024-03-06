import networkx as nx


def detect_bugs(cpg):
    # detect npd bug with reaching definition
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
    for ass in null_assignment:
        for usage in duc.adj[ass]:
            usage_attr = cpg.nodes[usage]
            call_expr = next(
                (
                    ch
                    for ch in ast.adj[usage]
                    if cpg.nodes[ch]["node_type"] == "call_expression"
                ),
                None,
            )
            if call_expr is None:
                continue
            id_expr = next(
                ch
                for ch in ast.adj[call_expr]
                if cpg.nodes[ch]["node_type"] == "identifier"
            )
            id_expr_attr = cpg.nodes[id_expr]
            if id_expr_attr["code"] == "printf":
                print(
                    f"""possible npd of {next(attr["label"] for u, v, k, attr in duc.edges(data=True, keys=True) if u == ass and v == usage)} at line {id_expr_attr["start"][0]+1} column {id_expr_attr["start"][1]+1}: {usage_attr["code"]}"""
                )
