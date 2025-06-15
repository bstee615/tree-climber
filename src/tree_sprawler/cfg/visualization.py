import graphviz

from tree_sprawler.cfg.types import NodeType
from tree_sprawler.cfg.visitor import CFG


def visualize_cfg(cfg: CFG, output_file: str = "cfg"):
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

        label = f"{node_id}: {node.source_text[:50]}{'\ndefinitions: ' + ', '.join(node.variable_definitions) if node.variable_definitions else ''}"
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
