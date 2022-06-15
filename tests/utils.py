from tree_sitter_cfg.cfg_creator import CFGCreator
from tree_sitter_cfg.tree_sitter_utils import c_parser

def parse_and_create_cfg(code):
    tree = c_parser.parse(bytes(code, "utf8"))
    v = CFGCreator()
    v.visit(tree.root_node)
    return v.cfg
