from pathlib import Path
from .cfg_creator import CfgVisitor, visualize_cfg
from .ast_creator import AstVisitor, visualize_ast
from .dataflow.def_use import make_duc
from .export.cpg import make_cpg, visualize_cpg
import argparse
from tree_sitter_languages import get_parser
from tree_sitter import Node


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename to parse")
    args = parser.parse_args()

    args.filename = Path(args.filename)
    if args.filename.is_dir():
        filenames = list(args.filename.rglob("*.c"))
    elif args.filename.is_file():
        filenames = [args.filename]
    else:
        raise FileNotFoundError(args.filename)
        
    parser = get_parser("c")

    print("parsing", len(filenames), "files", filenames[:5])
    for filename in filenames:
        with open(filename, "rb") as f:
            tree = parser.parse(f.read())
        
        # Parse AST
        ast_visitor = AstVisitor()
        ast_root = ast_visitor.visit(tree.root_node)
        ast = ast_visitor.graph
        visualize_ast(ast, "ast.html")

        # Parse CFG
        cfg_visitor = CfgVisitor()
        cfg_entry, _ = cfg_visitor.visit(tree.root_node)
        cfg_visitor.postprocess()
        cfg = cfg_visitor.graph
        visualize_cfg(cfg, "cfg.html")

        print("successfully parsed", filename)

        # TODO update
        # duc = make_duc(cfg_visitor.graph)
        duc = None

        cpg = make_cpg(ast, cfg, duc)
        visualize_cpg(cpg, "cpg.html")

        # TODO update
        # detect_bugs(cpg)
