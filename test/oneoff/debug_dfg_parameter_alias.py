"""
Debug DFG parameter alias behavior - Created 2025-08-15

This script examines how function parameters are currently handled in DFG analysis
to understand what needs to be fixed for the parsing bug:
"Both languages DFG, Function parameters should alias def uses"
"""

import os
import tempfile

from tree_sitter_languages import get_parser

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.dataflow.analyses.def_use import DefUseSolver, UseDefSolver
from tree_climber.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_climber.dataflow.solver import RoundRobinSolver

# Simple Java test with function parameters
java_code = """
public class Test {
    public static int add(int x, int y) {
        int result = x + y;  // x and y should be uses that alias to parameter definitions
        return result;
    }
}
"""

# Simple C test with function parameters
c_code = """
int add(int x, int y) {
    int result = x + y;  // x and y should be uses that alias to parameter definitions
    return result;
}
"""

# More complex test with parameter modification
complex_java_code = """
public class Test {
    public static int complex(int x, int y) {
        x = x + 1;  // x is both used and defined here
        y = y * 2;  // y is both used and defined here
        int result = x + y;
        return result;
    }
}
"""

# More complex test with parameter modification
complex_c_code = """
int complex(int x, int y) {
    x = x + 1;  // x is both used and defined here  
    y = y * 2;  // y is both used and defined here
    int result = x + y;
    return result;
}
"""


def analyze_dfg(language, code):
    print(f"\n=== {language.upper()} DFG Analysis ===")

    # Build CFG
    builder = CFGBuilder(language)
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    print(f"Function: {cfg.function_name}")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Print CFG nodes and their metadata
    print("\nCFG Nodes:")
    for node_id, node in sorted(cfg.nodes.items()):
        print(f"  {node_id}: {node.node_type} - '{node.source_text.strip()}'")
        if node.metadata.variable_definitions:
            print(f"    Defines: {node.metadata.variable_definitions}")
        if node.metadata.variable_uses:
            print(f"    Uses: {node.metadata.variable_uses}")

    # Build dataflow result
    problem = ReachingDefinitionsProblem()
    solver = RoundRobinSolver()
    dataflow_result = solver.solve(cfg, problem)

    # Analyze def-use chains
    def_use_solver = DefUseSolver()
    def_use_result = def_use_solver.solve(cfg, dataflow_result)

    print("\nDef-Use Chains:")
    for var_name, chains in def_use_result.chains.items():
        print(f"  Variable '{var_name}':")
        for chain in chains:
            def_node = cfg.nodes[chain.definition]
            print(
                f"    Definition at node {chain.definition}: '{def_node.source_text.strip()}'"
            )
            for use_id in chain.uses:
                use_node = cfg.nodes[use_id]
                print(
                    f"      -> Used at node {use_id}: '{use_node.source_text.strip()}'"
                )

    # Analyze use-def chains
    use_def_solver = UseDefSolver()
    use_def_result = use_def_solver.solve(cfg, dataflow_result)

    print("\nUse-Def Chains:")
    for var_name, chains in use_def_result.chains.items():
        print(f"  Variable '{var_name}':")
        for chain in chains:
            use_node = cfg.nodes[chain.use]
            print(f"    Use at node {chain.use}: '{use_node.source_text.strip()}'")
            for def_id in chain.definitions:
                if def_id in cfg.nodes:
                    def_node = cfg.nodes[def_id]
                    print(
                        f"      <- Defined at node {def_id}: '{def_node.source_text.strip()}'"
                    )
                else:
                    print(f"      <- Defined at node {def_id}: (node not found)")


if __name__ == "__main__":
    print("=== SIMPLE PARAMETER TESTS ===")
    analyze_dfg("java", java_code)
    analyze_dfg("c", c_code)

    print("\n=== COMPLEX PARAMETER TESTS ===")
    analyze_dfg("java", complex_java_code)
    analyze_dfg("c", complex_c_code)
