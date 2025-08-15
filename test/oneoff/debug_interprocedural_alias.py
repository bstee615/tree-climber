"""
Debug inter-procedural parameter alias behavior - Created 2025-08-15

This script examines the current behavior for inter-procedural dataflow analysis
where function arguments should alias to parameters within the called function.
"""

from tree_climber.cfg.builder import CFGBuilder
from tree_climber.dataflow.analyses.def_use import DefUseSolver, UseDefSolver
from tree_climber.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_climber.dataflow.solver import RoundRobinSolver

# Test case showing the issue
java_code = """
public class Test {
    public static void helper(int a) {
        int b = a + 1;  // 'a' should alias to argument 'x' from call site
    }
    
    public static void main(String[] args) {
        int x = 5;
        helper(x);  // 'x' should alias to parameter 'a' in helper
    }
}
"""

c_code = """
void helper(int a) {
    int b = a + 1;  // 'a' should alias to argument 'x' from call site
}

int main() {
    int x = 5;
    helper(x);  // 'x' should alias to parameter 'a' in helper
    return 0;
}
"""


def analyze_interprocedural_dfg(language, code):
    print(f"\n=== {language.upper()} Inter-procedural DFG Analysis ===")

    # Build CFG (this creates separate CFGs for each function)
    builder = CFGBuilder(language)
    builder.setup_parser()
    cfg = builder.build_cfg(code)

    print(f"Function: {cfg.function_name}")
    print(f"Total nodes: {len(cfg.nodes)}")

    # Print CFG nodes and their metadata with edges
    print("\nCFG Nodes and Edges:")
    for node_id, node in sorted(cfg.nodes.items()):
        print(f"  {node_id}: {node.node_type} - '{node.source_text.strip()}'")
        if node.metadata.variable_definitions:
            print(f"    Defines: {node.metadata.variable_definitions}")
        if node.metadata.variable_uses:
            print(f"    Uses: {node.metadata.variable_uses}")
        if node.metadata.function_calls:
            print(f"    Calls: {node.metadata.function_calls}")
        if node.successors:
            successor_info = []
            for succ_id in node.successors:
                label = node.get_edge_label(succ_id)
                label_str = f" [{label}]" if label else ""
                successor_info.append(f"{succ_id}{label_str}")
            print(f"    -> {', '.join(successor_info)}")
        if node.predecessors:
            print(f"    <- {list(node.predecessors)}")

    # Build dataflow result with CFG for inter-procedural analysis
    problem = ReachingDefinitionsProblem()
    solver = RoundRobinSolver()
    dataflow_result = solver.solve(cfg, problem)

    # Debug: Check dataflow facts for parameter aliases
    print("\nDataflow Facts (IN):")
    for node_id, facts in dataflow_result.in_facts.items():
        if facts:
            node = cfg.nodes[node_id]
            print(f"  Node {node_id} ({node.node_type}): '{node.source_text.strip()}'")
            for fact in facts:
                print(f"    {fact}")

    print("\nDataflow Facts (OUT):")
    for node_id, facts in dataflow_result.out_facts.items():
        if facts:
            node = cfg.nodes[node_id]
            print(f"  Node {node_id} ({node.node_type}): '{node.source_text.strip()}'")
            for fact in facts:
                print(f"    {fact}")

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


if __name__ == "__main__":
    print("=== INTER-PROCEDURAL ALIAS TEST ===")
    analyze_interprocedural_dfg("java", java_code)
    analyze_interprocedural_dfg("c", c_code)
