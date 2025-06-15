from tree_sprawler.dataflow.dataflow_types import DataflowProblem
from tree_sprawler.dataflow.problems.reaching_definitions import (
    Empty,
    ReachingDefinitionsGenKill,
    Union,
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
            result = n * 2;
        } else if (n < 0) {
            result = -n;
        }
        print(result);
    }
    """
    builder = CFGBuilder("c")
    builder.setup_parser()
    cfg = builder.build_cfg(c_code)

    # Visualize the CFG
    visualize_cfg(cfg)

    problem = DataflowProblem(
        meet=Union(),
        transfer=ReachingDefinitionsGenKill(),
        in_init=Empty(),
        out_init=Empty(),
    )

    solver = RoundRobinSolver()
    result = solver.solve_dataflow(cfg, problem)
    print("IN Facts:", result.in_facts)
    print("OUT Facts:", result.out_facts)
