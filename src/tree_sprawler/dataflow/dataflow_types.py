import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Set

from tree_sprawler.ast_utils import get_definitions
from tree_sprawler.cfg.cfg_types import CFGNode
from tree_sprawler.cfg.visitor import CFG


class DataflowFact:
    def __hash__(self) -> int:
        """
        Return a hash for the dataflow fact.
        This should be unique for each fact based on its content.
        """
        raise NotImplementedError("Dataflow fact must implement __hash__.")


class MeetOperation:
    def __call__(self, facts: Iterable[frozenset[DataflowFact]]) -> Set[DataflowFact]:
        """
        Combine multiple dataflow facts using a meet operation.
        This is typically a set union or intersection, depending on the problem.
        """
        raise NotImplementedError("Meet operation must be implemented.")


class TransferFunction:
    def __call__(self, node: CFGNode, in_facts: Set[DataflowFact]) -> Set[DataflowFact]:
        """
        Apply the transfer function to a node with the given input facts.
        This function should return the output facts for the node.
        """
        raise NotImplementedError("Transfer function must be implemented.")


class DataflowInitializer:
    def __call__(self, node: CFGNode) -> Set[DataflowFact]:
        """
        Initialize the dataflow facts for a node.
        This function should return the initial facts for the node.
        """
        raise NotImplementedError("Dataflow initializer must be implemented.")


@dataclass
class DataflowProblem:
    meet: MeetOperation
    transfer: TransferFunction
    in_init: DataflowInitializer
    out_init: DataflowInitializer


@dataclass
class DataflowResult:
    in_facts: dict[int, Set[DataflowFact]]
    out_facts: dict[int, Set[DataflowFact]]


# Define a simple dataflow problem (e.g., reaching definitions)
class ReachingDefinition(DataflowFact):
    def __init__(self, variable: str, node_id: int):
        self.variable = variable
        self.node_id = node_id

    def __hash__(self) -> int:
        return hash((self.variable, self.node_id))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, type(self))
            and self.variable == other.variable
            and self.node_id == other.node_id
        )

    def __repr__(self) -> str:
        return f"ReachingDefinition(variable={self.variable}, node_id={self.node_id})"


class Union(MeetOperation):
    def __call__(self, facts: Iterable[frozenset[DataflowFact]]) -> Set[DataflowFact]:
        return set().union(*[set(fact_set) for fact_set in facts])


class ReachingDefinitionsGenKill(TransferFunction):
    def __call__(self, node: CFGNode, in_facts: Set[DataflowFact]) -> Set[DataflowFact]:
        node_id = node.id
        defined_variables = get_definitions(node.ast_node) if node.ast_node else []
        gen_facts = {
            ReachingDefinition(variable=var, node_id=node_id)
            for var in defined_variables
        }
        kill_facts = {
            fact
            for fact in in_facts
            if isinstance(fact, ReachingDefinition)
            and fact.variable in defined_variables
        }

        out_facts = (in_facts - kill_facts) | gen_facts
        # print(
        #     f"Node {node_id}: DEFS = {defined_variables}, GEN = {gen_facts}, KILL = {kill_facts}, OUT = {out_facts}"
        # )
        return out_facts


class Empty(DataflowInitializer):
    def __call__(self, _node: CFGNode) -> Set[DataflowFact]:
        # Initialize with an empty set of facts
        return set()


def solve_dataflow(cfg: CFG, problem: DataflowProblem) -> DataflowResult:
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
        for node_id, node in cfg.nodes.items():
            old_out_facts = copy.deepcopy(out_facts[node_id])
            in_facts[node_id] = problem.meet(
                [frozenset(out_facts[pred]) for pred in node.predecessors]
            )
            out_facts[node_id] = problem.transfer(node, in_facts[node_id])
            if out_facts[node_id] != old_out_facts:
                changed = True
        changed = False  # Reset changed for the next iteration

    return DataflowResult(in_facts=in_facts, out_facts=out_facts)


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

    result = solve_dataflow(cfg, problem)
    print("IN Facts:", result.in_facts)
    print("OUT Facts:", result.out_facts)
