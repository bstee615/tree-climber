from pathlib import Path
from .cfg_creator import CfgVisitor, visualize_cfg
from .ast_creator import AstVisitor, visualize_ast
from .dataflow.def_use import make_duc, visualize_duc
from .views.cpg import make_cpg, visualize_cpg
import argparse
from tree_sitter_languages import get_parser
from .analysis.bug_detection import detect_bugs
import traceback


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filenames", help="filename to parse", nargs="+")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    # args.filename = Path(args.filename)
    # if args.filename.is_dir():
    #     filenames = list(args.filename.rglob("*.c"))
    # elif args.filename.is_file():
    #     filenames = [args.filename]
    # else:
    #     raise FileNotFoundError(args.filename)
    filenames = args.filenames
        
    parser = get_parser("c")

    print("parsing", len(filenames), "files", filenames[:5])
    for filename in filenames:
        try:
            with open(filename, "rb") as f:
                tree = parser.parse(f.read())
            
            # Parse AST
            ast_visitor = AstVisitor()
            ast_root = ast_visitor.visit(tree.root_node)
            ast = ast_visitor.graph
            # visualize_ast(ast, "ast.html")

            # Parse CFG
            cfg_visitor = CfgVisitor()
            cfg_entry, _ = cfg_visitor.visit(tree.root_node)
            cfg_visitor.postprocess()
            cfg = cfg_visitor.graph
            # visualize_cfg(cfg, "cfg.html")

            print("successfully parsed", filename)

            try:
                duc = make_duc(cfg)
                # visualize_duc(duc, "duc.html")
            except Exception as ex:
                if args.strict:
                    raise
                print(f"Could not parse DUC for {filename}: {ex}")
                traceback.print_exc()
                duc = None

            cpg = make_cpg(ast, cfg, duc)
            # visualize_cpg(cpg, "cpg.html")

            # TODO update
            # detect_bugs(cpg)
            # print("SUCCESS!")
            break
        except Exception as ex:
            print(f"Could not parse {filename}: {ex}")
            traceback.print_exc()
