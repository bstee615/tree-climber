from tree_sprawler.cfg_parser.cfg_visitor import CFG, NodeType
from tree_sprawler.cfg_parser.languages.c import CCFGVisitor
import graphviz


from tree_sitter_languages import get_parser


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

    def visualize_cfg(self, cfg: CFG, output_file: str = "cfg"):
        """Generate a visual representation of the CFG using Graphviz"""
        dot = graphviz.Digraph(comment=f"CFG for {cfg.function_name}")
        dot.attr(rankdir="TB")

        # Add nodes
        for node_id, node in cfg.nodes.items():
            shape = "ellipse"
            color = "lightblue"

            if node.node_type == NodeType.ENTRY:
                shape = "box"
                color = "lightgreen"
            elif node.node_type == NodeType.EXIT:
                shape = "box"
                color = "lightcoral"
            elif node.node_type == NodeType.CONDITION:
                shape = "diamond"
                color = "lightyellow"
            elif node.node_type == NodeType.LOOP_HEADER:
                shape = "diamond"
                color = "lightcyan"
            elif node.node_type == NodeType.SWITCH_HEAD:
                shape = "diamond"
                color = "lightpink"
            elif node.node_type == NodeType.CASE:
                shape = "box"
                color = "lightsalmon"
            elif node.node_type == NodeType.DEFAULT:
                shape = "box"
                color = "orange"
            elif node.node_type == NodeType.LABEL:
                shape = "box"
                color = "lavender"
            elif node.node_type == NodeType.GOTO:
                shape = "box"
                color = "violet"

            label = f"{node_id}: {node.source_text[:50]}"
            dot.node(str(node_id), label, shape=shape, style="filled", fillcolor=color)

        # Add edges with labels
        for node_id, node in cfg.nodes.items():
            for successor_id in node.successors:
                # Check if there's a label for this edge
                edge_label = node.get_edge_label(successor_id)
                if edge_label:
                    dot.edge(str(node_id), str(successor_id), label=edge_label)
                else:
                    dot.edge(str(node_id), str(successor_id))

        dot.render(output_file, format="png", cleanup=True)
        return f"{output_file}.png"