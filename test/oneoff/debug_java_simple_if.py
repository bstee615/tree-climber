#!/usr/bin/env python3
"""
Debug script for Java simple if CFG structure.
Created: 2025-08-14

Context: The test_simple_if test is failing because it expects a node with 
'EXIT' in the source text, but the actual EXIT nodes might have different text.

Investigation: Examine the actual CFG structure for the simpleIf method to 
understand how to properly test the edge connections.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from test.java_cfg_samples.test_java_cfg import JavaCFGTestHelper


def debug_simple_if():
    """Debug the simpleIf method CFG structure."""
    
    helper = JavaCFGTestHelper()
    samples_dir = os.path.join(os.path.dirname(__file__), "..", "java_cfg_samples", "basic_constructs.java")
    
    print(f"Loading Java file: {samples_dir}")
    
    try:
        cfg = helper.build_cfg_from_java_file(samples_dir, "simpleIf")
        helper.debug_cfg_structure(cfg, "Simple If CFG Structure")
        
        print(f"\nLooking for condition node:")
        condition_nodes = [n for n in cfg.nodes.values() if "x > 0" in n.source_text]
        if condition_nodes:
            condition_node = condition_nodes[0]
            print(f"Found condition node {condition_node.id}: '{condition_node.source_text}'")
            print(f"Successors: {list(condition_node.successors)}")
            print(f"Edge labels: {condition_node.edge_labels}")
            
            for succ_id in condition_node.successors:
                succ_node = cfg.nodes[succ_id]
                edge_label = condition_node.get_edge_label(succ_id)
                print(f"  -> {succ_id} ({succ_node.node_type.name}): '{succ_node.source_text}' [label: '{edge_label}']")
        else:
            print("No condition node found!")
            
        print(f"\nEXIT nodes:")
        exit_nodes = [n for n in cfg.nodes.values() if n.node_type.name == "EXIT"]
        for exit_node in exit_nodes:
            print(f"  {exit_node.id}: '{exit_node.source_text}'")
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    debug_simple_if()