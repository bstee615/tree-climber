"""Test program to visualize Java CFG"""

import os
import sys

from tree_sitter_languages import get_parser

from tree_sprawler.cfg.builder import get_visitor
from tree_sprawler.cfg.visualization import visualize_cfg

try:
    # Read the test file
    test_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "test",
        "test.java",
    )
    print(f"Reading file: {test_file}")
    with open(test_file, "r") as f:
        source_code = f.read()
        print(f"Successfully read {len(source_code)} bytes")

    # Parse the file using the Java parser
    print("Creating Java parser...")
    parser = get_parser("java")
    print("Parsing source code...")
    tree = parser.parse(bytes(source_code, "utf8"))
    print("Successfully parsed source code")

    # Create CFG visitor and visit the tree
    print("Creating CFG visitor...")
    visitor = get_visitor("java")
    print("Visiting AST...")
    result = visitor.visit(tree.root_node)
    print("Successfully visited AST")

    # Post-process the CFG to clean up nodes
    print("Post-processing CFG...")
    visitor.postprocess_cfg()
    print("Post-processing complete")

    # Print detailed CFG information
    cfg = visitor.cfg
    # print("\nCFG Analysis for Java code")
    # print("-" * 50)
    # print(f"Method name: {cfg.function_name}")
    # print(f"Total nodes: {len(cfg.nodes)}")
    # print(f"Entry nodes: {cfg.entry_node_ids}")
    # print(f"Exit nodes: {cfg.exit_node_ids}\n")

    # print("Node details:")
    # print("-" * 50)
    # for node_id, node in sorted(cfg.nodes.items()):
    #     print(f"\nNode {node_id} ({node.node_type})")
    #     print(f"  Text: {node.source_text}")
    #     print(f"  Predecessors: {sorted(node.predecessors)}")
    #     print(f"  Successors: {sorted(node.successors)}")
    #     if node.edge_labels:
    #         print(f"  Edge labels: {node.edge_labels}")
    #     if node.metadata and (
    #         node.metadata.variable_definitions or node.metadata.variable_uses
    #     ):
    #         if node.metadata.variable_definitions:
    #             print(f"  Definitions: {sorted(node.metadata.variable_definitions)}")
    #         if node.metadata.variable_uses:
    #             print(f"  Uses: {sorted(node.metadata.variable_uses)}")

    # Visualize the CFG
    output_file = "java_cfg"
    print(f"\nGenerating visualization...")
    visualize_cfg(visitor.cfg, output_file)
    print(f"CFG visualization saved to: {output_file}")

except Exception as e:
    print("\nError:", str(e))
    print("\nTraceback:")
    import traceback

    traceback.print_exc()
    sys.exit(1)
