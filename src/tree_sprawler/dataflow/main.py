from tree_sprawler.dataflow.analyses.def_use import DefUseSolver, UseDefSolver
from tree_sprawler.dataflow.analyses.reaching_definitions import (
    ReachingDefinitionsProblem,
)
from tree_sprawler.dataflow.solver import RoundRobinSolver

if __name__ == "__main__":
    # Example usage of the dataflow framework
    from tree_sprawler.cfg.builder import CFGBuilder
    from tree_sprawler.cfg.visualization import visualize_cfg

    # Example C code snippet for testing
    c_code = """
    int example_function(int n) {
        int result = 0;
        
        // Test if-else statement
        if (n > 0) {
            result = result * 2;
        } else if (n < 0) {
            result = -result;
            print(result);
        }

        if (n == 0) {
            print(result);
        }
    }
    """
    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(c_code)

    # Visualize the CFG
    visualize_cfg(cfg)

    # Analyze reaching definitions
    problem = ReachingDefinitionsProblem()

    solver = RoundRobinSolver()
    result = solver.solve(cfg, problem)
    print("Reaching definitions:")
    print("In facts:")
    for node_id, facts in result.in_facts.items():
        print(f"Node {node_id}:")
        for fact in facts:
            print(f"\t* {fact}")
    for node_id, facts in result.out_facts.items():
        print(f"Node {node_id}:")
        for fact in facts:
            print(f"\t* {fact}")

    # Analyze use-def chains
    use_def_analyzer = UseDefSolver()
    use_def_result = use_def_analyzer.solve(cfg, result)
    print("Use-Def Chains:")
    for var, chains in use_def_result.chains.items():
        print(f"Variable: {var}")
        for chain in chains:
            print(f"\t* Use: {chain.use}: Definitions {chain.definitions}")

    # Analyze def-use chains
    def_use_analyzer = DefUseSolver()
    def_use_result = def_use_analyzer.solve(cfg, result)
    print("Def-Use Chains:")
    for var, chains in def_use_result.chains.items():
        print(f"Variable: {var}")
        for chain in chains:
            print(f"\t* Definition: {chain.definition}: Uses {chain.uses}")
