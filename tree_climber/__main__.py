from pathlib import Path
from .cfg_creator import CfgVisitor, visualize_cfg
from .ast_creator import AstVisitor, visualize_ast
from .dataflow.def_use import make_duc
from .export.cpg import make_cpg, visualize_cpg
import argparse
from tree_sitter_languages import get_parser
from .analysis.bug_detection import detect_bugs


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
