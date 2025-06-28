from typing import Optional

from tree_sitter import Tree
from tree_sitter_languages import get_parser

from tree_sprawler.cfg.visitor import CFG, CFGVisitor


def get_visitor(language: str) -> CFGVisitor:
    """Get the appropriate visitor class based on the language"""
    if language == "c":
        from tree_sprawler.cfg.languages.c import CCFGVisitor

        return CCFGVisitor()
    elif language == "java":
        from tree_sprawler.cfg.languages.java import JavaCFGVisitor

        return JavaCFGVisitor()
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

    def build_cfg(
        self, source_code: Optional[str] = None, tree: Optional[Tree] = None
    ) -> CFG:
        """Build CFG from source code"""
        if not self.parser:
            raise RuntimeError("Parser not set up. Call setup_parser() first.")
        if source_code is not None and tree is not None:
            raise ValueError("Only one of source_code or tree should be provided.")

        if source_code is not None:
            # Parse the source code
            tree = self.parser.parse(bytes(source_code, "utf8"))
            if tree is None:
                raise ValueError("Failed to parse source code.")
            root_node = tree.root_node
        elif tree is not None:
            # Use the provided tree
            root_node = tree.root_node
        else:
            raise ValueError(
                "Either source_code or tree must be provided, but both are None."
            )

        # Create visitor and build CFG
        visitor = get_visitor(self.language)
        visitor.visit(root_node)

        visitor.postprocess_cfg()

        return visitor.cfg
