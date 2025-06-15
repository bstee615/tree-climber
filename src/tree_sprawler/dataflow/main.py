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
    print("IN Facts:", result.in_facts)
    print("OUT Facts:", result.out_facts)
