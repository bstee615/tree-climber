from tree_sitter_languages import get_parser

from tree_sprawler.cfg.languages.c import CCFGVisitor
from tree_sprawler.cfg.visitor import CFG


def get_visitor(language: str) -> CCFGVisitor:
    """Get the appropriate visitor class based on the language"""
    if language == "c":
        return CCFGVisitor()
    else:
        raise ValueError(f"Unsupported language: {language}")


class CFGBuilder:
    """Main CFG builder class"""

    def __init__(self, language: str):
        # You'll need to install tree-sitter-c and set up the language
        # This is a placeholder - actual setup depends on your tree-sitter installation
        self.parser = None
        self.language = language

    def setup_parser(self):
        """Set up the tree-sitter parser for C"""
        self.parser = get_parser(self.language)
        pass

    def build_cfg(self, source_code: str) -> CFG:
        """Build CFG from source code"""
        if not self.parser:
            raise RuntimeError("Parser not set up. Call setup_parser() first.")

        # Parse the source code
        tree = self.parser.parse(bytes(source_code, "utf8"))
        root_node = tree.root_node

        # Create visitor and build CFG
        visitor = get_visitor(self.language)

        # Find function definitions and process them
        for child in root_node.children:
            if child.type == "function_definition":
                visitor.visit(child)

        visitor.postprocess_cfg()

        return visitor.cfg
