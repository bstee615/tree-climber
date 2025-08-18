import copy

from tree_climber.cfg.visitor import CFG
from tree_climber.dataflow.dataflow_types import DataflowProblem, DataflowResult


class RoundRobinSolver:
    def solve(self, cfg: CFG, problem: DataflowProblem) -> DataflowResult:
        """
        Solve a dataflow problem on a given Control Flow Graph (CFG).
        """
        # Initialize IN and OUT sets
        in_facts = {node_id: set() for node_id, _ in cfg.nodes.items()}
        out_facts = {node_id: set() for node_id, _ in cfg.nodes.items()}
        for node_id, node in cfg.nodes.items():
            in_facts[node_id] = problem.in_init(node)
            out_facts[node_id] = problem.out_init(node)

        # Iterate until convergence
        changed = True
        while changed:
            changed = False  # Reset changed for the next iteration
            for node_id, node in cfg.nodes.items():
                old_out_facts = copy.deepcopy(out_facts[node_id])
                in_facts[node_id] = problem.meet(
                    [frozenset(out_facts[pred]) for pred in node.predecessors]
                )
                out_facts[node_id] = problem.transfer(node, in_facts[node_id])
                if out_facts[node_id] != old_out_facts:
                    changed = True

        return DataflowResult(in_facts=in_facts, out_facts=out_facts)
